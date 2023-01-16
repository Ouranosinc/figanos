
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt



# To add
#  language
#  smoothing
# m??anual mode: asks for input for title,


## idees pour labels: arg replace_label


def line_ts(da, ax=None, use_attrs=None, sub_kw=None, line_kw=None):
    """
    Plots unique time series from dataframe

    Args:
        ax: user-specified matplotlib axis
        data: Xarray DataArray containing the data to plot
        dict_metadata: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw : maplotlib or xarray line kwargs

    Returns:
        matplotlib axis
    """
    #return empty dicts if no kwargs
    kwargs = empty_dict({'sub_kw': sub_kw, 'line_kw': line_kw})

    #initialize fig, ax if ax not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    #plot
    line_1 = da.plot.line(ax=ax, **kwargs['line_kw'])
    #line_1.set_label()

    #add/modify plot elements
    if use_attrs:
        ax_dict_metadata(ax, use_attrs, da)

    return ax



#out of function

line_ts(da_pct, use_attrs= {'title': 'ccdp_name'})
