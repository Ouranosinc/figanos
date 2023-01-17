
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt



# To add
#  language
#  smoothing
# manual mode?
# logo
# default value for attributes to use?


## idees pour labels: arg replace_label


def line_ts(data, ax=None, use_attrs=None, sub_kw=None, line_kw=None, ensemble = False):
    """
    Plots unique time series from dataframe
    Args:
        ax: user-specified matplotlib axis
        da: Xarray DataArray containing the data to plot
        use_attrs: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw : maplotlib or xarray line kwargs
    Returns:
        matplotlib axis
    """
    kwargs = empty_dict({'sub_kw': sub_kw, 'line_kw': line_kw})

    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    #arrange data
    plot_dict = {}
    if str(type(data)) == "<class 'xarray.core.dataset.Dataset'>":
        for k,v in data.data_vars.items():
            plot_dict[k] = v
    else:
        plot_dict[data.name] = data

    #set up for ensemble
    sorted_line_y = []
    sorted_line_x = []

    #plot
    for name, xr in plot_dict.items():
        #da.plot.line(ax=ax, **kwargs['line_kw']) # using xarray plotting
        ax.plot(xr[xr.dims[0]], xr.values, label = name) #assumes the only dim is time

        if ensemble is True:
            sorted_line_x.append(xr[xr.dims[0]])
            sorted_line_y.append(xr.values)

    if ensemble is True:
        ax.fill_between()

    #add/modify plot elements
    if use_attrs:
        set_plot_attrs(use_attrs, data, ax)

    ax.legend()

    return ax

#test

line_ts(da_pct, use_attrs= {'title': 'ccdp_name'})
