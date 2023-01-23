
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
# assumer que 'time' est la dimension, et fct qui regarde
# lorsque plusieurs datasets, prendre le 1er
# lorsque dataset n<est pas ensemble, label serait global_label_variable
# variables superflues?




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
    #set default kwargs and add/replace with user inputs, if provided
    plot_attrs = {'title': 'long_name',
                  'xlabel': 'time',
                  'ylabel': 'standard_name',
                  'yunits': 'units'}
    plot_sub_kw = {}
    plot_line_kw = {'label': 'name'}

    for user_dict, attr_dict in zip([use_attrs, sub_kw, line_kw], [plot_attrs, plot_sub_kw, plot_line_kw]):
        if user_dict:
            for k,v in user_dict.items():
                attr_dict[k] = v

    kwargs = {'sub_kw': plot_sub_kw, 'line_kw': plot_line_kw}

    #set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])


    #build dictionary of array 'categories', which determine how to plot (see get_array_categ fct)
    array_categ = {name: get_array_cat(array) for name, array in data.items()}

    #get data to plot

    for name, arr in data.items():
        if array_categ[name] in ['PCT_VAR_ENS', 'STATS_VAR_ENS', 'PCT_DIM_ENS']:

            array_data = {}

            if array_categ[name] == 'PCT_DIM_ENS':
                for pct in arr.percentiles:
                    pct_name = name + "_p" + str(int(pct)) #creates plot label
                    array_data[pct] = arr.sel(percentiles=int(pct))
            else:
                for k, v in arr.data_vars.items():
                    array_data[k] = v

            #create a dictionary labeling the middle, upper and lower line
            sorted_lines = sort_lines(array_data)


            #plot the ensemble
            line_1 = ax.plot(array_data[sorted_lines['middle']]['time'],
                             array_data[sorted_lines['middle']].values, **kwargs['line_kw'])

            ax.fill_between(array_data[sorted_lines['lower']]['time'],
                            array_data[sorted_lines['lower']].values,
                            array_data[sorted_lines['upper']].values,
                            color=line_1[0].get_color(),
                            edgecolor='white', alpha=0.2)



    # #plot
    # else:
    #     for name, arr in array_data.items():
    #         ax.plot(arr[arr.dims[0]], arr.values, label = name, **kwargs['line_kw'])

    #add/modify plot elements according to the first entry
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    ax.legend()


    return ax

#test

fig, ax = plt.subplots()
line_ts({'rcp2.5': dataset1, 'rcp8.5': dataset2}, ax = ax)
line_ts(line, ax = ax)


line_ts(da_pct, line_kw = {'color': 'red'})
line_ts(ds_pct, use_attrs= {'title': 'ccdp_name'})
line_ts(ds_pct, ensemble=True, line_kw={'color': 'red'})
line_ts({"BOURGEONNOISERIES":ds_pct})


mod_da_pct = da_pct + da_pct*0.05
fig, ax1 = plt.subplots()
line_ts(ds_pct, ensemble=True, ax = ax1)
line_ts(mod_da_pct, ax = ax1)
