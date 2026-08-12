#######################################################################################
# This script calculates the NNSE, NCC and lag of the discharge:
# - it calculates the observed and historical mean monthly discharge
# - from those it calculates the NNSE,NCC and lag
# At the bottom the specific station can be chosen
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
from permetrics.regression import RegressionMetric
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from scipy.signal import correlate
plt.rcdefaults()

#######################################################################################
# Load stored observational data
#####################################################################################
path_obs = '/home/b/b301048/NextGEMS_hackathon/Observations/station_attributes_with_obsdis24h_197001-202312_v4.0_20240216_withEFAS.nc'
obs = xr.open_dataset(path_obs).load()

#######################################################################################
# Functions needed for calculating
#######################################################################################
def calc_mean_obsdis_dis(grdc_stationname, filename, catchment, stationname):
    dis_data = xr.open_dataset('../../stored_datasets/discharge_'+filename+'_30yr_hist.nc').load()
    dis_xr = dis_data.groupby('time.month').mean()
    dis = dis_xr.dis.to_numpy()
    # Get observational data (some stations have a different structure and are specified below)
    if stationname == 'Lobith':
        rhine_obs1 = obs.obsdis.where(obs.stationname == 'Lobith', drop=True).sel(
            time=slice('1990-01-01', '2013-12-31'))[:, 0]  # runs until '2014-01-01'
        rhine_obs2 = obs.obsdis.where(obs.stationname == 'Lobith', drop=True).sel(
            time=slice('2014-01-01', '2019-12-31'))[:, 1]
        obs_data = xr.concat([rhine_obs1, rhine_obs2], dim="time")
    elif stationname == 'Basel':
        basel_obs1 = obs.obsdis.where(obs.stationname == 'Basel Rheinhalle', drop=True).sel(
            time=slice('1990-01-01', '2011-12-31'))[:, 0]  # runs until '2012-01-01'
        basel_obs2 = obs.obsdis.where(obs.stationname == 'Basel Rheinhalle', drop=True).sel(
            time=slice('2012-01-01', '2019-12-31'))[:, 1]
        obs_data = xr.concat([basel_obs1, basel_obs2], dim="time")
    elif catchment == 'Po':
        obs_data = obs.obsdis.where(obs.stationname == grdc_stationname, drop=True).sel(
            time=slice('1990-01-01', '2019-12-31'))[:, 1]
    else:
        obs_data = obs.obsdis.where(obs.stationname == grdc_stationname, drop=True).sel(
            time=slice('1990-01-01', '2019-12-31'))[:, 0]
    obsdis = obs_data.groupby('time.month').mean().to_numpy()
    return obsdis, dis

def calc_NNSE_discharge(obsdis, dis, catchment, grdc_stationname):
    evaluator = RegressionMetric(obsdis, dis)
    print('NNSE in ' + catchment + ' ' + grdc_stationname + ': ' + str(evaluator.normalized_nash_sutcliffe_efficiency()))


def normalized_cross_correlation(x, y, catchment):
    """
    Compute the normalized cross-correlation (NCC) and lag between two 1D numpy arrays.
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length.")
    # Demean the signals
    x_demean = x - np.mean(x)
    y_demean = y - np.mean(y)
    # Compute full cross-correlation
    corr = correlate(x_demean, y_demean, mode="full")
    # Normalize by the product of standard deviations and number of points
    corr /= np.std(x) * np.std(y) * len(x)
    print(corr)
    # Compute lag array (negative = y leads, positive = x leads)
    lags = np.arange(-len(x) + 1, len(x))
    print(lags)
    # Get the maximum correlation and lag
    best_idx = np.argmax(corr)
    best_corr = corr[best_idx]
    best_lag = lags[best_idx]
    print(f"Best NCC {catchment}= {best_corr:.3f} at lag = {best_lag}")


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
# From here change the 0 in each list to the number of the station needed to calculate NNSE, NCC and lag.
#######################################################################################
grdc_stationname = list_grdc_stationnames[0]
filename = list_filenames[0]
catchment = list_catchments[0]
stationname = list_stationnames[0]

obsdis, dis = calc_mean_obsdis_dis(grdc_stationname, filename, catchment, stationname)
calc_NNSE_discharge(obsdis, dis, catchment, grdc_stationname)
normalized_cross_correlation(dis, obsdis, catchment)
