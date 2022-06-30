## Script to compute mean diurnal cycle of SKT from ICON
## E. Dutra June 2022 


import xarray as xr
import numpy as np
import os 
from netCDF4 import Dataset,num2date 
import pandas as pd
import datetime as dt 
import time
import sys
import intake
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
import datetime as dt 

def load_var(exp,cvar=None,realm='atm',frequency='30minute',load_LALO=False):
  ## Load catalog 
  t0=time.time()
  if exp == 'ngc2009':
    catalog_file = "/home/k/k203123/NextGEMS_Cycle2.git/experiments/ngc2009/scripts/ngc2009.json"
    grid_path = "/pool/data/ICON/grids/public/mpim/0015/icon_grid_0015_R02B09_G.nc"
  elif exp == 'ngc2012':
    catalog_file = "/home/k/k203123/NextGEMS_Cycle2.git/experiments/ngc2012/scripts/ngc2012.json"
    grid_path = "/pool/data/ICON/grids/public/mpim/0033/icon_grid_0033_R02B08_G.nc"
    frequency='3hour'
  
  if load_LALO:
    grid = xr.open_dataset(grid_path)
    model_lon = grid.clon.values*180./np.pi
    model_lat = grid.clat.values*180./np.pi
    return model_lat,model_lon
    
  cat = intake.open_esm_datastore(catalog_file)
  final_query = cat.search(realm=realm, frequency=frequency, variable_id=cvar)
  dataset_dict = final_query.to_dataset_dict(
      cdf_kwargs={
          "chunks": dict(
              time=1,
          )
      }
  )
  keys = list(dataset_dict.keys())
  print(keys)
  data = dataset_dict[keys[0]]
  print(f"Loaded {exp} {cvar} in {time.time()-t0:.1f} sec") 
 
  return data

def inter2D(xIN):
  nn_interpolation = NearestNDInterpolator(points_ifs, xIN)
  return nn_interpolation(lon_reg, lat_reg)

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
  cvar[:] = np.arange(24)
   
  
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

t0 = time.time()
resol=sys.argv[1] # 'ngc2009'
ddate=sys.argv[2]

#resol='ngc2009'
#ddate="202006"

DFOUT="/scratch/b/b381666/SKT_DIAG/"
ZFILL=-999
tcw_min = 0.005

freq=1
if resol == 'ngc2012':
  freq=3

YM = dt.datetime.strptime(ddate,"%Y%m")

## Define output regular grid 
lon_reg, lat_reg = np.meshgrid(np.arange(-80,80.05,0.05), np.arange(80,-80.05,-0.05))

## define output file 
fout = f"{DFOUT}/NETCDF4_{resol}_LST_{ddate}.nc"
ncOUT = gen_output(fout)
ncOUT.close()
print(f"Saving to:{fout}")

## Define output regular grid 
lon_reg, lat_reg = np.meshgrid(np.arange(-80,80.05,0.05), np.arange(80,-80.05,-0.05))


## Load icon data 
t0_ = time.time()
D_ts = load_var(resol,'ts')
D_cllvi = load_var(resol,'cllvi')
D_clivi = load_var(resol,'clivi')
print(f"loaded data in {time.time()-t0_:.1f} sec") 


## load lat/lon 
model_lat, model_lon = load_var(resol,load_LALO=True)

## Select region of interest 
reg = ( (model_lat>-81) & (model_lat<81) &
         (model_lon >-81) & (model_lon<81) )
npp = np.sum(reg)
points_ifs = np.vstack((model_lon[reg], model_lat[reg])).T

## Main work 
ndays = (YM.replace(month = YM.month % 12 +1, day = 1)-dt.timedelta(days=1)).day
## Main loop on hours for diurnal cycle 
#ndays=3
for ih in range(0,24,freq):
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
    skt = D_ts['ts'].sel(time=slot)[reg]  - 273.16
    tcw = D_cllvi['cllvi'].sel(time=slot)[reg]  +  D_clivi['clivi'].sel(time=slot)[reg]
    
    # select only clear sky 
    xOK = tcw <= tcw_min
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
