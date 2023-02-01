
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# To add
#  translation to fr
#  logo
# FIX full legend when multiple ensembles
# ylabel at end of line rather than legend

def line_ts(data, ax=None, use_attrs=None, sub_kw=None, line_kw=None, legend='lines', show_coords = True):
    """
    Plots time series from 1D dataframe or dataset
    Args:
        data: dictionary of labeled Xarray DataArrays or Datasets
        ax: user-specified matplotlib axis
        use_attrs: dict linking a plot element (key, e.g. 'title')
            to a DataArray attribute (value, e.g. 'Description')
        sub_kw: matplotlib subplot kwargs
        line_kw: matplotlib or xarray line kwargs
        legend: 'full' (lines and shading), 'lines' (lines only),
                'in_plot' (self-expl.), 'none' (no legend)
    Returns:
        matplotlib axis
    """

    # if only one data input, insert in dict
    non_dict_data = False

    if type(data) != dict:
        data = {'no_label': data}
        line_kw = {'no_label': empty_dict(line_kw)}
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
        elif array_categ[name] in ['NON_ENS_DS']:
            for k, sub_arr in arr.data_vars.items():
                sub_name = kwargs['line_kw'][name]['label'] + "_" + sub_arr.name
                lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values,**kwargs['line_kw'][name])

        #  non-ensemble DataArrays
        else:
            lines_dict[name] = ax.plot(arr['time'], arr.values,**kwargs['line_kw'][name])

    #  add/modify plot elements according to the first entry.
    set_plot_attrs(plot_attrs, list(data.values())[0], ax)

    # other plot elements

    ax.margins(x=0, y=0.05)

    if show_coords:
        plot_coords(ax, list(data.values())[0])

    if non_dict_data is False and legend is not None:
        if legend == 'in_plot':
            in_plot_legend(ax)
        else:
            ax.legend()


    return ax





