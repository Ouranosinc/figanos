
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd



# To add
#   language
#   logo
#   transformer dates de days since... a dates?
#   erreur ensemble+DA
#   xlim
#   assigning kwargs to different lines: list??
# input = dict(nom:ds ou nom:da), avec noms qui deviennent legend
# detect if ensemble (mean, max, min _pNN), detect if in coords
    ## fonction qui label chaque entree comme {global_label:, type: ds/da, ens = da/ds/var_ens/dim_ens},
# assumer que 'time' est la dimension, et fct qui regarde
# lorsque plusieurs datasets, prendre
# lorsque dataset n<est pas ensemble, label serait global_label_variable




def line_ts(data, ensemble = False, ax=None, use_attrs=None, sub_kw=None, line_kw=None):
    """
    Plots time series from 1D dataframe or dataset
    Args:
        ax: user-specified matplotlib axis
        data: dictionary of labeled Xarray DataArrays or Datasets
        use_attrs: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw : matplotlib or xarray line kwargs
    Returns:
        matplotlib axis
    """
    kwargs = empty_dict({'sub_kw': sub_kw, 'line_kw': line_kw})

    #set default args and add/replace user inputs
    #plot_attrs = {'title': 'long_name', 'xlabel': 'time', 'ylabel': 'standard_name', 'yunits': 'units'}
    #sub_kw = {}
    #line_kw = {'label': 'name'}



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
            ax.plot(arr[arr.dims[0]], arr.values, label = name, **kwargs['line_kw'])

    #add/modify plot elements
    plot_attrs = default_attrs()
    if use_attrs:
        for k, v in use_attrs.items():
            plot_attrs[k] = v
    set_plot_attrs(plot_attrs, data, ax)

    ax.legend()


    return ax

#test

fig, ax = plt.subplots()
line_ts({'rcp2.5': dataset1, 'rcp8.5': dataset2}, ax = ax)
line_ts(line, ax = ax)


line_ts(da_pct, line_kw = {'color': 'red'})
line_ts(ds_pct, use_attrs= {'title': 'ccdp_name'})
line_ts(ds_pct, ensemble=True, line_kw={'color': 'red'})


mod_da_pct = da_pct + da_pct*0.05
fig, ax1 = plt.subplots()
line_ts(ds_pct, ensemble=True, ax = ax1)
line_ts(mod_da_pct, ax = ax1)
