## Script to compute mean diurnal cycle of SKT from IFS
## E. Dutra June 2022 

import xarray as xr
import numpy as np
import gribscan
import os 
from netCDF4 import Dataset,num2date 
import pandas as pd
import datetime as dt 
import time
import sys

import matplotlib.pylab as plt
import matplotlib.cm as cm
import cmocean.cm as cmo
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

def gen_output(fout):
   # create output file 
  if os.path.isfile(fout):
    os.remove(fout)
  nc = Dataset(fout,'w',format='NETCDF4')

  # create dimensions 
  nc.createDimension('lat',len(lat_reg))
  nc.createDimension('lon',len(lon_reg))
  nc.createDimension('time',24)
  
   
  # create dimensions variables 
  cvar = nc.createVariable('lat','f4',['lat',])
  cvar.units = "degrees_north"
  cvar.long_name = "latitude"
  cvar.standard_name = "latitude"
  cvar.axis= "Y" 
  cvar[:] = lat_reg[:,0]
  
  cvar = nc.createVariable('lon','f4',['lon',])
  cvar.units = "degrees_east"
  cvar.long_name = "longitude"
  cvar.standard_name = "longitude"
  cvar.axis= "X" 
  cvar[:] = lon_reg[0,:]
  
  cvar = nc.createVariable('time','i4',['time',])
  cvar.units = f"hours since {YM.strftime('%Y-%m-%d')}T00:00:00"
  cvar.long_name = "time"
  cvar.standard_name = "time"
  cvar.axis= "T"
  cvar.calendar = "standard"
   
  
  cvar = nc.createVariable('LST','f4',('time','lat','lon'),
                           fill_value=ZFILL,zlib=True,complevel=6,
                           least_significant_digit=2)
  cvar.long_name='LST'
  cvar.units='Celsius'
    
  cvar = nc.createVariable('FVALID','f4',('time','lat','lon'),
                           fill_value=ZFILL,zlib=True,complevel=6,
                           least_significant_digit=3)
  cvar.long_name='fraction of valid pixels in average'
  cvar.units='0-1'
    
  cvar = nc.createVariable('NSLOT','f4',('time',))
  cvar.long_name='total number of slots processed'
  cvar.units='-'
    
  return nc

def inter2D(xIN):
  nn_interpolation = NearestNDInterpolator(points_ifs, xIN)
  return nn_interpolation(lon_reg, lat_reg)

#resol='tco2559-ng5'  # or tco3999-ng5
#resol='tco3999-ng5'  # or tco3999-ng5
#resol='tco1279-orca025' # 
#ddate="202005"


t0 = time.time()
resol=sys.argv[1]
ddate=sys.argv[2]

DFOUT="/scratch/b/b381666/SKT_DIAG/"
ZFILL=-999
tcc_min = 0.3

YM = dt.datetime.strptime(ddate,"%Y%m")

## Define output regular grid 
lon_reg, lat_reg = np.meshgrid(np.arange(-80,80.05,0.05), np.arange(80,-80.05,-0.05))

## define output file 
fout = f"{DFOUT}/NETCDF4_{resol}_LST_{ddate}.nc"
ncOUT = gen_output(fout)
ncOUT.close()
print(f"Saving to:{fout}")


## Load surface data with open_zarr() 
# json file was already prepared with gribscan-index and gribscan-build command line tools
t0_ = time.time()
if resol == 'tco1279-orca025':
  datazarr = "/work/bm1235/a270046/cycle2-sync/tco1279-orca025/nemo_deep/ICMGGc2/json.dir/atm2d_v0.json" 
elif resol ==   'tco3999-ng5':
  datazarr='/work/bm1235/a270046/cycle2-sync/tco3999-ng5/ICMGGc2/json.dir/atm2d.json' 
elif resol == 'tco2559-ng5':
  datazarr = '/work/bm1235/a270046/cycle2-sync/tco2559-ng5/ICMGGall_update/json.dir/atm2d.json'
print("Loading: ",datazarr)
data = xr.open_zarr("reference::"+datazarr, consolidated=False)
print(f"loaded data list {datazarr} in {time.time()-t0_:.1f} sec") 


## Get the grid 
model_lon = np.where(data.lon.values>180, data.lon.values-360, data.lon.values)
model_lat = data.lat.values

## Select region of interest 
reg = ( (model_lat>-81) & (model_lat<81) &
         (model_lon >-81) & (model_lon<81) )
npp = np.sum(reg)
points_ifs = np.vstack((model_lon[reg], model_lat[reg])).T

## Main work 
ndays = (YM.replace(month = YM.month % 12 +1, day = 1)-dt.timedelta(days=1)).day
## Main loop on hours for diurnal cycle 
for ih in range(24):
  t0H = time.time()
  nslotSTP = 0
  zAVG = np.zeros(npp,'f4')
  zVAL = np.zeros(npp,'i4')
  # loop on days of month 
  for iday in range(ndays):
    slot = YM+dt.timedelta(days=iday)+dt.timedelta(hours=ih)
    nslotSTP = nslotSTP + 1
    print("loading",slot)
    # load data into memory 
    skt = data.skt.sel(time=slot)[reg] - 273.16
    tcc = data.tcc.sel(time=slot)[reg]
    
    # select only clear sky 
    xOK = tcc <= tcc_min
    zVAL[xOK] = zVAL[xOK] + 1 
    zAVG[xOK] = zAVG[xOK] + skt[xOK]
    
  #compute averages 
  zAVG = np.where(zVAL>0,zAVG / zVAL,ZFILL)
  zVAL = np.where(zVAL>0,zVAL/nslotSTP,0)
  
  # write to output 
  ncOUT =  Dataset(fout,'a',format='NETCDF4')
  ncOUT.variables['time'][ih] = ih
  ncOUT.variables['NSLOT'][ih] = nslotSTP
    
  ncOUT.variables['LST'][ih,:,:] = inter2D(zAVG)
  ncOUT.variables['FVALID'][ih,:,:] = inter2D(zVAL)
  
  print(f"Processed {ddate} hour {ih} with {nslotSTP} slots in {time.time()-t0H:.1f} sec") 
 
  ncOUT.close()
print(f"finished in {time.time()-t0:.1f} sec") 
