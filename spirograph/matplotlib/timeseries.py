
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt



# To add
#  language


## idees pour labels: arg replace_label


def line_ts(da, ax=None, dict_metadata=None, sub_kw=None, line_kw=None):
    """
    plot unique time series from  dataframe
    ax: user-specified matplotlib axis
    data: dataset ou dataframe xarray
    dict_metadata: join figure element to xarray dataset element
    sub_kw: matplotlib subplot kwargs
    line_kw : maplotlib or xarray line kwargs
    """
    #return empty dicts if no kwargs
    kwargs = empty_dic({'sub_kw': sub_kw, 'line_kw': line_kw})

    #initialize fig, ax if ax not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    #plot
    da.plot.line(ax=ax, **kwargs['line_kw'])

    #add/modify plot elements
    if dict_metadata:
        ax_dict_metadata(ax, dict_metadata, da, 'lines')
    if 'label' in dict_metadata:
        ax.legend()
    return ax



#out of function

da = da_pct
dict_metadata = {'title':'my custom title'}
da_pct.plot.line()
