
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt



# To add
#  language
#  smoothing
# logo
# transformer dates de days since... a dates?
# use_attrs = default au lieu de None??


## idees pour labels: arg replace_label


def line_ts(data, ensemble = False, ax=None, use_attrs=None, sub_kw=None, line_kw=None):
    """
    Plots unique time series from 1D dataframe or dataset
    Args:
        ax: user-specified matplotlib axis
        da: Xarray DataArray containing the data to plot
        use_attrs: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw : matplotlib or xarray line kwargs
    Returns:
        matplotlib axis
    """
    kwargs = empty_dict({'sub_kw': sub_kw, 'line_kw': line_kw})

    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    #arrange data
    array_dict = {}
    if str(type(data)) == "<class 'xarray.core.dataset.Dataset'>":
        for k, v in data.data_vars.items():
            array_dict[k] = v
            if ensemble is True:
                sorted_lines = sort_lines(array_dict)
    else:
        array_dict[data.name] = data

    #plot
    if ensemble is True:

        line_1 = ax.plot(array_dict[sorted_lines['middle']][array_dict[sorted_lines['middle']].dims[0]],
                array_dict[sorted_lines['middle']].values, **kwargs['line_kw'])

        ax.fill_between(array_dict[sorted_lines['lower']][array_dict[sorted_lines['lower']].dims[0]],
                        array_dict[sorted_lines['lower']].values,
                        array_dict[sorted_lines['upper']].values,
                        color = line_1[0].get_color(),
                        edgecolor = 'white', alpha = 0.2)
    else:
        for name, arr in array_dict.items():
            ax.plot(arr[arr.dims[0]], arr.values,label = name, **kwargs['line_kw'])

    #add/modify plot elements
    plot_attrs = default_attrs(data)
    if use_attrs:
        for k, v in use_attrs.items():
            plot_attrs[k] = v

    set_plot_attrs(plot_attrs, data, ax)


    ax.legend()

    return ax

#test

line_ts(da_pct, use_attrs={'title': 'ccdp_name'}, line_kw = {'color': 'red'})
line_ts(ds_pct, ensemble=True, line_kw={'color': 'red'})
line_ts(ds_pct, use_attrs= {'title': 'ccdp_name'}, ensemble = True,line_kw = {'color':'red'})
