#######################################################################################
# This script makes an overview map of a catchment, in this case the Rhine
# It includes elevation levels
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
import numpy as np
import matplotlib.pylab as plt
import intake
import pandas as pd
import cartopy.crs as ccrs
from cartopy.feature import BORDERS, RIVERS, ShapelyFeature
from cartopy.io.shapereader import Reader
import rasterio

from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter)

#######################################################################################
# Choose catchment
#######################################################################################
# load the lats and lons and state filename for catchment outline
lons_Rhine = [3,13]
lats_Rhine = [45,55]
fname_Rhine = 'mrb_basins.shp'

#######################################################################################
# Open catalog and load IFS data
#######################################################################################
# Load discharge data
cat = intake.open_catalog("https://data.nextgems-h2020.eu/catalog.yaml")
ds_prod = cat.IFS['IFS_9-FESOM_5-production']['2D_1h_camaflood'].to_dask()
ds_prod['time'] = ds_prod.time-np.timedelta64(1,'D')

#######################################################################################
# Function needed for city plotting (still need to be altered for other catchments)
#######################################################################################
def plot_cities(ax):
    # lat/lon coordinates of Rhine cities  
    lats = [51.86, 50.73, 47.56]
    lons = [6.12, 7.10, 7.59]
    cities = ["Lobith", "Bonn", "Basel"]
    symbols = ["ro", "rs", "r^"]
    sizes = [8,7,9] # for presentations: [16,14,18]
    for lon, lat, city, symbol, size in zip(lons, lats, cities, symbols, sizes):
        ax.plot(lon, lat, symbol, markeredgecolor='black', zorder=20, markersize=size, transform=ccrs.PlateCarree(), label=city)
        #ax.text(lon + 0.1, lat + 0.1, city, fontsize="large", weight='bold', transform=ccrs.PlateCarree()) # to have the label right next to the symbol
        plt.legend(loc='best', fontsize="large") # to have the labels in a legend


#######################################################################################
# Function to make an overview map
#######################################################################################

def make_overview_map(ds, lons=lons_Rhine, lats=lats_Rhine):
    # Get the indices of the lons and lats of the catchment for the plot
    lons9 = pd.unique(ds.lon)  # pd.unique so it's not rearranged
    lats9 = pd.unique(ds.lat)
    lons_index = np.where((lons9 > lons[0]) & (lons9 < lons[1]))
    lats_index = np.where((lats9 > lats[0]) & (lats9 < lats[1]))
    
    plt.figure(figsize=(6, 5), layout='constrained')
    ax = plt.axes(projection=ccrs.PlateCarree())
    extent = [lons9[lons_index[0][0]],lons9[lons_index[0][-2]],lats9[lats_index[0][0]],lats9[lats_index[0][-2]]]
    ax.set_extent(extent)
    # make the plot
    ax.coastlines()
    ax.add_feature(BORDERS)
    ax.add_feature(RIVERS)
    shp = ShapelyFeature(Reader('../GRDC_shapefiles/mrb_basins.shp').geometries(),
                     ccrs.PlateCarree(), edgecolor='k', facecolor='none', linewidth=3)
    ax.add_feature(shp)
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.left_labels = False
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    plot_cities(ax)  
    
    with rasterio.open('output_SRTMGL3.tif') as src:
        elevation_data = src.read(1)
        transform = src.transform
        height, width = elevation_data.shape
        lon = np.linspace(transform[2], transform[2] + transform[0] * width, width)
        lat = np.linspace(transform[5], transform[5] + transform[4] * height, height)
        lon2d, lat2d = np.meshgrid(lon, lat)
    cs = ax.contourf(lon2d, lat2d, elevation_data, cmap='terrain', levels=np.arange(-700, 3600, 100))
    # Optional: Add colorbar
    plt.colorbar(cs, ticks=np.linspace(-100,3500,7), shrink = 0.8).set_label(label='Elevation (m)', fontsize=16)
    fig_name = 'background_Rhine_catchment'
    plt.savefig('../plots/examples/'+fig_name, dpi=500)
    return fig_name, plt.show

make_overview_map(ds_prod)
