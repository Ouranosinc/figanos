from __future__ import annotations

import math
import warnings
from pathlib import Path
from typing import Any

import cartopy.feature as cfeature  # noqa
import cartopy.mpl.geoaxes
import geopandas as gpd
import matplotlib
import matplotlib.axes
import matplotlib.cm
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xarray as xr
from cartopy import crs as ccrs
from matplotlib.cm import ScalarMappable

from spirograph.matplotlib.utils import (
    add_cartopy_features,
    cbar_ticks,
    check_timeindex,
    clean_cmap_bounds,
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
    ax : matplotlib.axes.Axes
        The Matplotlib axis object.
    da : DataArray
        The DataArray containing the realizations.
    name : str
        The label to be used in the first part of a composite label.
        Can be the name of the parent Dataset or that of the DataArray.
    plot_kw : dict
        Dictionary of kwargs coming from the timeseries() input.
    non_dict_data : dict
        TBD.

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
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    legend: str = "lines",
    show_lat_lon: bool = True,
) -> matplotlib.axes.Axes:
    """Plot time series from 1D Xarray Datasets or DataArrays as line plots.

    Parameters
    ----------
    data : dict or Dataset/DataArray
        Input data to plot. It can be a DataArray, Dataset or a dictionary of DataArrays and/or Datasets.
    ax : matplotlib.axes.Axes, optional
        Matplotlib axis on which to plot.
    use_attrs : dict, optional
        A dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'ylabel': 'long_name', 'yunits': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw : dict, optional
        Arguments to pass to `plt.subplots()`. Only works if `ax` is not provided.
    plot_kw : dict, optional
        Arguments to pass to the `plot()` function. Changes how the line looks.
        If 'data' is a dictionary, must be a nested dictionary with the same keys as 'data'.
    legend : str (default 'lines')
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines),
         'edge' (out of plot), 'none' (no legend).
    show_lat_lon : bool (default True)
        If True, show latitude and longitude coordinates at the bottom right of the figure.

    Returns
    -------
    matplotlib.axes.Axes
    """
    # convert SSP, RCP, CMIP formats in keys
    if isinstance(data, dict):
        data = process_keys(data, convert_scen_name)
    if isinstance(plot_kw, dict):
        plot_kw = process_keys(plot_kw, convert_scen_name)

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # if only one data input, insert in dict.
    non_dict_data = False
    if not isinstance(data, dict):
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
                raise KeyError(
                    'plot_kw must be a nested dictionary with keys corresponding to the keys in "data"'
                )

    # check: type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError(
                '"data" must be a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
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
                raise TypeError(
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
            raise ValueError(
                "Data structure not supported"
            )  # can probably be removed along with elif logic above,
            # given that get_array_categ() also does this check

    #  add/modify plot elements according to the first entry.
    set_plot_attrs(
        use_attrs,
        list(data.values())[0],
        ax,
        title_loc="left",
        wrap_kw={"min_line_len": 35, "max_line_len": 48},
    )
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
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    projection: ccrs.Projection = ccrs.LambertConformal(),
    transform: ccrs.Projection | None = None,
    features: list[str] | dict[str, dict[str, Any]] | None = None,
    geometries_kw: dict[str, Any] | None = None,
    contourf: bool = False,
    cmap: str | matplotlib.colors.Colormap | None = None,
    levels: int | None = None,
    divergent: bool | int | float = False,
    show_time: bool = False,
    frame: bool = False,
) -> matplotlib.axes.Axes:
    """Create map from 2D data.

    Parameters
    ----------
    data : dict, DataArray or Dataset
        Input data do plot. If dictionary, must have only one entry.
    ax : matplotlib axis, optional
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs : dict, optional
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'cbar_label': 'long_name', 'cbar_units': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw:  dict, optional
        Arguments to pass to the `xarray.plot.pcolormesh()` or 'xarray.plot.contourf()' function.
        If 'data' is a dictionary, can be a nested dictionary with the same keys as 'data'.
    projection : ccrs.Projection
        The projection to use, taken from the cartopy.crs options. Ignored if ax is not None.
    transform : ccrs.Projection, optional
        Transform corresponding to the data coordinate system. If None, an attempt is made to find dimensions matching
        ccrs.PlateCarree() or ccrs.RotatedPole().
    features : list or dict, optional
        Features to use, as a list or a nested dict containing kwargs. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers', 'states'].
    geometries_kw : dict, optional
        Arguments passed to cartopy ax.add_geometry() which adds given geometries (GeoDataFrame geometry) to axis.
    contourf : bool
        By default False, use plt.pcolormesh(). If True, use plt.contourf().
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/varaibles_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding colormap, aligned with the IPCC visual style guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    levels : int, optional
        Levels to use to divide the colormap. Acceptable values are from 2 to 21, inclusive.
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
    show_time : bool
        Show time (as date) at bottom right of plot.
    frame : bool
        Show or hide frame. Default False.

    Returns
    -------
    matplotlib.axes.Axes
    """

    # checks
    if levels:
        if type(levels) != int or levels < 2 or levels > 21:
            raise ValueError(
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
            raise ValueError("If `data` is a dict, it must be of length 1.")

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
    if isinstance(cmap, str):
        if cmap not in plt.colormaps():
            try:
                cmap = create_cmap(levels=levels, filename=cmap)
            except FileNotFoundError:
                pass

    elif cmap is None:
        cdata = Path(__file__).parents[1] / "data/ipcc_colors/variable_groups.json"
        cmap = create_cmap(
            get_var_group(path_to_json=cdata, da=plot_data),
            levels=levels,
            divergent=divergent,
        )

    # set defaults
    if divergent is not False:
        if isinstance(divergent, (int, float)):
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
    if features:
        add_cartopy_features(ax, features)

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


def gdfmap(
    df: gpd.GeoDataFrame,
    df_col: str,
    ax: cartopy.mpl.geoaxes.GeoAxes | cartopy.mpl.geoaxes.GeoAxesSubplot | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    projection: ccrs.Projection = ccrs.PlateCarree(),
    features: list[str] | dict[str, dict[str, Any]] | None = None,
    cmap: str | matplotlib.colors.Colormap | None = "slev_seq",
    levels: int | list[int | float] | None = None,
    cbar: bool = True,
    frame: bool = False,
) -> matplotlib.axes.Axes:
    """
    Create a map plot from geometries.

    Parameters
    ----------
    df : geopandas.GeoDataFrame
        Dataframe containing the geometries and the data to plot. Must have a column named 'geometry'.
    df_col : str
        Name of the column of 'df' containing the data to plot using the colorscale.
    ax : cartopy.mpl.geoaxes.GeoAxes or cartopy.mpl.geoaxes.GeoaxesSubplot, optional
        Matplotlib axis built with a projection, on which to plot.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw :  dict, optional
        Arguments to pass to the GeoDataFrame.plot() method.
    projection : ccrs.Projection
        The projection to use, taken from the cartopy.crs options.
    features : list or dict, optional
        Features to use, as a list or a nested dict containing kwargs. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers', 'states'].
    cmap : matplotlib.colors.Colormap or str
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/varaibles_groups.json) in the name of df_col
        and use corresponding colormap, aligned with the IPCC visual style guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    levels : int or list, optional
        Number of  levels or list of level boundaries (in data units) to use to divide the colormap.
    cbar : bool
        Show colorbar. Default 'True'.
    frame : bool
        Show or hide frame. Default False.

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create empty dicts if None
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)
    features = empty_dict(features)

    # checks
    if not isinstance(df, gpd.GeoDataFrame):
        raise TypeError("df myst be an instance of class geopandas.GeoDataFrame")

    if "geometry" not in df.columns:
        raise ValueError("column 'geometry' not found in GeoDataFrame")

    # convert to projection
    df = gpd_to_ccrs(df=df, proj=projection)

    # setup fig, ax
    if not ax:
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)
        ax.set_aspect("equal")  # recommended by geopandas

    # add features and defaults
    default_features = {
        "land": {"color": "#f0f0f0"},
        "rivers": {"edgecolor": "#cfd3d4"},
        "lakes": {"facecolor": "#cfd3d4"},
        "coastline": {"edgecolor": "black"},
    }
    features = default_features | features
    add_cartopy_features(ax, features)

    # colormap
    if isinstance(cmap, str):
        if cmap in plt.colormaps():
            cmap = matplotlib.colormaps[cmap]
        else:
            try:
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError:
                warnings.warn("invalid cmap, using default")
                cmap = create_cmap(filename="slev_seq")

    elif cmap is None:
        cdata = Path(__file__).parents[1] / "data/ipcc_colors/variable_groups.json"
        cmap = create_cmap(get_var_group(unique_str=df_col, path_to_json=cdata))

    # create normalization for colormap
    if levels:
        if isinstance(levels, int):
            lin_levels = clean_cmap_bounds(
                df[df_col].min(), df[df_col].max(), levels=levels
            )
            norm = matplotlib.colors.BoundaryNorm(boundaries=lin_levels, ncolors=cmap.N)
        elif isinstance(levels, list):
            norm = matplotlib.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
        else:
            raise TypeError("levels must be int or list")
        plot_kw.setdefault("norm", norm)

    # colorbar
    if cbar:
        plot_kw.setdefault("legend", True)
        plot_kw.setdefault("legend_kwds", {})
        plot_kw["legend_kwds"].setdefault("label", df_col)
        plot_kw["legend_kwds"].setdefault("orientation", "horizontal")
        plot_kw["legend_kwds"].setdefault("pad", 0.02)

    # plot
    plot = df.plot(column=df_col, ax=ax, cmap=cmap, **plot_kw)

    if frame is False:
        # cbar
        plot.figure.axes[1].spines["outline"].set_visible(False)
        plot.figure.axes[1].tick_params(size=0)
        # main axes
        ax.spines["geo"].set_visible(False)

    return ax


def violin(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    color: str | int | list[str | int] | None = None,
) -> matplotlib.axes.Axes:
    """Make violin plot using seaborn.

    Parameters
    ----------
    data : dict or Dataset/DataArray
        Input data to plot. If a dict, must contain DataArrays and/or Datasets.
    ax : matplotlib.axes.Axes, optional
        Matplotlib axis on which to plot.
    use_attrs : dict, optional
        A dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'ylabel': 'long_name', 'yunits': 'units'}.
        Only the keys found in the default dict can be used.
    fig_kw : dict, optional
        Arguments to pass to `plt.subplots()`. Only works if `ax` is not provided.
    plot_kw : dict, optional
        Arguments to pass to the `seaborn.violinplot()` function.
    color :  str, int or list, optional
        Unique color or list of colors to use. Integers point to the applied stylesheet's colors, in zero-indexed order.
        Passing 'color' or 'palette' in plot_kw overrides this argument.

    Returns
    -------
    matplotlib.axes.Axes
    """

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # if data is dict, assemble into one DataFrame
    non_dict_data = True
    if isinstance(data, dict):
        non_dict_data = False
        df = pd.DataFrame()
        for key, xr_obj in data.items():
            if isinstance(xr_obj, xr.Dataset):
                # if one data var, use key
                if len(list(xr_obj.data_vars)) == 1:
                    df[key] = xr_obj[list(xr_obj.data_vars)[0]].values
                # if more than one data var, use key + name of var
                else:
                    for data_var in list(xr_obj.data_vars):
                        df[key + "_" + data_var] = xr_obj[data_var].values

            elif isinstance(xr_obj, xr.DataArray):
                df[key] = xr_obj.values

            else:
                raise TypeError(
                    '"data" must be a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
                )

    elif isinstance(data, xr.Dataset):
        # create dataframe
        df = data.to_dataframe()
        df = df[data.data_vars]

    elif isinstance(data, xr.DataArray):
        # create dataframe
        df = data.to_dataframe()
        for coord in list(data.coords):
            if coord in df.columns:
                df = df.drop(columns=coord)

    else:
        raise TypeError(
            '"data" must be a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
        )

    # set fig, ax if not provided
    if not ax:
        fig, ax = plt.subplots(**fig_kw)

    # set default use_attrs values
    if "orient" in plot_kw and plot_kw["orient"] == "h":
        use_attrs = {"xlabel": "long_name", "xunits": "units"} | use_attrs
    else:
        use_attrs = {"ylabel": "long_name", "yunits": "units"} | use_attrs

    #  add/modify plot elements according to the first entry.
    if non_dict_data:
        set_plot_obj = data
    else:
        set_plot_obj = list(data.values())[0]

    set_plot_attrs(
        use_attrs,
        xr_obj=set_plot_obj,
        ax=ax,
        title_loc="left",
        wrap_kw={"min_line_len": 35, "max_line_len": 48},
    )

    # color
    if color:
        style_colors = matplotlib.rcParams["axes.prop_cycle"].by_key()["color"]
        if isinstance(color, str):
            plot_kw.setdefault("color", color)
        elif isinstance(color, int):
            try:
                plot_kw.setdefault("color", style_colors[color])
            except IndexError:
                raise IndexError("Index out of range of stylesheet colors")
        elif isinstance(color, list):
            for c, i in zip(color, np.arange(len(color))):
                if isinstance(c, int):
                    try:
                        color[i] = style_colors[c]
                    except IndexError:
                        raise IndexError("Index out of range of stylesheet colors")
            plot_kw.setdefault("palette", color)

    # plot
    sns.violinplot(df, ax=ax, **plot_kw)

    # grid
    if "orient" in plot_kw and plot_kw["orient"] == "h":
        ax.grid(visible=True, axis="x")

    return ax


def stripes(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    fig_kw: dict[str, Any] | None = None,
    divide: int | None = None,
    cmap: str | matplotlib.colors.Colormap | None = None,
    cmap_center: int | float = 0,
    cbar: bool = True,
    cbar_kw: dict[str, Any] | None = None,
) -> matplotlib.axes.Axes:
    """
    Create stripes plot with or without multiple scenarios.

    Parameters
    ----------
    data : dict or DataArray or Dataset
        Data to plot. If a dictionary of xarray objects, each will correspond to a scenario.
    ax : matplotlib.axes.Axes, optional
        Matplotlib axis on which to plot.
    fig_kw : : dict, optional
        Arguments to pass to `plt.subplots()`. Only works if `ax` is not provided.
    divide : int, optional
        Year at which the plot is divided into scenarios. If not provided, the horizontal separators
        will extent over the full time axis.
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/varaibles_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding diverging colormap, aligned with the IPCC visual style guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    cmap_center : int or float
        Center of the colormap in data coordinates. Default is 0.
    cbar : bool
        Show colorbar.
    cbar_kw : dict, optional
        Arguments to pass to plt.colorbar.

    Returns
    -------
    matplotlib.axes.Axes
    """

    # create empty dicts if None
    fig_kw = empty_dict(fig_kw)
    cbar_kw = empty_dict(cbar_kw)

    # init main (figure) axis
    if not ax:
        fig_kw.setdefault("figsize", (10, 5))
        fig, ax = plt.subplots(**fig_kw)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines[["top", "bottom", "left", "right"]].set_visible(False)

    # init plot axis
    ax_0 = ax.inset_axes([0, 0.15, 1, 0.75])

    # handle non-dict data
    if not isinstance(data, dict):
        data = {"_no_label": data}

    # convert SSP, RCP, CMIP formats in keys
    data = process_keys(data, convert_scen_name)

    n = len(data)

    # extract DataArrays from datasets
    for key, obj in data.items():
        if isinstance(obj, xr.DataArray):
            pass
        elif isinstance(obj, xr.Dataset):
            data[key] = obj[list(obj.data_vars)[0]]
        else:
            raise TypeError("data must contain xarray DataArrays or Datasets")

    # get time interval
    time_index = list(data.values())[0].time.dt.year.values
    delta_time = [
        time_index[i] - time_index[i - 1] for i in np.arange(1, len(time_index), 1)
    ]

    if all(i == delta_time[0] for i in delta_time):
        dtime = delta_time[0]
    else:
        raise ValueError("Time delta between each array element must be constant")

    # modify axes
    ax.set_xlim(min(time_index) - 0.5 * dtime, max(time_index) + 0.5 * dtime)
    ax_0.set_xlim(min(time_index) - 0.5 * dtime, max(time_index) + 0.5 * dtime)
    ax_0.set_ylim(0, 1)
    ax_0.set_yticks([])
    ax_0.xaxis.set_ticks_position("top")
    ax_0.tick_params(axis="x", direction="out", zorder=10)
    ax_0.spines[["top", "left", "right", "bottom"]].set_visible(False)

    # width of bars, to fill x axis limits
    width = (max(time_index) + 0.5 - min(time_index) - 0.5) / len(time_index)

    # create historical/projection divide
    if divide is not None:
        # convert divide year to transAxes
        divide_disp = ax_0.transData.transform(
            (divide - width * 0.5, 1)
        )  # left limit of stripe, 1 is placeholder
        divide_ax = ax_0.transAxes.inverted().transform(divide_disp)
        divide_ax = divide_ax[0]
    else:
        divide_ax = 0

    # create an inset ax for each da in data
    subaxes = {}
    for i in np.arange(n):
        name = "subax_" + str(i)
        y = (1 / n) * i
        subaxes[name] = ax_0.inset_axes([0, y, 1, 1 / n], transform=ax_0.transAxes)
        subaxes[name].set(xlim=ax_0.get_xlim(), ylim=(0, 1), xticks=[], yticks=[])
        subaxes[name].spines[["top", "bottom", "left", "right"]].set_visible(False)
        # lines separating axes
        if i > 0:
            subaxes[name].spines["bottom"].set_visible(True)
            subaxes[name].spines["bottom"].set(
                lw=2,
                color="w",
                bounds=(divide_ax, 1),
                transform=subaxes[name].transAxes,
            )
            # circles
            if divide:
                circle = matplotlib.patches.Ellipse(
                    xy=(divide_ax, y),
                    width=0.01,
                    height=0.03,
                    color="w",
                    transform=ax_0.transAxes,
                    zorder=10,
                )
                ax_0.add_patch(circle)

    # get max and min of all data
    data_min = 1e6
    data_max = -1e6
    for da in data.values():
        if min(da.values) < data_min:
            data_min = min(da.values)
        if max(da.values) > data_max:
            data_max = max(da.values)

    # colormap
    if isinstance(cmap, str):
        if cmap in plt.colormaps():
            cmap = matplotlib.colormaps[cmap]
        else:
            try:
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError:
                pass

    elif cmap is None:
        cdata = Path(__file__).parents[1] / "data/ipcc_colors/variable_groups.json"
        cmap = create_cmap(
            get_var_group(path_to_json=cdata, da=list(data.values())[0]), divergent=True
        )

    # create cmap norm
    if cmap_center is not None:
        norm = matplotlib.colors.TwoSlopeNorm(cmap_center, vmin=data_min, vmax=data_max)
    else:
        norm = matplotlib.colors.Normalize(data_min, data_max)

    # plot
    for (name, subax), (key, da) in zip(subaxes.items(), data.items()):
        subax.bar(da.time.dt.year, height=1, width=dtime, color=cmap(norm(da.values)))
        if divide:
            if key != "_no_label":
                subax.text(
                    0.99,
                    0.5,
                    key,
                    transform=subax.transAxes,
                    fontsize=14,
                    ha="right",
                    c="w",
                    weight="bold",
                )

    # colorbar
    if cbar is True:
        sm = ScalarMappable(cmap=cmap, norm=norm)
        cax = ax.inset_axes([0.01, 0.05, 0.35, 0.06])
        cbar_tcks = np.arange(math.floor(data_min), math.ceil(data_max), 2)
        # label
        label = ""
        if "long_name" in list(data.values())[0].attrs:
            label = list(data.values())[0].long_name
            if "units" in list(data.values())[0].attrs:
                u = list(data.values())[0].units
                label += f" ({u})"
            label = wrap_text(label, max_line_len=40)

        cbar_kw = {
            "cax": cax,
            "orientation": "horizontal",
            "ticks": cbar_tcks,
            "label": label,
        } | cbar_kw
        plt.colorbar(sm, **cbar_kw)
        cax.spines["outline"].set_visible(False)
        cax.set_xscale("linear")

    return ax
