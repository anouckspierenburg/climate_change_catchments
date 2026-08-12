#######################################################################################
# In this script a global overview map of the catchments will be made:
# - GRDC shapefiles have to be downloaded beforehand and placed in the right path
# - it reads in the shapefiles and colors and hatches it to the corresponding pattern
# - borders and coastlines are added with 50 m resolution
# - it is all plotted on Robinson projection through cartopy
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
import matplotlib.pylab as plt
from matplotlib.patches import Patch
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter)

#######################################################################################
# Function and inputs needed
#######################################################################################
catchments = ['Rhine','Danube','Rhône','Colorado','Po',
                   'Mississippi','São Francisco','Paraná',
                   'Yukon','Fraser',
                   'Fitzroy', 'Okavango','Amazon']
colors = ['tab:purple','tab:purple','tab:purple','tab:purple','tab:purple',
          '#CC79A7','#CC79A7','#CC79A7',
          '#56B4E9','#56B4E9',
          '#009E73','#009E73','#009E73']
hatches = ['','------','////////','++++++','........',
           '','------','////////',
           '','------',
           '','------','////////']

def make_overview_worldmap(catchments, colors, hatches):
    legend_elements = []
    fig = plt.figure()
    ax = fig.add_subplot(111,projection=ccrs.Robinson())
    ax.coastlines(resolution='50m', linewidth=0.6, rasterized=True)
    ax.add_feature(cf.BORDERS.with_scale('50m'),
               linewidth=0.5, rasterized=True)
    # Add catchments
    for catchment, color, hatch in zip(catchments, colors, hatches):
        shp = ShapelyFeature(Reader('../GRDC_shapefiles/'+catchment+'/mrb_basins.shp').geometries(), ccrs.PlateCarree(), edgecolor='black', linewidth=0.5, facecolor=color, hatch=hatch)
        ax.add_feature(shp, label=catchment)
        legend_elements.append(Patch(facecolor=color, edgecolor='black', hatch=hatch, label=catchment))
    # Add labels and gridlines
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.left_labels = False
    gl.right_labels = True
    gl.bottom_labels = True
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()

    fig_name = 'worldmap_catchments.pdf'
    cols = [legend_elements[0:5], legend_elements[5:8], legend_elements[8:10], legend_elements[10:13]]

    # Horizontal positions of each column
    x_anchors = [0.12, 0.35, 0.55, 0.75]
    y_anchor = 1.06 # vertical position below the map

    for handles, x in zip(cols, x_anchors):
        leg = fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(x, y_anchor), ncol=1, frameon=False, handlelength=1.5, handletextpad=0.6)

    fig.subplots_adjust(top=0.26)
   
    plt.tight_layout()
    plt.savefig('../plots/examples/'+fig_name, dpi=500, bbox_inches="tight",
    pad_inches=0.05)
    return fig_name, plt.show

make_overview_worldmap(catchments, colors, hatches)
