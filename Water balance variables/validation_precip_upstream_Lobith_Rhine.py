#######################################################################################
# This script performs the validation of historical precipitation with observations in Lobith
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
import earthkit.hydro as ekh
import numpy as np
import intake
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
from scipy import stats
plt.rcdefaults()

#######################################################################################
# Get precipitation observations
#######################################################################################
# Read CSV, skipping the first two lines
df = pd.read_csv(
    "../stored_datasets/Peobs",
    skiprows=2,                # ⬅️ skip the intro lines
    names=["time", "P"],   # manually name columns
    parse_dates=["time"],      # parse datetime strings
)
da = xr.DataArray(
    data=df["P"].values,
    dims=["time"],
    coords={"time": df["time"].values},
    name="P"
)

obs_mean = da.groupby(da['time'].dt.month).mean()
obs_m = da.resample({'time':'ME'}).mean()

#######################################################################################
# Open catalog and load IFS data, river network and gridsizes
#######################################################################################
# Load IFS data
cat = intake.open_catalog("https://data.nextgems-h2020.eu/catalog.yaml")
ds_m = cat.IFS['IFS_9-FESOM_5-production']['2D_monthly_0.25deg'].to_dask()
ds_m['time']=ds_m.time-np.timedelta64(1,'D')
ds_hist_m = cat.IFS['IFS_9-FESOM_5-production-hist']['2D_monthly_0.25deg'].to_dask()
ds_hist_m['time']=ds_hist_m.time-np.timedelta64(1,'D')  # changes accumulated variables to the correct month
# Load river network
network15 = ekh.river_network.load("cama_15min","4")
# get gridsizes
path_area = '/home/b/b383507/grd_area_data/ncdata.nc'
grdarea = xr.open_dataset(path_area).load()['grdare']
grdarea2= grdarea.to_numpy()

# Observational data
path_obs = '/home/b/b301048/NextGEMS_hackathon/Observations/station_attributes_with_obsdis24h_197001-202312_v4.0_20240216_withEFAS.nc'
obs = xr.open_dataset(path_obs).load()

#######################################################################################
# Reshaping IFS variables to network
#######################################################################################
def interpolate_IFS(var1, ds, grdarea=grdarea):
    # Define time, lat, lon coordinates
    time_vals = ds.time.values
    lat_vals = pd.unique(ds[var1].lat)
    lon_vals = pd.unique(ds[var1].lon)
    # reshape to (time, lat, lon)
    reshaped_data = np.reshape(ds[var1].values,(len(time_vals), len(lat_vals), len(lon_vals)))
    # Create new DataArray with correct dimensions
    new_da = xr.DataArray(reshaped_data, coords={'time': time_vals, 'lat': lat_vals, 'lon': lon_vals}, dims=['time', 'lat', 'lon'], name=var1)
    # Reorder lon to fit the order of CamaFlood network
    new_da2 = xr.concat([new_da.sel(lon=slice(-180.0,-0.25)),(new_da.sel(lon=slice(0,179.75)))],dim='lon')
    # add -180 at the end to make interpolation possible
    new_da3 = xr.concat([new_da2, new_da2.sel(lon=-180.0).assign_coords(lon=180.0)], dim="lon")
    # Interpolate IFS to camaflood network
    new_lats = np.linspace(89.875,-89.875,720)
    new_lons = np.linspace(-179.875, 179.875, 1440)
    ds_inter = new_da3.interp(time=time_vals, lat=new_lats, lon=new_lons)
    #if you want m^3
    ds_inter_area = ds_inter*grdarea  #ds*grdsize for accurrate outcomes 
    return ds_inter_area

#######################################################################################
# Apply upstream functions
#######################################################################################
def calc_confidence_interval(list_ds, daily=True):
    if daily:
        list_ds = [ds.resample({'time':'ME'}).mean() for ds in list_ds]
    stds = [ds.groupby('time.month').std(ddof=1) for ds in list_ds]
    n_count = [ds.groupby('time.month').count() for ds in list_ds]
    sems = [std/np.sqrt(n) for std,n in zip(stds,n_count)]
    t_vals = [stats.t.ppf(0.975, n - 1) for n in n_count]
    h_values = [t_val * sem for t_val,sem in zip(t_vals,sems)]
    return h_values

def upstream_mean_from_sum(ds_inter_area, obs=obs, network15=network15):
    ds_inter2 = ds_inter_area.to_numpy()
    ds = ekh.upstream.sum(network15, ds_inter2)   
    # Get the stations
    lobith_area = obs.CamaArea_15min.where(obs.stationname=='Lobith', drop=True)[0].values*1000000  #km^2 to m^2
    lobith_ds = (ds[:,152,744]/lobith_area)*1000 #m to mm
    return lobith_ds

time_vals = ds_m.time.values
time_vals_hist = ds_hist_m.time.values
def monthly_mean_xarray(station_ds, time_vals, var1):
    # Create xarray DataArray
    da_xarray = xr.DataArray(station_ds, coords={'time': time_vals}, dims='time', name=var1)
    station_mean = da_xarray.groupby(da_xarray['time'].dt.month).mean()
    return station_mean


#######################################################################################
# Applied functions
#######################################################################################
var1 = 'tp'
ds_inter_area_hist = interpolate_IFS(var1, ds_hist_m)
lobith_ds_h = upstream_mean_from_sum(ds_inter_area_hist)
lobith_ds_h = xr.DataArray(lobith_ds_h, coords={'time': time_vals_hist}, dims='time', name='tp')

means_lobith = [monthly_mean_xarray(lobith_ds_h,time_vals_hist,var1),
               obs_mean]
list_lobith = [lobith_ds_h, obs_m]
h_values_lobith = calc_confidence_interval(list_lobith)
runs_lobith = ['Historical', 'Observations'] 

def timeseries_stations_validation_ci(list_runs, list_ds, h_values, station):
    fontsize = 12
    months = ['J','F','M','A','M','J','J','A','S','O','N','D']
    days_per_month = [31,28.25,31,30,31,30,31,31,30,31,30,31]
    colors = ['#555555','tab:blue']
    linestyles = ['--','-']
    filename=station+'_upstream_ci_monthly_mean_precipitation.pdf'
    fig, ax = plt.subplots()
    for (run,ds,color,h,linestyle) in zip(list_runs,list_ds,colors,h_values,linestyles):
        if run != 'Observations':
            ds = ds/days_per_month
            h = h/days_per_month
        ax.plot(ds.month, ds, color,label=run, linestyle=linestyle)
        lower = ds-h
        upper = ds+h
        plt.fill_between(ds.month, lower.values, upper.values, color=color, alpha=0.3)
    plt.legend(fontsize=fontsize, loc='lower right')
    ax.set_xticks(list_ds[0].month, labels=months,fontsize=fontsize)
    ax.set_xlim(list_ds[0].month[0], list_ds[0].month[-1])
    ax.set_yticklabels(np.arange(0, 4.5, step=0.5), fontsize=fontsize)
    ax.set_ylim(0,4.0)
    ax.set_xlabel('Months',fontsize=fontsize)
    ax.set_ylabel('Precipitation (mm/day)', fontsize=fontsize)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.title('Precipitation upstream '+station)
    plt.tight_layout()
    plt.savefig('../plots/examples/p_'+filename, dpi=500)
    return plt.show

timeseries_stations_validation_ci(runs_lobith, means_lobith, h_values_lobith, 'Lobith')
