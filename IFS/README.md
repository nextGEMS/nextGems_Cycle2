# IFS simulations

Link to complete description of simulations - TO BE PROVIDED (easy GEMS?)

## Raw data on levante

`/work/bm1235/a270046/cycle2-sync/`
- **2.5km** experiment (8m :)): `tco3999-ng5` (IFS 2.5km, FESOM ~5km)
- **4km** experiment: `tco2559-ng5` (IFS 4km, FESOM ~5km)
- **9km** baseline: `tco1279-orca025` (IFS 9km, NEMO 0.25deg)

## Appetizers (interpolated to regular grid, plus movies and images)
Several variables interpolated on regular global 5400x2700 grid and 2000x2000 polar grids. Don't use it for balance computations, those are neares neighbor interpolated data.

**Movies:** https://nextcloud.awi.de/s/PY9FYznLXo4J7mY 

Names of the movies are : `[resolution]_[projection]_[variable].mp4`

*Path on levante:* `/work/ab0995/a270088/NextGems_public/appetizer`

- `IFS2.5` = `tco3999-ng5` (see above in raw data)
- `IFS4.5` = `tco2559-ng5` (see above in raw data)

Each of the variables have `images` and `netcdf` folders. Recomended way to open and process `netCDF` from those folders see in the [plot_appetizer_data_IFS.ipynb](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/plot_appetizer_data_IFS.ipynb) notebook.

[More about appetizer script](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/appetizer_howto.md), if you want to produce it for some other variables.

## Notebooks

- [STARTHERE_IFS.ipynb](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/STARTHERE_IFS.ipynb) - Basic example of how to **Get the data/Get the grid/Interpolate/Plot** IFS data (based on `tco3999-ng5`, but will work on `tco2559-ng5` as well)
- [pressurelevels_IFS.ipynb](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/pressurelevels_IFS.ipynb) - Plot data on pressure levels
- [plot_appetizer_data_IFS.ipynb](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/plot_appetizer_data_IFS.ipynb) - Plot and process interpolated netCDF files from `appetizer`.
- [create_index_for_interpolated_datakerchunk_ifs.ipynb](https://github.com/nextGEMS/nextGems_Cycle2/blob/main/IFS/create_index_for_interpolated_datakerchunk_ifs.ipynb) - How to index `appetizer` data (and any large number of netCDF data) to trick xarray to think it's zarr.
