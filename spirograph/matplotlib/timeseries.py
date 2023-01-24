
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd


# To add
#   language
#   logo
#   xlim
# assumer que 'time' est la dimension, et fct qui regarde
# variables superflues?
# FIX when PCT_DIM_ENS, label for each line


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

    # if only one data input, insert in dict
    non_dict_data = False
    if type(data) != dict:
        data = {'data': data}
        non_dict_data = True

    # set default kwargs and add/replace with user inputs, if provided
    plot_attrs = {'title': 'long_name',
                  'xlabel': 'time',
                  'ylabel': 'standard_name',
                  'yunits': 'units'}
    plot_sub_kw = {}
    plot_line_kw = { name: {} for name in data.keys() }

    for user_dict, attr_dict in zip([use_attrs, sub_kw, line_kw], [plot_attrs, plot_sub_kw, plot_line_kw]):
        if user_dict:
            for k,v in user_dict.items():
                attr_dict[k] = v


    kwargs = {'sub_kw': plot_sub_kw, 'line_kw': plot_line_kw}

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])


    # build dictionary of array 'categories', which determine how to plot (see get_array_categ fct)
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # get data to plot

    for name, arr in data.items():

        if array_categ[name] in ['PCT_VAR_ENS', 'STATS_VAR_ENS', 'PCT_DIM_ENS']:

            # extract each line from the datasets
            array_data = {}
            if array_categ[name] == 'PCT_DIM_ENS':
                for pct in arr.percentiles:
                    array_data[pct] = arr.sel(percentiles=int(pct))
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
                    ax.plot(sub_arr['time'], sub_arr.values, **kwargs['line_kw'][name], label = sub_name)


        else: # should be DataArray

            ax.plot(arr['time'], arr.values, **kwargs['line_kw'][name], label = name)

    #add/modify plot elements according to the first entry
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    if non_dict_data is False:
        ax.legend()


    return ax

# test

## simple DataArray, labeled or unlabeled
line_ts(da_pct, line_kw = {'color': 'red'})
line_ts({'My data': da_pct})

## simple Dataset ensemble (variables)
line_ts(ds_pct, use_attrs= {'title': 'ccdp_name'})
line_ts({'My other data':ds_pct}, use_attrs= {'title': 'ccdp_name'})

## simple Dataset ensemble (pct)
line_ts(datest)
line_ts({'My random data': datest})

## all together
line_ts({'DataArray':da_pct, 'Var Ensemble': ds_pct, 'other': datest},
        line_kw = {'DataArray':{'color': 'purple'}, 'Var Ensemble': {'color': 'brown'}})




