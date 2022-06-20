from itertools import islice

import numpy as np
import xarray as xr
import pandas as pd

VARDEFS = {
    "atmflx": {
        "T  FSWR": ("SW", {"units": "W/m2"}),
        "T  FLWR": ("LW", {"units": "W/m2"}),
        "T  FVDF": ("T_vrt.dff", {"units": "W/m2"}),
        "Q  FVDF": ("Q_vrt.diff", {"units": "mm/D"}),
        "Q  FCVR": ("Cnv_rain", {"units": "mm/D"}),
        "Q  FCVN": ("Cnv_snow", {"units": "mm/D"}),
        "Q  FLSR": ("LS_rain", {"units": "mm/D"}),
        "Q  FLSN": ("LS_snow", {"units": "mm/D"}),
        "U  FVDF": ("Uflxvrt.dff", {"units": "Pa"}),
        "V  FVDF": ("Vflxvrt.dff", {"units": "Pa"}),
    },
    "atmvar": {
        "P  HIST": ("pressure", {"units": "hPa"}),
        "U  HIST": ("x-wind", {"units": "m/s"}),
        "V  HIST": ("y-wind", {"units": "m/s"}),
        "T  HIST": ("temp", {"units": "degC"}),
        "Q  HIST": ("sp.humidity", {"units": "g/kg"}),
        "L  HIST": ("c.liq", {"units": "g/kg"}),
        "I  HIST": ("c.ice", {"units": "g/kg"}),
        "A  HIST": ("c.frac", {"units": "%"}),
        "N  HIST": ("rain", {"units": "g/kg"}),
        "O  HIST": ("snow", {"units": "g/kg"}),
        "R  HIST": ("RH", {"units": "%"}),
        "W  HIST": ("vert.vel", {"units": "Pa/s"}),
    },
    "sfcflx": {
        "SFSSLHF": ("sfsslhf", {"units": "W/m2"}),
        "SFSFDIR": ("sfsfdir", {"units": "W/m2"}),
        "SFSSSHF": ("sfsshf", {"units": "W/m2"}),
        "SFSSW": ("sfssw", {"units": "W/m2"}),
        "SFSLW": ("sfslw", {"units": "W/m2"}),
        "SFSSWC": ("clrskySW", {"units": "W/m2"}),
        "SFSLWC": ("clrskyLW", {"units": "W/m2"}),
        "SFSLSR": ("LSrainfall", {"units": "kg/m2"}),
        "SFSCR": ("Conv.rainfall", {"units": "kg/m2"}),
        "SFSLSF": ("LSsnowfall", {"units": "kg/m2"}),
        "SFSCF": ("Conv.snowfall", {"units": "kg/m2"}),
        "SFSTCC": ("tot.cldcvr", {}),
        "SFSLSPF": ("LS prec.frac", {"units": "1"}),
        "SFSSWDO": ("Dwnwrd SW", {"units": "W/m2"}),
        "SFSLWDO": ("Dwnwrd LW", {"units": "W/m2"}),
        "SFSZ": ("orogr", {"units": "m2/s2"}),
        "SFSLF": ("Land frac", {}),
        "S  HIST": ("s hist", {}),
    },
    "sfcpres": {
        "S  HIST": ("SP", {"units": "Pa"}),
    },
    "sfcvar": {
        "SFST2M": ("2mtemp", {"units": "C"}),
        "SFSQ2M": ("2mspechum", {"units": "g/kg"}),
        "SFS10U": ("10U", {"units": "m/s"}),
        "SFS10V": ("10V", {"units": "m/s"}),
        "SFSZ0M": ("Sfc.rough", {"units": "m"}),
        "SFSZ0H": ("sfc.rough.heat", {"units": "m"}),
        "SFSAL": ("albedo", {"units": "%"}),
        "SFSBLH": ("BLH", {"units": "m"}),
        "SFSTSK": ("Tskin", {"units": "degC"}),
    },
}
STAT_NR = {
            1 : 'BARBADOS CLOUD OBSERVATORY' ,
            2 : 'EUREC4A_1'     ,
            3 : 'EUREC4A_2'     ,
            4 : 'EUREC4A_3'     ,
            5 : 'EUREC4A_4'     ,
            6 : 'EUREC4A_5'     ,
            7 : 'EUREC4A_6'     ,
            8 : 'EUREC4A_7'     ,
            9 : 'EUREC4A_8'     ,
           10 : 'EUREC4A_9'     ,
           11 : 'EUREC4A_10'    ,
           12 : 'CABAUW_NL'     ,
           13 : 'SODANKYLA_FIN' ,
           14 : 'ARMS_OKL'      ,
           15 : 'LINDENBERG_GER',
           16 : 'BARROW_USA'    ,
           17 : 'SUMMIT_DNK'    ,
           18 : 'DOMEC_ANTARC'  ,
           19 : 'PAYERNE_SWZ'   ,
           20 : 'ATTO_BRZ'      ,
           21 : 'MNSGERAIS_BRZ' ,
           22 : 'BAHIA_BRZ'     ,
           23 : 'SAN_LUIS_MXC'  ,
           24 : 'ZACATECAS_MXC' ,
           25 : 'SCOTLAND'      ,
           26 : 'BURGOS_SPN'    ,
           27 : 'HUELVA_SPN'    ,
           28 : 'PSTERN_SPRING' ,
           29 : 'PSTERN_AUTUMN' ,
           30 : 'PSTERN_MARCH'  ,
}

HEADER_TYPES = {"exp": str, "vp": int, "i": int, "ty": int, "west": float, "north": float}

def round_to_the_minute(times):
    ref = np.datetime64("2020-01-01")
    return ref + np.round((times - ref) / np.timedelta64(1, "m")) * np.timedelta64(1, "m")

def load_ddh(filename, kind):
    with open(filename) as ifh:
        header = dict(zip(*map(str.split, islice(ifh, 2))))
    header = {k:f(header[k]) for k, f in HEADER_TYPES.items() if k in header}
    
    df = pd.read_fwf(filename, header=0, skiprows=2, parse_dates=["vdat"])
    ds = (df.to_xarray()
          .assign(time = lambda ds: ds.vdat + ds.vtim * np.timedelta64(60*60, "s"))
          .drop_vars(["#   idat", "itim", "vdat", "vtim", "index"]))
    
    times, tidx = np.unique(ds.time, return_inverse=True)
    levels, lidx = np.unique(ds.lev, return_inverse=True)

    def reshape_var(var):
        out = np.full((len(times), len(levels)), np.nan, dtype=var.dtype)
        out[tidx, lidx] = var
        return xr.DataArray(out, dims=("time", "level"))
    
    ds = xr.Dataset({
        newname: reshape_var(ds[oldname].values).assign_attrs(attrs)
        for oldname, (newname, attrs) in VARDEFS[kind].items()
    }, coords={
        "time": (("time",), round_to_the_minute(times)),
        "level": (("level",), levels),
        "station": ((), header["i"]),
        "lat": ((), header["north"], {"units": "degrees_north"}),
        "lon": ((), 360 - header["west"], {"units": "degrees_east"}),
    }, attrs={k: header[k] for k in ["exp", "vp", "ty"]})
    
    if len(ds.level) == 1:
        ds = ds.squeeze().drop("level")
    
    ds.attrs['Station name']= STAT_NR[int(header["i"])]
    return ds
