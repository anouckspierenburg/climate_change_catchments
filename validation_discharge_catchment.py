#######################################################################################
# This script plots discharge in a specific station:
# - it loads the observational, historical and future monthly discharge 
# - it adds the 95% confidence interval over the 30 year period.
# At the bottom the station can be chosen.
#######################################################################################


#######################################################################################
# Imports needed
#######################################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import xarray as xr
import matplotlib.cm as cm
from matplotlib import colors,colorbar
from scipy import stats

#######################################################################################
# Functions needed for the discharge plot
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

def timeseries_stations_validation_ci(path,list_runs, list_ds, h_values, catchment, stationname):
    """
    This function plots a timeseries of the monthly mean discharge data. 
    It adds 95% confidence intervals, and stores the plot.
    """
    fontsize = 12 
    months = ['J','F','M','A','M','J','J','A','S','O','N','D']
    colors = ['#555555','#008080', 'tab:orange'] # gray,teal,orange
    linestyles = ['--','-','-']
    filename=str(catchment+'_'+stationname+'_ci_monthly_mean_discharge.pdf')
    fig, ax = plt.subplots()
    for (run,ds,color,h,linestyle) in zip(list_runs,list_ds,colors,h_values,linestyles):
        ax.plot(ds.month, ds, color, linestyle=linestyle, label=run)
        lower = ds-h
        upper = ds+h
        ax.fill_between(ds.month, lower.values, upper.values, alpha=0.3, color=color)
    ax.legend(loc='upper right',fontsize=fontsize)     
    ax.set_xticks(list_ds[1].month, labels=months,fontsize=fontsize)
    ax.set_xlim(list_ds[1].month[0], list_ds[1].month[-1])
    ax.set_ylim(0)
    ax.set_xlabel('Months',fontsize=fontsize)
    ax.set_ylabel('Discharge ($m^3/s$)',fontsize=fontsize)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title('Discharge '+stationname)     
    fig.tight_layout()
    fig.canvas.draw()
    fig.savefig(path+filename, dpi=500)
    #plt.close(fig) # Uncomment if you don't want the plot to pop up
    return

def load_and_make_discharge_timeseries(path,filename, grdc_stationname, catchment, stationname):
    """
    This function loads the discharge data from nc files into an xarray, 
    as well as the observational data of the years 1990-2019.
    Then resamples to daily and calculates the monthly mean and confidence intervals.
    It then calls the plotting function.
    """
    # Load discharge data (check if the path is correct for your data)
    path_obs = '/home/b/b301048/NextGEMS_hackathon/Observations/station_attributes_with_obsdis24h_197001-202312_v4.0_20240216_withEFAS.nc'
    obs = xr.open_dataset(path_obs).load()
    dis_h = xr.open_dataset('../../stored_datasets/discharge_'+filename+'_30yr_hist.nc').load()
    dis =  xr.open_dataset('../../stored_datasets/discharge_'+filename+'_30yr_fut.nc').load()
    # Resample to daily from hourly
    cama_h = dis_h.dis.resample({'time':'D'}).mean()
    cama = dis.dis.resample({'time':'D'}).mean()
    # Get observational data (some stations have a different structure and are specified below)
    if stationname == 'Lobith':
        rhine_obs1 = obs.obsdis.where(obs.stationname=='Lobith', drop=True).sel(time=slice('1990-01-01', '2013-12-31'))[:,0] #runs until '2014-01-01' 
        rhine_obs2 = obs.obsdis.where(obs.stationname=='Lobith', drop=True).sel(time=slice('2014-01-01', '2019-12-31'))[:,1] 
        obs_data = xr.concat([rhine_obs1, rhine_obs2], dim="time")
    elif stationname == 'Basel':
        basel_obs1 = obs.obsdis.where(obs.stationname=='Basel Rheinhalle', drop=True).sel(time=slice('1990-01-01', '2011-12-31'))[:,0] #runs until '2012-01-01'
        basel_obs2 = obs.obsdis.where(obs.stationname=='Basel Rheinhalle', drop=True).sel(time=slice('2012-01-01', '2019-12-31'))[:,1]
        obs_data = xr.concat([basel_obs1, basel_obs2], dim="time")
    elif catchment == 'Po':
        obs_data = obs.obsdis.where(obs.stationname==grdc_stationname, drop=True).sel(time=slice('1990-01-01', '2019-12-31'))[:,1]
    else:
        obs_data = obs.obsdis.where(obs.stationname==grdc_stationname, drop=True).sel(time=slice('1990-01-01', '2019-12-31'))[:,0]   
    # Put the three sets into a list for easy plotting
    ds_all = [obs_data, cama_h, cama]
    # Calculate the monthly mean and the h_values for plot and confidence interval
    ds_m = [ds.groupby('time.month').mean() for ds in ds_all]
    h_values = calc_confidence_interval(ds_all)
    run_names = ['Observations','Historical', 'Future']
    timeseries_stations_validation_ci(path,run_names, ds_m, h_values, catchment, stationname)
    return 

#######################################################################################
# Lists of files and catchment names used
#######################################################################################
list_filenames = ['Lobith','Izmail_Danube','Beaucaire_Rhone','Hoover_Colorado','Pontelagoscuro_Po',
                  'Vicksburg_Mis','Juazeiro_Sao_Francisco','Corrientes_Parana',
                  'Pilot_Yukon','Hope_Fraser',
                  'Willare_Fitzroy','Mohembo_Oka','Manacapuru_Amazon']

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
# From here change the 0 in each list to the number of the station needed to make a timeseries plot of the discharge.
#######################################################################################
if __name__ == "__main__":
    # Information that you can change
    path = '../../plots/thesis/discharge/tests/'
    filename = list_filenames[0]
    grdc_stationname = list_grdc_stationnames[0]
    catchment = list_catchments[0]
    stationname = list_stationnames[0]
   
    load_and_make_discharge_timeseries(path, filename, grdc_stationname, catchment, stationname) 


