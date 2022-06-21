from itertools import islice

import numpy as np
import xarray as xr
import pandas as pd

VARDEFS = {
    "atmflx": {
        "T  FSWR": ("sw", {"units": "W/m2","long_name": "T flux: SW rad"}),
        "T  FLWR": ("lw", {"units": "W/m2","long_name": "T flux: LW rad"}),
        "T  FVDF": ("tfvdf", {"units": "W/m2","long_name": "T flux: Vert diffusion"}),
        "Q  FVDF": ("qfvdf", {"units": "mm/D","long_name": "Q flux: Vert diffusion"}),
        "Q  FCVR": ("qfcvr", {"units": "mm/D","long_name": "Q flux: Convective rain"}),
        "Q  FCVN": ("qfcvn", {"units": "mm/D","long_name": "Q flux: Convective snow"}),
        "Q  FLSR": ("qflsr", {"units": "mm/D","long_name": "Q flux: Large scale rain"}),
        "Q  FLSN": ("qflsn", {"units": "mm/D","long_name": "Q flux: Large scale snow"}),
        "U  FVDF": ("ufvdf", {"units": "Pa","long_name": "U flux: Vert diffusion"}),
        "V  FVDF": ("vfvdf", {"units": "Pa","long_name": "V flux: Vert diffusion"}),
    },
     "atmvar": {
        "P  HIST": ("p", {"units": "Pa","long_name": "Pressure"}),
        "U  HIST": ("u", {"units": "m/s","long_name": "Eastward component of the wind"}),
        "V  HIST": ("v", {"units": "m/s","long_name": "Northward component of the wind"}),
        "T  HIST": ("t", {"units": "K","long_name": "Temperature"}),
        "Q  HIST": ("q", {"units": "kg/kg","long_name": "Specific Humidity"}),
        "L  HIST": ("clwc", {"units": "kg/kg","long_name": "Specific cloud liquid water content"}),
        "I  HIST": ("ciwc", {"units": "kg/kg","long_name": "Specific cloud ice water content"}),
        "A  HIST": ("cc", {"units": "%","long_name": "Fraction of cloud cover"}),
        "N  HIST": ("crwc", {"units": "kg/kg","long_name": "Specific rain water content"}),
        "O  HIST": ("cswc", {"units": "kg/kg","long_name": "Specific snow water content"}),
        "R  HIST": ("rh", {"units": "%","long_name": "Relative humidity"}),
        "W  HIST": ("w", {"units": "Pa/s","long_name": "Vertical velocity"}),
    },

    "sfcflx": {
        "SFSSLHF": ("slhf", {"units": "W/m2","long_name": "Surface latent heat flux"}),
        "SFSFDIR": ("fdir", {"units": "W/m2","long_name": "Total sky direct radiation at surface"}),
        "SFSSSHF": ("sshf", {"units": "W/m2","long_name": "Surface sensible heat flux"}),
        "SFSSW": ("sfcsw", {"units": "W/m2","long_name": "Surface solar radiation"}),
        "SFSLW": ("sfclw", {"units": "W/m2","long_name": "Surface thermal radiation"}),
        "SFSSWC": ("sfcswc", {"units": "W/m2","long_name": "Surface clear-sky solar radiation"}),
        "SFSLWC": ("sfclwc", {"units": "W/m2","long_name": "Surface clear-sky thermal radiation"}),
        "SFSLSR": ("lsr", {"units": "kg/m2","long_name": "Large scale rainfall"}),
        "SFSCR": ("cr", {"units": "kg/m2","long_name": "Convective rainfall"}),
        "SFSLSF": ("lsf", {"units": "kg/m2","long_name": "Large scale snowfall"}),
        "SFSCF": ("cs", {"units": "kg/m2","long_name": "Convective snowfall"}),
        "SFSTCC": ("ttc", {"units": "1","long_name": "Total cloud cover"}),
        "SFSLSPF": ("LS prec.frac", {"units": "1","long_name": "Large-scale precip. fraction"}),
        "SFSSWDO": ("sfcswd", {"units": "W/m2","long_name": "Surface downwards solar radiation"}),
        "SFSLWDO": ("sfclwd", {"units": "W/m2","long_name": "Surface downwards thermal radiation"}),
        "SFSZ": ("z", {"units": "m2/s2","long_name": "Orography"}),
        "SFSLF": ("Land frac", {"units": "1","long_name": "Land Fraction"}),
        "S  HIST": ("sfcp", {"units": "Pa","long_name": "Surface Pressure"}),
    },
    "sfcpres": {
        "S  HIST": ("SP", {"units": "Pa","long_name": "Surface Pressure"}),
    },
    "sfcvar": {
        "SFST2M": ("2t", {"units": "K","long_name": "2m temperature"}),
        "SFSQ2M": ("2q", {"units": "kg/kg","long_name": "2m specific humidity"}),
        "SFS10U": ("10u", {"units": "m/s","long_name": "10m eastward component of the wind"}),
        "SFS10V": ("10v", {"units": "m/s","long_name": "10m northward component of the wind"}),
        "SFSZ0M": ("zo", {"units": "m","long_name": "Surface roughness"}),
        "SFSZ0H": ("zoh", {"units": "m","long_name": "Surface roughness for heat"}),
        "SFSAL": ("al", {"units": "%","long_name": "Surface albedo"}),
        "SFSBLH": ("blh", {"units": "m","long_name": "Boundary layer height"}),
        "SFSTSK": ("tsk", {"units": "K","long_name": "Skin temperature"}),
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
