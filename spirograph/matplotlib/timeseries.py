
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import warnings
import pandas as pd

# To add
#  language
#  logo
# FIX label used twice
# show percentiles?
# ylabel at end of line rather than legend
#special term in use_attrs to use dict key
#change fill_between() edgecolor to the background color

def line_ts(data, ax=None, use_attrs=None, sub_kw=None, line_kw=None, legend='lines'):
    """
    Plots time series from 1D dataframe or dataset
    Args:
        data: dictionary of labeled Xarray DataArrays or Datasets
        ax: user-specified matplotlib axis
        use_attrs: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw: matplotlib or xarray line kwargs
        legend: 'full' (lines and shading), 'lines' (lines only), 'none' (no legend)
    Returns:
        matplotlib axis
    """

    # if only one data input, insert in dict
    non_dict_data = False

    if type(data) != dict:
        data = {'data_1': data}
        line_kw = {'data_1': empty_dict(line_kw)}
        non_dict_data = True

    # basic checks
    ## type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError('data must contain Xarray-type objects')

    ## 'time' dimension and calendar format
    data = check_timeindex(data)


    # set default kwargs
    plot_attrs = {'title': 'long_name',
                  'xlabel': 'time',
                  'ylabel': 'standard_name',
                  'yunits': 'units'}

    plot_sub_kw = {}

    if non_dict_data is True:
        plot_line_kw = {}
    else:
        plot_line_kw = {name: {} for name in data.keys()}

    # add/replace default kwargs with user inputs
    for user_dict, attr_dict in zip([use_attrs, sub_kw, line_kw],
                                    [plot_attrs, plot_sub_kw, plot_line_kw]):
        if user_dict:
            for k, v in user_dict.items():
                attr_dict[k] = v

    kwargs = {'sub_kw': plot_sub_kw, 'line_kw': plot_line_kw}

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    # build dictionary of array 'categories', which determine how to plot data
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # get data and plot
    lines_dict = {}

    for name, arr in data.items():

        # ensembles
        if array_categ[name] in ['PCT_VAR_ENS', 'STATS_VAR_ENS', 'PCT_DIM_ENS_DA']:

            # extract each array from the datasets
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
            lines_dict[name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                             array_data[sorted_lines['middle']].values, **kwargs['line_kw'][name], label=name)

            ax.fill_between(array_data[sorted_lines['lower']]['time'],
                            array_data[sorted_lines['lower']].values,
                            array_data[sorted_lines['upper']].values,
                            color=lines_dict[name][0].get_color(),
                            edgecolor='white', alpha=0.2)

            if legend == 'full':
                patch = Patch(facecolor=lines_dict[name][0].get_color(),
                              edgecolor='white', alpha=0.2,
                              label="{} - {}".format(sorted_lines['lower'],
                                                     sorted_lines['upper']))


        #  non-ensemble Datasets
        elif array_categ[name] in ['NON_ENS_DS']:
            for k, sub_arr in arr.data_vars.items():
                sub_name = name + "_" + sub_arr.name  # creates plot label
                lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values,
                                          **kwargs['line_kw'][name], label=sub_name
                                          )

        #  non-ensemble DataArrays
        else:
            lines_dict[name] = ax.plot(arr['time'], arr.values,
                                  **kwargs['line_kw'][name], label=name
                                  )

    #  add/modify plot elements according to the first entry.
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    #  other plot elements

    if non_dict_data is False and legend is not None:
        if legend == 'full':
            handles = [v[0] for v in list(lines_dict.values())] # line objects are tuples(?)
            handles.append(patch)
            ax.legend(handles=handles)
        else:
            ax.legend()

    ax.margins(x=0, y=0.05)

    return ax





