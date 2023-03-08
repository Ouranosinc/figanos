import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import warnings

from spirograph.matplotlib.utils import *


def _plot_realizations(ax, da, name, plot_kw, non_dict_data):
    """ Plot realizations from a DataArray, inside or outside a Dataset.

    Parameters
    _________
    da: DataArray
        The DataArray containing the realizations.
    name: str
        The label to be used in the first part of a composite label.
        Can be the name of the parent Dataset or that of the DataArray.
    plot_kw: dict
        Dictionary of kwargs coming from the timeseries() input.
    ax: matplotlib axis
        The Matplotlib axis.

    Returns
    _______
    Matplotlib axis
    """
    ignore_label = False

    for r in da.realization.values:

        if plot_kw[name]:  # if kwargs (all lines identical)
            if not ignore_label:  # if label not already in legend
                label = '' if non_dict_data is True else name
                ignore_label = True
            else:
                label = ''
        else:
            label = str(r) if non_dict_data is True else (name + '_' + str(r))

        ax.plot(da.sel(realization=r)['time'], da.sel(realization=r).values,
                label=label, **plot_kw[name])

    return ax



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
        Default value is {'title': 'description', 'ylabel': 'long_name', 'yunits': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw: dict
        Arguments to pass to `plt.subplots()`. Only works if `ax` is not provided.
    plot_kw: dict
        Arguments to pass to the `plot()` function. Changes how the line looks.
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

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # if only one data input, insert in dict.
    non_dict_data = False
    if type(data) != dict:
        non_dict_data = True
        data = {'_no_label': data}  # mpl excludes labels starting with "_" from legend
        plot_kw = {'_no_label': empty_dict(plot_kw)}

    # assign keys to plot_kw if empty
    if len(plot_kw) == 0:
        for name, arr in data.items():
            plot_kw[name] = {}
    else:
        for name, arr in data.items():
            if name not in plot_kw:
                raise Exception('plot_kw must be a nested dictionary with keys corresponding to the keys in "data"')

    # check: type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError('`data` must contain a xr.Dataset, a xr.DataArray or a dictionary of xr.Dataset/ xr.DataArray.')

    # check: 'time' dimension and calendar format
    data = check_timeindex(data)

    # set default use_attrs values
    use_attrs.setdefault('title', 'description')
    use_attrs.setdefault('ylabel', 'long_name')
    use_attrs.setdefault('yunits', 'units')

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**fig_kw)

    # dict of array 'categories'
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    lines_dict = {}  # created to facilitate accessing line properties later

    # get data and plot
    for name, arr in data.items():

        #  remove 'label' to avoid error due to double 'label' args
        if 'label' in plot_kw[name]:
            del plot_kw[name]['label']
            warnings.warn('"label" entry in plot_kw[{}] will be ignored.'.format(name))


        if array_categ[name] == "ENS_REALS_DA":
            _plot_realizations(ax, arr, name, plot_kw, non_dict_data)

        elif array_categ[name] == "ENS_REALS_DS":
            if len(arr.data_vars) >= 2:
                raise Exception('To plot multiple ensembles containing realizations, use DataArrays outside a Dataset')
            for k, sub_arr in arr.data_vars.items():
                _plot_realizations(ax, sub_arr, name, plot_kw, non_dict_data)

        elif array_categ[name] == 'ENS_PCT_DIM_DS':
            for k, sub_arr in arr.data_vars.items():

                sub_name = sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)

                # extract each percentile array from the dims
                array_data = {}
                for pct in sub_arr.percentiles.values:
                    array_data[str(pct)] = sub_arr.sel(percentiles=pct)

                # create a dictionary labeling the middle, upper and lower line
                sorted_lines = sort_lines(array_data)

                # plot
                lines_dict[sub_name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                                               array_data[sorted_lines['middle']].values,
                                               label=sub_name, **plot_kw[name])

                ax.fill_between(array_data[sorted_lines['lower']]['time'],
                                array_data[sorted_lines['lower']].values,
                                array_data[sorted_lines['upper']].values,
                                color=lines_dict[sub_name][0].get_color(),
                                linewidth=0.0, alpha=0.2,
                                label=fill_between_label(sorted_lines, name, array_categ, legend))


        # other ensembles
        elif array_categ[name] in ['ENS_PCT_VAR_DS', 'ENS_STATS_VAR_DS', 'ENS_PCT_DIM_DA']:

            # extract each array from the datasets
            array_data = {}
            if array_categ[name] == 'ENS_PCT_DIM_DA':
                for pct in arr.percentiles:
                    array_data[str(int(pct))] = arr.sel(percentiles=int(pct))
            else:
                for k, v in arr.data_vars.items():
                    array_data[k] = v

            # create a dictionary labeling the middle, upper and lower line
            sorted_lines = sort_lines(array_data)

            # plot
            lines_dict[name] = ax.plot(array_data[sorted_lines['middle']]['time'],
                                       array_data[sorted_lines['middle']].values,
                                       label=name, **plot_kw[name])

            ax.fill_between(array_data[sorted_lines['lower']]['time'],
                            array_data[sorted_lines['lower']].values,
                            array_data[sorted_lines['upper']].values,
                            color=lines_dict[name][0].get_color(),
                            linewidth=0.0, alpha=0.2,
                            label=fill_between_label(sorted_lines, name, array_categ, legend))


        #  non-ensemble Datasets
        elif array_categ[name] == "DS":

            ignore_label = False
            for k, sub_arr in arr.data_vars.items():

                sub_name = sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)

                #  if kwargs are specified by user, all lines are the same and we want one legend entry
                if plot_kw[name]:
                    label = name if not ignore_label else ''
                    ignore_label = True
                else:
                    label = sub_name

                lines_dict[sub_name] = ax.plot(sub_arr['time'], sub_arr.values, label=label, **plot_kw[name])


        #  non-ensemble DataArrays
        elif array_categ[name] in ['DA']:
            lines_dict[name] = ax.plot(arr['time'], arr.values, label=name, **plot_kw[name])

        else:
            raise Exception('Data structure not supported')  # can probably be removed along with elif logic above,
                                                             # given that get_array_categ() checks also



    #  add/modify plot elements according to the first entry.
    set_plot_attrs(use_attrs, list(data.values())[0], ax)
    ax.set_xlabel('time')  # check_timeindex() already checks for 'time'

    # other plot elements (will be replaced by Stylesheet)

    ax.margins(x=0, y=0.05)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if show_lat_lon:
        plot_coords(ax, list(data.values())[0], type='location')

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



def gridmap(data, ax=None, use_attrs=None, fig_kw=None, plot_kw=None, projection=ccrs.LambertConformal(),transform=None,
            features=None, contourf=False, cmap=None, levels=None, divergent=False, show_time=False, frame=False):
    """ Create map from 2D data.

    Parameters
    ________
    data: dict, DataArray or Dataset
        Input data do plot. If dictionary, must have only one entry.
    ax: matplotlib axis
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs: dict
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'cbar_label': 'long_name', 'cbar_units': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw: dict
        Arguments to pass to `plt.figure()`.
    plot_kw: dict
        Arguments to pass to the `xarray.plot.pcolormesh()` or 'xarray.plot.contourf()' function.
        If 'data' is a dictionary, can be a nested dictionary with the same keys as 'data'.
    projection: ccrs projection
        Projection to use, taken from the cartopy.crs options. Ignored if ax is not None.
    features: list
        List of features to use. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers'].
    contourf: bool
        By default False, use plt.pcolormesh(). If True, use plt.contourf().
    cmap: colormap or str
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/varaibles_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding colormap, aligned with the IPCC visual style guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    levels: int
        Levels to use to divide the colormap. Acceptable values are from 2 to 21, inclusive.
    divergent: bool or int or float
        If int or float, becomes center of cmap.
    show_time:bool
        Show time (as date) at bottom right of plot.
    frame: bool
        Show or hide frame. Default False.

    Returns
    _______
        matplotlib axis
    """

    # checks
    if levels:
        if type(levels) != int or levels < 2 or levels > 21:
            raise Exception('levels must be int between 2 and 21, inclusively. To pass a list, use plot_kw={"levels":list()}.')

    #create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # set default use_attrs values
    use_attrs.setdefault('title', 'description')
    use_attrs.setdefault('cbar_label', 'long_name')
    use_attrs.setdefault('cbar_units', 'units')

    # extract plot_kw from dict if needed
    if isinstance(data, dict) and plot_kw and list(data.keys())[0] in plot_kw.keys():
        plot_kw = plot_kw[list(data.keys())[0]]

    # if data is dict, extract
    if isinstance(data, dict):
        if len(data) == 1:
            data = list(data.values())[0]
        else:
            raise Exception('`data` must be a dict of len=1, a DataArray or a Dataset')

    # select data to plot
    if isinstance(data, xr.DataArray):
        plot_data = data
    elif isinstance(data, xr.Dataset):
        warnings.warn('data is xr.Dataset; only the first variable will be used in plot')
        plot_data = data[list(data.keys())[0]]
    else:
        raise TypeError('`data` must contain a xr.DataArray or xr.Dataset')

    # setup transform
    if transform is None:
        if 'lat' in data.dims and 'lon' in data.dims:
            transform = ccrs.PlateCarree()
        elif 'rlat' in data.dims and 'rlon' in data.dims:
            if hasattr(data, 'rotated_pole'):
                transform = get_rotpole(data)

    # setup fig, ax
    if not ax:
        fig, ax = plt.subplots(subplot_kw={'projection': projection}, **fig_kw)

    #create cbar label
    if 'cbar_units' in use_attrs and len(get_attributes(use_attrs['cbar_units'], data)) >= 1:  # avoids '[]' as label
        cbar_label = get_attributes(use_attrs['cbar_label'], data) + ' (' + \
                     get_attributes(use_attrs['cbar_units'], data) + ')'
    else:
        cbar_label = get_attributes(use_attrs['cbar_label'], data)

    #colormap
    if type(cmap) == str:
        if cmap not in plt.colormaps():
            try:
                cmap = create_cmap(levels=levels, filename=cmap)
            except FileNotFoundError:
                pass

    elif cmap is None:
        cdata = Path(__file__).parents[1] / 'data/ipcc_colors/variable_groups.json'
        cmap = create_cmap(get_var_group(plot_data, path_to_json=cdata), levels=levels, divergent=divergent)

    # set defaults
    if divergent is not False:
        if type(divergent) in [int, float]:
            plot_kw.setdefault('center', divergent)
        else:
            plot_kw.setdefault('center', 0)

    plot_kw.setdefault('cbar_kwargs', {})
    plot_kw['cbar_kwargs'].setdefault('label', wrap_text(cbar_label))

    #plot
    if contourf is False:
        pl = plot_data.plot.pcolormesh(ax=ax, transform=transform, cmap=cmap, **plot_kw)

    else:
        plot_kw.setdefault('levels', levels)
        pl = plot_data.plot.contourf(ax=ax, transform=transform, cmap=cmap, **plot_kw)

    #add features
    if features:
        for f in features:
            ax.add_feature(getattr(cfeature, f.upper()))

    if show_time is True:
        plot_coords(ax, plot_data, type='time')

    # remove some labels to avoid overcrowding, when levels are used with pcolormesh
    if contourf is False and levels is not None:
        pl.colorbar.ax.set_yticks(cbar_ticks(pl, levels))

    set_plot_attrs(use_attrs, data, ax)

    if frame is False:
        ax.spines['geo'].set_visible(False)

    return ax
