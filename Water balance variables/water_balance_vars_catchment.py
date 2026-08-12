#######################################################################################
# This script plots the water balance variables:
# - it reshapes and interpolates the data
# - uses earthkit to calculate the upstream means in a certain station
# - plots the historical, future or difference
# At the bottom the specifics and station can be chosen
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
# Data needed 
#######################################################################################
# Load observational data
path_obs = '/home/b/b301048/NextGEMS_hackathon/Observations/station_attributes_with_obsdis24h_197001-202312_v4.0_20240216_withEFAS.nc'
obs = xr.open_dataset(path_obs).load()
# Load IFS data
cat = intake.open_catalog("https://data.nextgems-h2020.eu/catalog.yaml")
ds_m = cat.IFS['IFS_9-FESOM_5-production']['2D_monthly_0.25deg'].to_dask()
ds_m['time'] = ds_m.time-np.timedelta64(1, 'D')
ds_hist_m = cat.IFS['IFS_9-FESOM_5-production-hist']['2D_monthly_0.25deg'].to_dask()
ds_hist_m['time']=ds_hist_m.time-np.timedelta64(1, 'D')  # changes accumulated variables to the correct month
# Load river network
network15 = ekh.river_network.load("cama_15min","4")
# get grid sizes
path_area = '../../grd_area_data/ncdata.nc'
grdarea = xr.open_dataset(path_area).load()['grdare']
grdarea2 = grdarea.to_numpy()

#######################################################################################
# Functions needed for calculating 
#######################################################################################
def calc_confidence_interval(list_ds, daily=True):
    """
    This function calculates the confidence interval per month.
    Input: list of xarray datasets.
    Output: list of h_values per dataset, with in each 12 h_values one per month.
    """
    if daily:
        list_ds = [ds.resample({'time':'ME'}).mean() for ds in list_ds]
    stds = [ds.groupby('time.month').std(ddof=1) for ds in list_ds]
    n_count = [ds.groupby('time.month').count() for ds in list_ds]
    sems = [std/np.sqrt(n) for std,n in zip(stds,n_count)]
    t_vals = [stats.t.ppf(0.975, n - 1) for n in n_count] 
    h_values = [t_val * sem for t_val,sem in zip(t_vals,sems)]
    return h_values
    
def interpolate_IFS(var1, ds, grdarea=grdarea):
    """
    This function reshapes and interpolates the IFS data to a river network to be able to use
    earthkit hydro.
    """
    # Define time, lat, lon coordinates
    time_vals = ds.time.values
    lat_vals = pd.unique(ds[var1].lat)
    lon_vals = pd.unique(ds[var1].lon)
    # reshape to (time, lat, lon)
    reshaped_data = np.reshape(ds[var1].values,(len(time_vals), len(lat_vals), len(lon_vals)))
    # Create new DataArray with correct dimensions
    new_da = xr.DataArray(reshaped_data, coords={'time': time_vals, 'lat': lat_vals, 'lon': lon_vals}, dims=['time', 'lat', 'lon'], name=var1)
    # Reorder lon to fit the order of CaMa-Flood network
    new_da2 = xr.concat([new_da.sel(lon=slice(-180.0,-0.25)),(new_da.sel(lon=slice(0,179.75)))],dim='lon')
    # add -180 at the end to make interpolation possible
    new_da3 = xr.concat([new_da2, new_da2.sel(lon=-180.0).assign_coords(lon=180.0)], dim="lon")
    # Interpolate IFS to camaflood network
    new_lats = np.linspace(89.875,-89.875,720)
    new_lons = np.linspace(-179.875, 179.875, 1440)
    ds_inter = new_da3.interp(time=time_vals, lat=new_lats, lon=new_lons)
    #if you want m^3
    ds_inter_area = ds_inter*grdarea  # ds*grdsize for accurate outcomes
    return ds_inter_area

vars1 = ['tp','sro','ssro','e'] 
# Interpolate the values to network for all variables
inter_ds_fut = [interpolate_IFS(var1, ds_m) for var1 in vars1]  # load them once to save time plotting
inter_ds_hist = [interpolate_IFS(var1, ds_hist_m) for var1 in vars1]

def upstream_mean_from_sum_catchment(ds_inter_area, grdc_stationname):
    """
    Apply upstream functions to get the mean upstream of a certain variable.
    """
    ds_inter2 = ds_inter_area.to_numpy()
    ds = ekh.upstream.sum(network15, ds_inter2)   
    # Get the station upstream area
    area = obs.CamaArea_15min.where(obs.stationname==grdc_stationname, drop=True)[0].values*1000000  #km^2 to m^2
    # Find the lat and lon index of the station in the observations
    stations_index = [int(obs.CamaY1_15min.where(obs.stationname==grdc_stationname, drop=True)[0]), int(obs.CamaX1_15min.where(obs.stationname==grdc_stationname, drop=True)[0])] 
    # Get the data of the specific station
    station_ds = (ds[:,stations_index[0]-1,stations_index[1]-1]/area)*1000 # to get mm
    return station_ds

time_vals = ds_m.time.values
time_vals_hist = ds_hist_m.time.values

def monthly_mean_xarray(station_ds, time_vals, var1):
    # Create xarray DataArray
    da_xarray = xr.DataArray(station_ds, coords={'time': time_vals}, dims='time', name=var1)
    return da_xarray

#######################################################################################
# Functions needed for plotting and calling
#######################################################################################
def timeseries_station_all_vars(path, list_ds, catchment, h_values, station, future=True, plot_title=False, dS=False):
    """
    This function plots the future or historical upstream mean of the water balance variables, optionally together with the storage term dS.
    """
    fontsize = 12
    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    days_per_month = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if future:
        filename = str(catchment+'_'+station+'_fut_ci_all_vars')
        timing = 'Future '
    else:
        filename = str(catchment+'_'+station+'_hist_ci_all_vars')
        timing = 'Historical '   
    colors = ['tab:blue', 'tab:purple', 'tab:green', 'tab:red']
    names = ['Precipitation','Surface runoff','Subsurface runoff','Evaporation']
    fig, ax = plt.subplots()
    for (name, ds, color, h) in zip(names, list_ds, colors, h_values):
        ds = ds/days_per_month
        ax.plot(ds.month, ds, color, label=name)
        h = h/days_per_month
        lower = ds-h
        upper = ds+h
        plt.fill_between(ds.month, lower.values, upper.values, alpha=0.3,color=color)
    if dS:  
        list_ds = list_ds+[(list_ds[0]-(list_ds[1]+list_ds[2]+list_ds[3]))]
        ax.bar(list_ds[0].month, list_ds[4]/days_per_month,color='tab:orange',label='dS', alpha=0.5, width=0.5)
        ax.axhline(0, color='black', linewidth=1)   # for storage bars with negative values
        total_dS = (sum(list_ds[4])/sum(list_ds[0]))*100
        plt.title(timing+'upstream mean of '+catchment+' in '+station+'\n (total dS as percentage of total tp: '+ str(np.round(total_dS.values,1))+'%)')
    plt.legend(fontsize=fontsize, loc='best')
    ax.set_xticks(list_ds[1].month, labels=months,fontsize=fontsize)
    ax.set_xlim(list_ds[1].month[0], list_ds[1].month[-1])
    ax.set_xlabel('Months',fontsize=fontsize)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylabel('Water balance component ($mm/day$)',fontsize=fontsize)     #decomment
    if plot_title:
        plt.title(timing+'upstream mean of '+catchment+' in '+station, fontsize=fontsize)
    plt.tight_layout()
    plt.savefig(path+filename+'.pdf', dpi=500)
    return plt.show

def timeseries_station_diff_all_vars(path, list_ds, catchment, station, plot_title=False):
    """
    This function plots the difference between the future and historical upstream mean of the water balance variables.
    """
    fontsize = 12
    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    days_per_month = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    filename = str(catchment+'_'+station+'_diff_all_vars')
    colors = ['tab:blue', 'tab:purple', 'tab:green', 'tab:red']
    names = ['Precipitation','Surface runoff','Subsurface runoff','Evaporation']
    fig, ax = plt.subplots()
    for (ds,color,name) in zip(list_ds,colors,names):
        ds = ds/days_per_month
        ax.plot(ds.month, ds, color, label=name, linewidth=2)
    ax.axhline(0, color='black', linewidth=1)  
    plt.legend(fontsize=fontsize, loc='best')
    ax.set_xticks(list_ds[1].month, labels=months,fontsize=fontsize)
    ax.set_xlim(list_ds[1].month[0], list_ds[1].month[-1])
    ax.set_xlabel('Months',fontsize=fontsize)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylabel('Difference ($mm/day$)',fontsize=fontsize)
    if plot_title:
        plt.title('Upstream mean difference of '+catchment+' in '+station, fontsize=fontsize)
    plt.tight_layout()
    plt.savefig(path+filename+'.pdf', dpi=500)
    return plt.show
    
#######################################################################################
# Applied functions yearly mean plot easily changeable
#######################################################################################
def calc_and_plot_all_vars_per_station(path, catchment, grdc_stationname, stationname, future=True, plot_title=False, dS=False, difference=False):
    """
    This function calculates per variable the upstream monthly mean and confidence interval.
    Then calls the plotting function.
    """
    # State all variables
    vars1 = ['tp','sro','ssro','e']
    # Choose difference or specific timing
    if difference:
        total_ds = [upstream_mean_from_sum_catchment(ds_fut, grdc_stationname)-upstream_mean_from_sum_catchment(ds_hist, grdc_stationname) for ds_fut,ds_hist in zip(inter_ds_fut,inter_ds_hist)]
    else:
        if future:
            inter_ds = inter_ds_fut
        else:
            inter_ds = inter_ds_hist
        # Calculate the upstream means for all variables and all stations
        total_ds = [upstream_mean_from_sum_catchment(ds, grdc_stationname) for ds in inter_ds]  # 4 var
    # Get the mean yearly values
    signs = [1,1,1,-1] # -1 for evaporation
    list_vars = [monthly_mean_xarray(ds, time_vals, var1)*sign for ds, var1, sign in zip(total_ds, vars1, signs)]
    list_vars_m = [list_var.groupby(list_var['time'].dt.month).mean() for list_var in list_vars]
    if difference == False:
        h_values = calc_confidence_interval(list_vars, daily=False)
        timeseries_station_all_vars(path, list_vars_m, catchment, h_values, stationname, future, plot_title, dS)
    else:
        timeseries_station_diff_all_vars(path, list_vars_m, catchment, stationname, plot_title)
    return    

#######################################################################################
# Lists of catchment names used
#######################################################################################
list_grdc_stationnames = ['Lobith','Ceatal Izmail','Le Rhone A Beaucaire','Below Hoover Dam Az Nv','Pontelagoscuro',
                          'Vicksburg Ms','Juazeiro','Corrientes',
                          'Pilot Station Ak','Hope',
                          'Willare','Mohembo Mtaembo 67932112','Manacapuru']

list_catchments = ['Rhine','Danube','Rhône','Colorado','Po',
                   'Mississippi','São Francisco','Paraná',
                   'Yukon','Fraser',
                   'Fitzroy', 'Okavango','Amazon']

list_stationnames = ['Lobith','Ceatal Izmail','Beaucaire','Hoover','Pontelagoscuro',
                          'Vicksburg','Juazeiro','Corrientes',
                          'Pilot_Station','Hope',
                          'Willare','Mohembo','Manacapuru']

#######################################################################################
# From here change the 0 in each list to the number of the station needed to make a plot of the water balance variables.
#######################################################################################

# Information that you can change
path = '../../plots/examples/'
grdc_stationname = list_grdc_stationnames[0]
catchment = list_catchments[0]
stationname = list_stationnames[0]
# For historical: future=False, for future: future=True
future = True 
plot_title = True
# True if you want the storage term dS in bars in the plot. If dS=True, set plot_title=False 
dS = True
# True if you want the difference between future and historical. If difference=True, set dS=False
difference = False
 
calc_and_plot_all_vars_per_station(path, catchment, grdc_stationname, stationname, future, plot_title, dS, difference)
