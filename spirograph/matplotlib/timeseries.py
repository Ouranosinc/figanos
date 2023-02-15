import xarray as xr
import matplotlib.pyplot as plt
from spirograph.matplotlib.util_fcts import empty_dict, check_timeindex, get_array_categ, \
    sort_lines, get_suffix, set_plot_attrs, split_legend, plot_lat_lon

# Todo: translation to fr, logo

def timeseries(data, ax=None, use_attrs=None, fig_kw=None, plot_kw=None, legend='lines', show_lat_lon = True):
    """
    Plot time series from 1D Xarray Datasets or DataArrays as line plots.

    Parameters
    __________
    data: dict or Dataset/DataArray
        Input data to plot. It can be a DataArray, Dataset or a dictionary of DataArrays and/or Datasets.
    ax: matplotlib axis
        Matplotlib axis on which to plot.
    use_attrs: dict
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'long_name', 'ylabel': 'standard_name', 'yunits': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw: dict
        Arguments to pass to `plt.subplots()`. Only works if `ax` is not provided.
    plot_kw: dict
        Arguments to pass the `plot()` function. Changes how the line looks.
        If 'data' is a dictionary, must be a nested dictionary with the same keys as 'data'.
    legend: str (default 'lines')
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines),
         'edge' (out of plot), 'none' (no legend).
    show_lat_lon: bool (default True)
        If True, show latitude and longitude coordinates at the bottom right of the figure.
    Returns
    _______
        matplotlib axis
    """

    #create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # if only one data input, insert in dict.
    non_dict_data = False
    if type(data) != dict:
        non_dict_data = True
        data = {'_no_label': data}  # mpl excludes labels starting with "_" from legend
        plot_kw = {'_no_label': empty_dict(plot_kw)}

    #assign keys to plot_kw if empty
    if len(plot_kw) == 0:
        for name, arr in data.items():
            plot_kw[name] = {}
    else:
        for name, arr in data.items():
            if name not in plot_kw:
                raise Exception('plot_kw must be a nested dictionary with keys corresponding to the keys in "data"')

    # basic checks
    ## type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError('`data` must contain a xr.Dataset, a xr.DataArray or a dictionary of xr.Dataset/ xr.DataArray.')

    ## 'time' dimension and calendar format
    data = check_timeindex(data)


    # set default use_attrs values
    use_attrs.setdefault('title', 'long_name')
    use_attrs.setdefault('ylabel', 'standard_name')
    use_attrs.setdefault('yunits', 'units')



    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**fig_kw)

    # build dictionary of array 'categories', which determine how to plot data
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # get data and plot
    lines_dict = {}  # created to facilitate accessing line properties later

    for name, arr in data.items():

        #  add 'label':name in ax.plot() kwargs if not there, to avoid error due to double 'label' args
        plot_kw[name].setdefault('label', name)


        # Dataset containing percentile ensembles
        if array_categ[name] == 'PCT_DIM_ENS_DS':
            for k, sub_arr in arr.data_vars.items():
                if non_dict_data is True:
                    sub_name = sub_arr.name
                else:
                    sub_name = plot_kw[name]['label'] + "_" + sub_arr.name

                # extract each percentile array from the dims
                array_data = {}
                for pct in sub_arr.percentiles:
                    array_data[str(int(pct))] = sub_arr.sel(percentiles=int(pct))

                # create a dictionary labeling the middle, upper and lower line
                sorted_lines = sort_lines(array_data)

                # plot line while temporary changing label to sub_name
                store_label = plot_kw[name]['label']
                plot_kw[name]['label'] = sub_name

                lines_dict[sub_name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                                           array_data[sorted_lines['middle']].values,
                                           **plot_kw[name])

                plot_kw[name]['label'] = store_label

                # plot shading
                fill_between_label = "{}th-{}th percentiles".format(get_suffix(sorted_lines['lower']),
                                                                    get_suffix(sorted_lines['upper']))

                if legend != 'full':
                    fill_between_label = None

                ax.fill_between(array_data[sorted_lines['lower']]['time'],
                                array_data[sorted_lines['lower']].values,
                                array_data[sorted_lines['upper']].values,
                                color=lines_dict[sub_name][0].get_color(),
                                linewidth=0.0, alpha=0.2, label=fill_between_label)




        # other ensembles
        elif array_categ[name] in ['PCT_VAR_ENS', 'STATS_VAR_ENS', 'PCT_DIM_ENS_DA']:

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

            # plot line
            lines_dict[name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                                       array_data[sorted_lines['middle']].values,
                                       **plot_kw[name])

            # plot shading
            if array_categ[name] in ['PCT_VAR_ENS', 'PCT_DIM_ENS_DA']:
                fill_between_label = "{}th-{}th percentiles".format(get_suffix(sorted_lines['lower']),
                                                                    get_suffix(sorted_lines['upper']))
            if array_categ[name] in ['STATS_VAR_ENS']:
                fill_between_label = "min-max range"
            if legend != 'full':
                fill_between_label = None

            ax.fill_between(array_data[sorted_lines['lower']]['time'],
                            array_data[sorted_lines['lower']].values,
                            array_data[sorted_lines['upper']].values,
                            color=lines_dict[name][0].get_color(),
                            linewidth=0.0, alpha=0.2, label=fill_between_label)


        #  non-ensemble Datasets
        elif array_categ[name] in ['DS']:
            for k, sub_arr in arr.data_vars.items():
                if non_dict_data is True:
                    sub_name = sub_arr.name
                else:
                    sub_name = plot_kw[name]['label'] + "_" + sub_arr.name

                #label will be modified, so store now and put back later
                store_label = plot_kw[name]['label']

                #  if kwargs are specified by user, all lines are the same and we want one legend entry
                if len(plot_kw[name]) >= 2:  # 'label' is there by default
                    lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values, **plot_kw[name])
                    plot_kw[name]['label'] = '' #  makes sure label only appears once
                else:
                    plot_kw[name]['label'] = sub_name
                    lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values, **plot_kw[name])
                    plot_kw[name]['label'] = store_label


        #  non-ensemble DataArrays
        elif array_categ[name] in ['DA']:
            lines_dict[name] = ax.plot(arr['time'], arr.values, **plot_kw[name])

        else:
            raise Exception('Data structure not supported')  # can probably be removed along with elif logic above,
                                                             # given that get_array_categ() checks also



    #  add/modify plot elements according to the first entry.
    set_plot_attrs(use_attrs, list(data.values())[0], ax)

    # other plot elements (will be replaced by Stylesheet)

    ax.margins(x=0, y=0.05)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if show_lat_lon:
        plot_lat_lon(ax, list(data.values())[0])

    if legend is not None:
        if not ax.get_legend_handles_labels()[0]: # check if legend is empty
            pass
        elif legend == 'in_plot':
            split_legend(ax, in_plot=True)
        elif legend == 'edge':
            split_legend(ax, in_plot=False)
        else:
            ax.legend()

    return ax
