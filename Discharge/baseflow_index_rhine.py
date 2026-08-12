#######################################################################################
# This script calculates the baseflow index from the discharge for the Rhine catchment in:
# Lobith, Bonn and Basel
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
import matplotlib.pyplot as plt
import xarray as xr
plt.rcdefaults()

#######################################################################################
# Load stored data
#######################################################################################
# load station CaMa-Flood discharge data
lobith_dis_h = xr.open_dataset('../stored_datasets/discharge_Lobith_30yr_hist.nc').load()
bonn_dis_h = xr.open_dataset('../stored_datasets/discharge_Bonn_30yr_hist.nc').load()
basel_dis_h = xr.open_dataset('../stored_datasets/discharge_Basel_30yr_hist.nc').load()
lobith_dis = xr.open_dataset('../stored_datasets/discharge_Lobith_30yr_fut.nc').load()
bonn_dis = xr.open_dataset('../stored_datasets/discharge_Bonn_30yr_fut.nc').load()
basel_dis = xr.open_dataset('../stored_datasets/discharge_Basel_30yr_fut.nc').load()

lobith_cama = lobith_dis.dis
bonn_cama = bonn_dis.dis
basel_cama = basel_dis.dis
lobith_cama_h = lobith_dis_h.dis
bonn_cama_h = bonn_dis_h.dis
basel_cama_h = basel_dis_h.dis

# Put into one ds
val_ds = [lobith_cama_h, lobith_cama, bonn_cama_h, bonn_cama, basel_cama_h, basel_cama]
list_stations = ['Lobith', 'Lobith \nfuture','Bonn','Bonn \nfuture','Basel','Basel \nfuture']

# Resample the hourly time series to daily and take the minimum per day
daily_streamflows = [ds.resample({'time': 'D'}).min() for ds in val_ds]
# Resample to monthly, calculating the mean minimum daily streamflow (Baseflow)
monthly_baseflows = [daily_streamflow.resample({'time': 'ME'}).mean() for daily_streamflow in daily_streamflows]
# Calculate the monthly total streamflow (or monthly mean streamflow)
monthly_total_streamflows = [ds.resample({'time': 'ME'}).mean() for ds in val_ds]
# Compute the baseflow index (BFI) as baseflow / total streamflow
baseflow_indexs = [monthly_baseflow / monthly_total_streamflow for (monthly_baseflow, monthly_total_streamflow) in zip(monthly_baseflows,monthly_total_streamflows)]
# Calculate climatology by grouping the baseflow index by month and averaging across years
baseflow_climatologys = [baseflow_index.groupby(baseflow_index.time.dt.month).mean() for baseflow_index in baseflow_indexs]
months = ['J','F','M','A','M','J','J','A','S','O','N','D']
colors = ['tab:brown', 'tab:brown', 'tab:pink','tab:pink','tab:olive','tab:olive']
linestyles = ['--', '-', '--','-','--','-']
fontsize = 12

for (baseflow_climatology,list_station, color, linestyle) in zip(baseflow_climatologys,list_stations, colors, linestyles):
    plt.plot(baseflow_climatology.month, baseflow_climatology, color, label=list_station, linestyle=linestyle,linewidth=2)
plt.legend(ncols=3, fontsize=fontsize)
plt.xticks(baseflow_climatologys[1].month, labels=months, fontsize=fontsize)
plt.xlim(baseflow_climatologys[1].month[0], baseflow_climatologys[1].month[-1])
plt.ylim(0.92, 1.0)
plt.xlabel('Months', fontsize=fontsize)
plt.ylabel('BFI', fontsize=fontsize)
plt.grid(True, linestyle='--', alpha=0.7)
plt.title('Baseflow index (baseflow/mean streamflow)')
plt.tight_layout()
filename= 'baseflow_index_Rhine_new.pdf'
plt.savefig('../plots/examples/'+filename, dpi=500)
