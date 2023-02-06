import xarray as xr
import matplotlib.pyplot as plt

# To add
#  translation to fr
#  logo

def timeseries(data, ax=None, use_attrs=None, sub_kw=None, line_kw=None, legend='lines', show_coords = True):
    """
    Plots time series from 1D dataframes or datasets

    Parameters
    __________
    data: dict or Dataset/DataArray
        dictionary of labeled Xarray DataArrays or Datasets
    ax: matplotlib axis
        user-specified matplotlib axis
    use_attrs: dict
        dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description')
    sub_kw: dict
        matplotlib subplots kwargs in the format {'param': value}
    line_kw: dict
        matplotlib or xarray line kwargs in the format {'param': value}
    legend: str
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines),
         'edge' (out of plot), 'none' (no legend)
    show_coords: bool
        show latitude, longitude coordinates at the bottom right of the figure
    Returns
    _______
        matplotlib axis
    """

    # if only one data input, insert in dict
    non_dict_data = False

    if type(data) != dict:
        data = {'_no_label': data}  # mpl excludes labels starting with "_" from legend
        line_kw = {'_no_label': empty_dict(line_kw)}
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
    lines_dict = {}  # created to facilitate accessing line properties later

    for name, arr in data.items():

        #  add name in line kwargs if not there, to avoid error due to double 'label' args in plot()
        if 'label' not in kwargs['line_kw'][name]:
            kwargs['line_kw'][name]['label'] = name

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

            # plot line
            lines_dict[name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                                       array_data[sorted_lines['middle']].values,
                                       **kwargs['line_kw'][name])

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
                            linewidth = 0.0, alpha=0.2, label=fill_between_label)

        #  non-ensemble Datasets
        elif array_categ[name] in ['DS']:
            for k, sub_arr in arr.data_vars.items():
                if non_dict_data is True:
                    sub_name = sub_arr.name
                else:
                    sub_name = kwargs['line_kw'][name]['label'] + "_" + sub_arr.name

                #put sub_name in line_kwargs to label correctly on plot, store the
                # original, and put it back after
                store_label = kwargs['line_kw'][name]['label']
                kwargs['line_kw'][name]['label'] = sub_name
                lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values, **kwargs['line_kw'][name])
                kwargs['line_kw'][name]['label'] = store_label


        #  non-ensemble DataArrays
        elif array_categ[name] in ['DA']:
            lines_dict[name] = ax.plot(arr['time'], arr.values, **kwargs['line_kw'][name])

        else:
            raise Exception('Data structure not supported')

    #  add/modify plot elements according to the first entry.
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    # other plot elements (check overlap with Stylesheet!)

    ax.margins(x=0, y=0.05)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if show_coords:
        plot_coords(ax, list(data.values())[0])

    if legend is not None:  # non_dict_data is False and
        if legend == 'in_plot':
            split_legend(ax, out=False)
        elif legend == 'edge':
            split_legend(ax, out=True)
        else:
            ax.legend()

    return ax
