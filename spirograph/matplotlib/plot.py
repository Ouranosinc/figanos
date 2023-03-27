from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import cartopy.feature as cfeature  # noqa
import matplotlib.axes
import matplotlib.colors
import matplotlib.pyplot as plt
import xarray as xr
from cartopy import crs as ccrs

from spirograph.matplotlib.utils import (
    cbar_ticks,
    check_timeindex,
    convert_scen_name,
    create_cmap,
    empty_dict,
    fill_between_label,
    get_array_categ,
    get_attributes,
    get_rotpole,
    get_scen_color,
    get_var_group,
    gpd_to_ccrs,
    plot_coords,
    process_keys,
    set_plot_attrs,
    sort_lines,
    split_legend,
    wrap_text,
)


def _plot_realizations(
    ax: matplotlib.axes.Axes,
    da: xr.DataArray,
    name: str,
    plot_kw: dict[str, Any],
    non_dict_data: dict[str, Any],
) -> matplotlib.axes.Axes:
    """Plot realizations from a DataArray, inside or outside a Dataset.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        The Matplotlib axis object.
    da: DataArray
        The DataArray containing the realizations.
    name: str
        The label to be used in the first part of a composite label.
        Can be the name of the parent Dataset or that of the DataArray.
    plot_kw: dict
        Dictionary of kwargs coming from the timeseries() input.

    Returns
    -------
    matplotlib.axes.Axes
    """
    ignore_label = False

    for r in da.realization.values:
        if plot_kw[name]:  # if kwargs (all lines identical)
            if not ignore_label:  # if label not already in legend
                label = "" if non_dict_data is True else name
                ignore_label = True
            else:
                label = ""
        else:
            label = str(r) if non_dict_data is True else (name + "_" + str(r))

        ax.plot(
            da.sel(realization=r)["time"],
            da.sel(realization=r).values,
            label=label,
            **plot_kw[name],
        )

    return ax


def timeseries(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes = None,
    use_attrs: dict[str, Any] = None,
    fig_kw: dict[str, Any] = None,
    plot_kw: dict[str, Any] = None,
    legend: str = "lines",
    show_lat_lon: bool = True,
) -> matplotlib.axes.Axes:
    """Plot time series from 1D Xarray Datasets or DataArrays as line plots.

    Parameters
    ----------
    data: dict or Dataset/DataArray
        Input data to plot. It can be a DataArray, Dataset or a dictionary of DataArrays and/or Datasets.
    ax: matplotlib.axes.Axes
        Matplotlib axis on which to plot.
    use_attrs: dict
        A dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
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
    -------
    matplotlib.axes.Axes
        matplotlib axis object.
    """
    # convert SSP, RCP, CMIP formats in keys
    if type(data) == dict:
        data = process_keys(data, convert_scen_name)
    if type(plot_kw) == dict:
        plot_kw = process_keys(plot_kw, convert_scen_name)

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # if only one data input, insert in dict.
    non_dict_data = False
    if type(data) != dict:
        non_dict_data = True
        data = {"_no_label": data}  # mpl excludes labels starting with "_" from legend
        plot_kw = {"_no_label": empty_dict(plot_kw)}

    # assign keys to plot_kw if not there
    if non_dict_data is False:
        for name in data:
            if name not in plot_kw:
                plot_kw[name] = {}
        for key in plot_kw:
            if key not in data:
                raise Exception(
                    'plot_kw must be a nested dictionary with keys corresponding to the keys in "data"'
                )

    # check: type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError(
                '"data" must contain a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
            )

    # check: 'time' dimension and calendar format
    data = check_timeindex(data)

    # set default use_attrs values
    use_attrs.setdefault("title", "description")
    use_attrs.setdefault("ylabel", "long_name")
    use_attrs.setdefault("yunits", "units")

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**fig_kw)

    # dict of array 'categories'
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    lines_dict = {}  # created to facilitate accessing line properties later

    # get data and plot
    for name, arr in data.items():
        # look for SSP, RCP, CMIP color
        cat_colors = (
            Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
        )
        if get_scen_color(name, cat_colors):
            plot_kw[name].setdefault("color", get_scen_color(name, cat_colors))

        #  remove 'label' to avoid error due to double 'label' args
        if "label" in plot_kw[name]:
            del plot_kw[name]["label"]
            warnings.warn(f'"label" entry in plot_kw[{name}] will be ignored.')

        if array_categ[name] == "ENS_REALS_DA":
            _plot_realizations(ax, arr, name, plot_kw, non_dict_data)

        elif array_categ[name] == "ENS_REALS_DS":
            if len(arr.data_vars) >= 2:
                raise Exception(
                    "To plot multiple ensembles containing realizations, use DataArrays outside a Dataset"
                )
            for k, sub_arr in arr.data_vars.items():
                _plot_realizations(ax, sub_arr, name, plot_kw, non_dict_data)

        elif array_categ[name] == "ENS_PCT_DIM_DS":
            for k, sub_arr in arr.data_vars.items():
                sub_name = (
                    sub_arr.name
                    if non_dict_data is True
                    else (name + "_" + sub_arr.name)
                )

                # extract each percentile array from the dims
                array_data = {}
                for pct in sub_arr.percentiles.values:
                    array_data[str(pct)] = sub_arr.sel(percentiles=pct)

                # create a dictionary labeling the middle, upper and lower line
                sorted_lines = sort_lines(array_data)

                # plot
                lines_dict[sub_name] = ax.plot(
                    array_data[sorted_lines["middle"]]["time"],
                    array_data[sorted_lines["middle"]].values,
                    label=sub_name,
                    **plot_kw[name],
                )

                ax.fill_between(
                    array_data[sorted_lines["lower"]]["time"],
                    array_data[sorted_lines["lower"]].values,
                    array_data[sorted_lines["upper"]].values,
                    color=lines_dict[sub_name][0].get_color(),
                    linewidth=0.0,
                    alpha=0.2,
                    label=fill_between_label(sorted_lines, name, array_categ, legend),
                )

        # other ensembles
        elif array_categ[name] in [
            "ENS_PCT_VAR_DS",
            "ENS_STATS_VAR_DS",
            "ENS_PCT_DIM_DA",
        ]:
            # extract each array from the datasets
            array_data = {}
            if array_categ[name] == "ENS_PCT_DIM_DA":
                for pct in arr.percentiles:
                    array_data[str(int(pct))] = arr.sel(percentiles=int(pct))
            else:
                for k, v in arr.data_vars.items():
                    array_data[k] = v

            # create a dictionary labeling the middle, upper and lower line
            sorted_lines = sort_lines(array_data)

            # plot
            lines_dict[name] = ax.plot(
                array_data[sorted_lines["middle"]]["time"],
                array_data[sorted_lines["middle"]].values,
                label=name,
                **plot_kw[name],
            )

            ax.fill_between(
                array_data[sorted_lines["lower"]]["time"],
                array_data[sorted_lines["lower"]].values,
                array_data[sorted_lines["upper"]].values,
                color=lines_dict[name][0].get_color(),
                linewidth=0.0,
                alpha=0.2,
                label=fill_between_label(sorted_lines, name, array_categ, legend),
            )

        #  non-ensemble Datasets
        elif array_categ[name] == "DS":
            ignore_label = False
            for k, sub_arr in arr.data_vars.items():
                sub_name = (
                    sub_arr.name
                    if non_dict_data is True
                    else (name + "_" + sub_arr.name)
                )

                #  if kwargs are specified by user, all lines are the same and we want one legend entry
                if plot_kw[name]:
                    label = name if not ignore_label else ""
                    ignore_label = True
                else:
                    label = sub_name

                lines_dict[sub_name] = ax.plot(
                    sub_arr["time"], sub_arr.values, label=label, **plot_kw[name]
                )

        #  non-ensemble DataArrays
        elif array_categ[name] in ["DA"]:
            lines_dict[name] = ax.plot(
                arr["time"], arr.values, label=name, **plot_kw[name]
            )

        else:
            raise Exception(
                "Data structure not supported"
            )  # can probably be removed along with elif logic above,
            # given that get_array_categ() checks also

    #  add/modify plot elements according to the first entry.
    set_plot_attrs(use_attrs, list(data.values())[0], ax)
    ax.set_xlabel("time")  # check_timeindex() already checks for 'time'

    # other plot elements
    if show_lat_lon:
        plot_coords(ax, list(data.values())[0], param="location", backgroundalpha=1)

    if legend is not None:
        if not ax.get_legend_handles_labels()[0]:  # check if legend is empty
            pass
        elif legend == "in_plot":
            split_legend(ax, in_plot=True)
        elif legend == "edge":
            split_legend(ax, in_plot=False)
        else:
            ax.legend()

    return ax


def gridmap(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes = None,
    use_attrs: dict[str, Any] = None,
    fig_kw: dict[str, Any] = None,
    plot_kw: dict[str, Any] = None,
    projection: ccrs.Projection = ccrs.LambertConformal(),
    transform: ccrs.Projection = None,
    features: list | dict[str, Any] = None,
    geometries_kw: dict[str, Any] = None,
    contourf: bool = False,
    cmap: str | matplotlib.colors.Colormap = None,
    levels: int = None,
    divergent: bool | int | float = False,
    show_time: bool = False,
    frame: bool = False,
) -> matplotlib.axes.Axes:
    """Create map from 2D data.

    Parameters
    ----------
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
    transform: ccrs transform
        Transform corresponding to the data coordinate system. If None, an attempt is made to find dimensions matching
        ccrs.PlateCarree() or ccrs.RotatedPole().
    features: list or dict
        Features to use, as a list or a nested dict containing kwargs. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers'].
    geometries_kw : dict
        Arguments passed to cartopy ax.add_geometry() which adds given geometries (GeoDataFrame geometry) to axis.
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
        If int or float, becomes center of cmap. Default center is 0.
    show_time:bool
        Show time (as date) at bottom right of plot.
    frame: bool
        Show or hide frame. Default False.

    Returns
    -------
        matplotlib axis
    """

    # checks
    if levels:
        if type(levels) != int or levels < 2 or levels > 21:
            raise Exception(
                'levels must be int between 2 and 21, inclusively. To pass a list, use plot_kw={"levels":list()}.'
            )

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # set default use_attrs values
    use_attrs.setdefault("title", "description")
    use_attrs.setdefault("cbar_label", "long_name")
    use_attrs.setdefault("cbar_units", "units")

    # extract plot_kw from dict if needed
    if isinstance(data, dict) and plot_kw and list(data.keys())[0] in plot_kw.keys():
        plot_kw = plot_kw[list(data.keys())[0]]

    # if data is dict, extract
    if isinstance(data, dict):
        if len(data) == 1:
            data = list(data.values())[0]
        else:
            raise Exception("`data` must be a dict of len=1, a DataArray or a Dataset")

    # select data to plot
    if isinstance(data, xr.DataArray):
        plot_data = data
    elif isinstance(data, xr.Dataset):
        warnings.warn(
            "data is xr.Dataset; only the first variable will be used in plot"
        )
        plot_data = data[list(data.keys())[0]]
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    # setup transform
    if transform is None:
        if "lat" in data.dims and "lon" in data.dims:
            transform = ccrs.PlateCarree()
        elif "rlat" in data.dims and "rlon" in data.dims:
            if hasattr(data, "rotated_pole"):
                transform = get_rotpole(data)

    # setup fig, ax
    if not ax:
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)

    # create cbar label
    if (
        "cbar_units" in use_attrs
        and len(get_attributes(use_attrs["cbar_units"], data)) >= 1
    ):  # avoids '[]' as label
        cbar_label = (
            get_attributes(use_attrs["cbar_label"], data)
            + " ("
            + get_attributes(use_attrs["cbar_units"], data)
            + ")"
        )
    else:
        cbar_label = get_attributes(use_attrs["cbar_label"], data)

    # colormap
    if type(cmap) == str:
        if cmap not in plt.colormaps():
            try:
                cmap = create_cmap(levels=levels, filename=cmap)
            except FileNotFoundError:
                pass

    elif cmap is None:
        cdata = Path(__file__).parents[1] / "data/ipcc_colors/variable_groups.json"
        cmap = create_cmap(
            get_var_group(plot_data, path_to_json=cdata),
            levels=levels,
            divergent=divergent,
        )

    # set defaults
    if divergent is not False:
        if type(divergent) in [int, float]:
            plot_kw.setdefault("center", divergent)
        else:
            plot_kw.setdefault("center", 0)

    if "add_colorbar" not in plot_kw or plot_kw["add_colorbar"] is not False:
        plot_kw.setdefault("cbar_kwargs", {})
        plot_kw["cbar_kwargs"].setdefault("label", wrap_text(cbar_label))

    # plot
    if contourf is False:
        pl = plot_data.plot.pcolormesh(ax=ax, transform=transform, cmap=cmap, **plot_kw)

    else:
        plot_kw.setdefault("levels", levels)
        pl = plot_data.plot.contourf(ax=ax, transform=transform, cmap=cmap, **plot_kw)

    # add features
    if isinstance(features, list):
        for f in features:
            ax.add_feature(getattr(cfeature, f.upper()))
    if isinstance(features, dict):
        for f in features:
            ax.add_feature(getattr(cfeature, f.upper()), **features[f])

    if show_time is True:
        plot_coords(ax, plot_data, param="time", backgroundalpha=0)

    # remove some labels to avoid overcrowding, when levels are used with pcolormesh
    if contourf is False and levels is not None:
        pl.colorbar.ax.set_yticks(cbar_ticks(pl, levels))

    set_plot_attrs(use_attrs, data, ax)

    if frame is False:
        ax.spines["geo"].set_visible(False)

    # add geometries
    if geometries_kw:
        if "geoms" not in geometries_kw.keys():
            warnings.warn(
                'geoms missing from geometries_kw (ex: {"geoms": df["geometry"]})'
            )
        if "crs" in geometries_kw.keys():
            geometries_kw["geoms"] = gpd_to_ccrs(
                geometries_kw["geoms"], geometries_kw["crs"]
            )
        else:
            geometries_kw["geoms"] = gpd_to_ccrs(geometries_kw["geoms"], projection)
        geometries_kw = {
            "crs": projection,
            "facecolor": "none",
            "edgecolor": "black",
        } | geometries_kw

        ax.add_geometries(**geometries_kw)

    return ax
