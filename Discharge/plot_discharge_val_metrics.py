#######################################################################################
# This script plots discharge statistics:
# - it loads the catchment names, NCC, NNSE and lag outcomes
# - it plots them as bars on two y-axis
# The list of statistics can be filled with your own values
#######################################################################################

#######################################################################################
# Imports needed
#######################################################################################
import numpy as np
import matplotlib.pyplot as plt
plt.rcdefaults()

#######################################################################################
# Data and catchment names needed
######################################################################################

list_catchments = ['Rhine', 'Danube', 'Rhône', 'Colorado', 'Po',
                   'Mississippi', 'São Francisco', 'Paraná',
                   'Yukon', 'Fraser',
                   'Fitzroy', 'Okavango', 'Amazon']

list_nnse = [0.21, 0.17, 0.16, 0.00, 0.19,
             0.59, 0.00, 0.01,
             0.81, 0.90,
             0.93, 0.39, 0.50]

list_ncc = [0.76, 0.94, 0.65, 0.77, 0.64,
            0.95, 0.91, 0.74,
            0.94, 0.97,
            0.97, 0.97, 0.95]

list_lag = [2, 1, 3, 2, 3,
            1, 0, 0,
            0, 0,
            0, -1, -1]


#######################################################################################
# Plotting function needed
######################################################################################

def plot_discharge_val_metrics_bar(list_nnse, list_ncc, list_lag, list_catchments):
    filename_plot = 'val_metrics_catch_comparison.pdf'
    x = np.arange(len(list_catchments))  # label positions
    width = 0.27
    fig, ax = plt.subplots()
    bars_nnse = ax.bar(x - width, list_nnse, width, label='NNSE', color='#06470c', edgecolor='black')
    bars_ncc = ax.bar(x, list_ncc, width, label='NCC', color='#929591', edgecolor='black')
    ax.set_ylim(-0.4, 1)

    ax2 = ax.twinx()
    bars_lag = ax2.bar(x + width, list_lag, width, label='Lag', color='#929591', hatch='///', edgecolor='black')
    ax2.set_ylim(-2, 5)
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xticks(x, labels=list_catchments, rotation=45, ha='right')
    ax.set_xlim(x[0] - 0.5, x[-1] + 0.5)
    ax.set_ylabel('Discharge NNSE and NCC')
    ax2.set_ylabel('Lag (months)')
    ax.legend(loc='lower left')
    ax2.legend(loc='lower right')
    ax.set_axisbelow(True)
    ax.grid(True, linestyle='--', alpha=0.7)
    # Background regions
    ax.axvspan(-0.5, 4.5, color='tab:purple', zorder=0, alpha=0.5)
    ax.axvspan(4.5, 7.5, color='#CC79A7', zorder=0, alpha=0.5)
    ax.axvspan(7.5, 9.5, color='#56B4E9', zorder=0, alpha=0.5)
    ax.axvspan(9.5, 12.5, color='#009E73', zorder=0, alpha=0.5)
    # Get tick labels
    labels = ax.get_yticklabels()
    # Hide first two
    for label in labels[:2]:
        label.set_visible(False)
    ticks = ax.yaxis.get_major_ticks()
    for tick in ticks[:2]:
        tick.label1.set_visible(False)
        tick.tick1line.set_visible(False)
    plt.tight_layout()
    plt.savefig('../../plots/examples/' + filename_plot, dpi=500)
    return plt.show


plot_discharge_val_metrics_bar(list_nnse, list_ncc, list_lag, list_catchments)
