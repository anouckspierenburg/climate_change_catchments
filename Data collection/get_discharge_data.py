#######################################################################################
# In this script discharge data of the stations will be found in the CaMa-Flood dataset
# Then they are stored in a netCDF file
# Example for the Amazon catchment, which can be altered to your catchment
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
# Imports needed
import xarray as xr
import numpy as np
import intake
import datetime

# Observational data
path_obs = '/home/b/b301048/NextGEMS_hackathon/Observations/station_attributes_with_obsdis24h_197001-202312_v4.0_20240216_withEFAS.nc'
obs = xr.open_dataset(path_obs).load()

# Open catalog and load CaMa-Flood data
cat = intake.open_catalog("https://data.nextgems-h2020.eu/catalog.yaml")
ds = cat.IFS['IFS_9-FESOM_5-production']['2D_1h_camaflood'].to_dask()
ds_h = cat.IFS['IFS_9-FESOM_5-production-hist']['2D_1h_camaflood'].to_dask() # Historical dataset for validation

# Functions needed
def find_common_elements(arr1, arr2):
    # Convert arrays to sets for faster lookup
    set1 = set(arr1)
    set2 = set(arr2)
    # Find intersection of the sets (common elements)
    common_elements = set1.intersection(set2)
    return list(common_elements)

#######################################################################################
# Find the right index
# discharge is 1800x3600 latxlon = CaMa6min
# > so obs dataset other resolution
#######################################################################################
## observations stations lat,lon values in list
## decomment the station wanted

station_name = 'Manacapuru_Amazon' # Station_Catchment
grdc_stationname = 'Manacapuru'
lat_lon = [obs.CamaLat1_6min.where(obs.stationname==grdc_stationname, drop=True)[0].values, obs.CamaLon1_6min.where(obs.stationname==grdc_stationname, drop=True)[0].values]       

lat_idx = np.abs(ds['lat'].values - lat_lon[0]).argmin()
lon_idx = np.abs(ds['lon'].values - lat_lon[1]).argmin()

nearest_lat = ds['lat'].values[lat_idx] # Have to do this step else the decimals are not exactly the same
nearest_lon = ds['lon'].values[lon_idx]

lats = np.where(ds['lat'].values == nearest_lat)
lons = np.where(ds['lon'].values == nearest_lon)

# Check between the two sets which match
idx = find_common_elements(lats[0].flatten(), lons[0].flatten())[0]

###############################################################
# After finding idx select the station with it: historical
station_ds_h = ds_h['dis'].isel(value=idx)
station_ds_loaded_h = station_ds_h.load()

# Put in a xarray
time_vals_h = ds_h.time.values
station_xr_h = xr.DataArray(station_ds_loaded_h, coords={'time': time_vals_h}, dims=['time'], name='dis')

# Save in netcdf
netcdf_filename_h = f'../../stored_datasets/discharge_{station_name}_30yr_hist.nc'
station_xr_h.to_netcdf(path=netcdf_filename_h)

#########################################################################
# After finding idx select the station with it: future
station_ds = ds['dis'].isel(value=idx)
station_ds_loaded = station_ds.load()

# Put in a xarray
time_vals = ds.time.values
station_xr = xr.DataArray(station_ds_loaded, coords={'time': time_vals}, dims=['time'], name='dis')

# Save in netcdf
netcdf_filename = f'../../stored_datasets/discharge_{station_name}_30yr_fut.nc'
station_xr.to_netcdf(path=netcdf_filename)
