
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd


# To add
#   language
#   logo
#   xlim
# fct qui s'assure que 'time' est une dimension
# FIX label used twice
# show lat,lon
# show percentiles?
# option for legend placement
#CHECK: if data not a dict, line_kw not a dict of dicts
#Exceptions, no data, data is all nans
# cftime conversion?
# ylabel at end of line rather than legend
#special term in use_attrs to use dict key



def line_ts(data, ax=None, use_attrs=None, sub_kw=None, line_kw=None):
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

    # if only one data input, insert in dict
    non_dict_data = False
    if type(data) != dict:
        data = {'data_1': data}
        line_kw = {'data_1': empty_dict(line_kw)}
        non_dict_data = True

    # set default kwargs and add/replace with user inputs, if provided
    plot_attrs = {'title': 'long_name',
                  'xlabel': 'time',
                  'ylabel': 'standard_name',
                  'yunits': 'units'}
    plot_sub_kw = {}
    if non_dict_data is True:
        plot_line_kw = {}
    else:
        plot_line_kw = {name: {} for name in data.keys()}

    for user_dict, attr_dict in zip([use_attrs, sub_kw, line_kw], [plot_attrs, plot_sub_kw, plot_line_kw]):
        if user_dict:
            for k, v in user_dict.items():
                attr_dict[k] = v

    kwargs = {'sub_kw': plot_sub_kw, 'line_kw': plot_line_kw}

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])


    # build dictionary of array 'categories', which determine how to plot (see get_array_categ fct)
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # get data to plot

    for name, arr in data.items():

        if array_categ[name] in ['PCT_VAR_ENS', 'STATS_VAR_ENS', 'PCT_DIM_ENS_DA']:

            # extract each line from the datasets
            array_data = {}
            if array_categ[name] == 'PCT_DIM_ENS_DA':
                for pct in arr.percentiles:
                    array_data[str(int(pct))] = arr.sel(percentiles=int(pct))
            else:
                for k, v in arr.data_vars.items():
                    array_data[k] = v

            # create a dictionary labeling the middle, upper and lower line
            sorted_lines = sort_lines(array_data)


            # plot the ensemble
            line_1 = ax.plot(array_data[sorted_lines['middle']]['time'],
                             array_data[sorted_lines['middle']].values, **kwargs['line_kw'][name], label=name)

            ax.fill_between(array_data[sorted_lines['lower']]['time'],
                            array_data[sorted_lines['lower']].values,
                            array_data[sorted_lines['upper']].values,
                            color=line_1[0].get_color(),
                            edgecolor='white', alpha=0.2)

        elif array_categ[name] in ['NON_ENS_DS']:

                for k, sub_arr in arr.data_vars.items():
                    sub_name = name + "_" + sub_arr.name  # creates plot label
                    ax.plot(sub_arr['time'], sub_arr.values, **kwargs['line_kw'][name], label=sub_name)


        else: # should be DataArray

            ax.plot(arr['time'], arr.values, **kwargs['line_kw'][name], label=name)

    #add/modify plot elements according to the first entry.
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    if non_dict_data is False:
        ax.legend()


    return ax





