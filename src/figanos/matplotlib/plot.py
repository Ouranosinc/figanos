# noqa: D100
from __future__ import annotations
import copy
import logging
import math
import string
import warnings
from collections.abc import Iterable
from inspect import signature
from pathlib import Path
from typing import Any

import cartopy.mpl.geoaxes
import geopandas as gpd
import matplotlib
import matplotlib.axes
import matplotlib.colors
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist.grid_finder as gf
import numpy as np
import pandas as pd
import seaborn as sns
import xarray as xr
from cartopy import crs as ccrs
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.projections import PolarAxes
from matplotlib.tri import Triangulation
from mpl_toolkits.axisartist.floating_axes import FloatingSubplot, GridHelperCurveLinear

from figanos.matplotlib.utils import (  # masknan_sizes_key,
    add_cartopy_features,
    add_features_map,
    check_timeindex,
    convert_scen_name,
    create_cmap,
    custom_cmap_norm,
    empty_dict,
    fill_between_label,
    get_array_categ,
    get_attributes,
    get_localized_term,
    get_rotpole,
    get_scen_color,
    get_var_group,
    gpd_to_ccrs,
    norm2range,
    plot_coords,
    process_keys,
    set_plot_attrs,
    size_legend_elements,
    sort_lines,
    split_legend,
    wrap_text,
)


logger = logging.getLogger(__name__)


def _plot_realizations(
    ax: matplotlib.axes.Axes,
    da: xr.DataArray,
    name: str,
    plot_kw: dict[str, Any],
    non_dict_data: dict[str, Any],
) -> matplotlib.axes.Axes:
    """
    Plot realizations from a DataArray, inside or outside a Dataset.

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


def _plot_timeseries(
    ax: matplotlib.axes.Axes,
    name: str,
    arr: xr.DataArray | xr.Dataset,
    plot_kw: dict[str, Any],
    non_dict_data: bool,
    array_categ: dict[str, Any],
    legend: str,
) -> matplotlib.axes.Axes:
    """
    Plot figanos timeseries.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Axe to be used for plotting.
    name : str
        Dictionary key of the plotted data.
    arr : Dataset/DataArray
        Data to be plotted.
    plot_kw : dict
        Dictionary of kwargs coming from the timeseries() input.
    non_dic_data : bool
        If True, plot_kw is not a dictionary.
    array_categ: dict
        Categories of data.
    legend: str
        Legend type.

    Returns
    -------
    matplotlib.axes.Axes
    """
    lines_dict = {}  # created to facilitate accessing line properties later
    # look for SSP, RCP, CMIP model color
    cat_colors = Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
    if get_scen_color(name, cat_colors):
        plot_kw[name].setdefault("color", get_scen_color(name, cat_colors))

    #  remove 'label' to avoid error due to double 'label' args
    if "label" in plot_kw[name]:
        del plot_kw[name]["label"]
        warnings.warn(f'"label" entry in plot_kw[{name}] will be ignored.', stacklevel=2)

    if array_categ[name] == "ENS_REALS_DA":
        _plot_realizations(ax, arr, name, plot_kw, non_dict_data)

    elif array_categ[name] == "ENS_REALS_DS":
        if len(arr.data_vars) >= 2:
            raise TypeError(
                "To plot multiple ensembles containing realizations, use DataArrays outside a Dataset"
            )
        for sub_arr in arr.data_vars.values():
            _plot_realizations(ax, sub_arr, name, plot_kw, non_dict_data)

    elif array_categ[name] == "ENS_PCT_DIM_DS":
        for sub_arr in arr.data_vars.values():
            sub_name = (
                sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)
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
        for sub_arr in arr.data_vars.values():
            sub_name = (
                sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)
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
        lines_dict[name] = ax.plot(arr["time"], arr.values, label=name, **plot_kw[name])

    else:
        raise ValueError(
            "Data structure not supported"
        )  # can probably be removed along with elif logic above,
        # given that get_array_categ() also does this check
    return ax


def timeseries(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    legend: str = "lines",
    show_lat_lon: bool | str | int | tuple[float, float] = True,
    enumerate_subplots: bool = False,
) -> matplotlib.axes.Axes:
    """
    Plot time series from 1D Xarray Datasets or DataArrays as line plots.

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
    legend : str (default 'lines') or dict
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines),
         'edge' (out of plot), 'facetgrid' under figure, 'none' (no legend). If dict, arguments to pass to ax.legend().
    show_lat_lon : bool, tuple, str or int
        If True, show latitude and longitude at the bottom right of the figure.
        Can be a tuple of axis coordinates (from 0 to 1, as a fraction of the axis length) representing
        the location of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

        ==================   =============
        Location String      Location Code
        ==================   =============
        'upper right'        1
        'upper left'         2
        'lower left'         3
        'lower right'        4
        'right'              5
        'center left'        6
        'center right'       7
        'lower center'       8
        'upper center'       9
        'center'             10
        ==================   =============
    enumerate_subplots: bool
        If True, enumerate subplots with letters.
        Only works with facetgrids (pass `col` or `row` in plot_kw).

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
    for arr in data.values():
        if not isinstance(arr, xr.Dataset | xr.DataArray):
            raise TypeError(
                '"data" must be a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
            )

    # check: 'time' dimension and calendar format
    data = check_timeindex(data)

    # set fig, ax if not provided
    if ax is None and (
        "row" not in list(plot_kw.values())[0].keys()
        and "col" not in list(plot_kw.values())[0].keys()
    ):
        fig, ax = plt.subplots(**fig_kw)
    elif ax is not None and (
        "col" in list(plot_kw.values())[0].keys()
        or "row" in list(plot_kw.values())[0].keys()
    ):
        raise ValueError("Cannot use 'ax' and 'col'/'row' at the same time.")
    elif ax is None:
        cfig_kw = fig_kw.copy()
        if "figsize" in fig_kw:  # add figsize to plot_kw for facetgrid
            list(plot_kw.values())[0].setdefault("figsize", fig_kw["figsize"])
            cfig_kw.pop("figsize")
        if cfig_kw:
            for v in plot_kw.values():
                {"subplots_kws": cfig_kw} | v
            warnings.warn(
                "Only figsize and figure.add_subplot() arguments can be passed to fig_kw when using facetgrid.", stacklevel=2
            )

    # set default use_attrs values
    if ax:
        use_attrs.setdefault("title", "description")
    else:
        use_attrs.setdefault("suptitle", "description")
    use_attrs.setdefault("ylabel", "long_name")
    use_attrs.setdefault("yunits", "units")

    # dict of array 'categories'
    array_categ = {name: get_array_categ(array) for name, array in data.items()}
    cp_plot_kw = copy.deepcopy(plot_kw)
    # get data and plot
    for name, arr in data.items():
        if ax:
            _plot_timeseries(ax, name, arr, plot_kw, non_dict_data, array_categ, legend)
        else:
            if name == list(data.keys())[0]:
                # create empty DataArray with same dimensions as data first entry to create an empty xr.plot.FacetGrid
                if isinstance(arr, xr.Dataset):
                    da = arr[list(arr.keys())[0]]
                else:
                    da = arr
                da = da.where(da == np.nan)
                im = da.plot(**plot_kw[name], color="white")

            [
                cp_plot_kw[name].pop(key)
                for key in ["row", "col", "figsize"]
                if key in cp_plot_kw[name].keys()
            ]

            # plot data in every axis of the facetgrid
            for i in range(0, im.axs.shape[0]):
                for j in range(0, im.axs.shape[1]):
                    sel_arr = {}

                    if "row" in plot_kw[name]:
                        sel_arr[plot_kw[name]["row"]] = i
                    if "col" in plot_kw[name]:
                        sel_arr[plot_kw[name]["col"]] = j

                    _plot_timeseries(
                        im.axs[i, j],
                        name,
                        arr.isel(**sel_arr).squeeze(),
                        cp_plot_kw,
                        non_dict_data,
                        array_categ,
                        legend,
                    )

    #  add/modify plot elements according to the first entry.
    if ax:
        set_plot_attrs(
            use_attrs,
            list(data.values())[0],
            ax,
            title_loc="left",
            wrap_kw={"min_line_len": 35, "max_line_len": 48},
        )
        ax.set_xlabel(
            get_localized_term("time").capitalize()
        )  # check_timeindex() already checks for 'time'

        # other plot elements
        if show_lat_lon:
            if show_lat_lon is True:
                plot_coords(
                    ax,
                    list(data.values())[0],
                    param="location",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_lat_lon, str | tuple | int):
                plot_coords(
                    ax,
                    list(data.values())[0],
                    param="location",
                    loc=show_lat_lon,
                    backgroundalpha=1,
                )
            else:
                raise TypeError(" show_lat_lon must be a bool, string, int, or tuple")

        if legend is not None:
            if not ax.get_legend_handles_labels()[0]:  # check if legend is empty
                pass
            elif legend == "in_plot":
                split_legend(ax, in_plot=True)
            elif legend == "edge":
                split_legend(ax, in_plot=False)
            elif isinstance(legend, dict):
                ax.legend(**legend)
            else:
                ax.legend()

        return ax
    else:
        if legend is not None:
            if not im.axs[-1, -1].get_legend_handles_labels()[
                0
            ]:  # check if legend is empty
                pass
            elif legend == "in_plot":
                split_legend(im.axs[-1, -1], in_plot=True)
            elif legend == "edge":
                split_legend(im.axs[-1, -1], in_plot=False)
            elif isinstance(legend, dict):
                handles, labels = im.axs[-1, -1].get_legend_handles_labels()
                legend = {"handles": handles, "labels": labels} | legend
                im.fig.legend(**legend)
            elif legend == "facetgrid":
                handles, labels = im.axs[-1, -1].get_legend_handles_labels()
                im.fig.legend(
                    handles,
                    labels,
                    loc="lower center",
                    ncol=len(im.axs[-1, -1].lines),
                    bbox_to_anchor=(0.5, -0.05),
                )

        if show_lat_lon:
            if show_lat_lon is True:
                plot_coords(
                    None,
                    list(data.values())[0].isel(lat=0, lon=0),
                    param="location",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_lat_lon, str | tuple | int):
                plot_coords(
                    None,
                    list(data.values())[0].isel(lat=0, lon=0),
                    param="location",
                    loc=show_lat_lon,
                    backgroundalpha=1,
                )
        if enumerate_subplots and isinstance(im, xr.plot.facetgrid.FacetGrid):
            for idx, ax in enumerate(im.axs.flat):
                ax.set_title(f"{string.ascii_lowercase[idx]}) {ax.get_title()}")

        return im


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
    levels: int | list | np.ndarray | None = None,
    divergent: bool | int | float = False,
    show_time: bool | str | int | tuple[float, float] = False,
    frame: bool = False,
    enumerate_subplots: bool = False,
) -> matplotlib.axes.Axes:
    """
    Create map from 2D data.

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
    levels : int, list, np.ndarray, optional
        Number of levels to divide the colormap into or list of level boundaries (in data units).
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
    show_time : bool, tuple, string or int.
        If True, show time (as date) at the bottom right of the figure.
        Can be a tuple of axis coordinates (0 to 1, as a fraction of the axis length) representing the location
        of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

        ==================   =============
        Location String      Location Code
        ==================   =============
        'upper right'        1
        'upper left'         2
        'lower left'         3
        'lower right'        4
        'right'              5
        'center left'        6
        'center right'       7
        'lower center'       8
        'upper center'       9
        'center'             10
        ==================   =============
    frame : bool
        Show or hide frame. Default False.
    enumerate_subplots: bool
        If True, enumerate subplots with letters.
        Only works with facetgrids (pass `col` or `row` in plot_kw).

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # set default use_attrs values
    use_attrs = {"cbar_label": "long_name", "cbar_units": "units"} | use_attrs
    if "row" not in plot_kw and "col" not in plot_kw:
        use_attrs.setdefault("title", "description")

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
        plot_data = data.squeeze()
    elif isinstance(data, xr.Dataset):
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        plot_data = data[list(data.keys())[0]].squeeze()
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    # setup transform
    if transform is None:
        if "lat" in data.dims and "lon" in data.dims:
            transform = ccrs.PlateCarree()
        if "rlat" in data.dims and "rlon" in data.dims:
            transform = get_rotpole(data)

    # setup fig, ax
    if ax is None and ("row" not in plot_kw.keys() and "col" not in plot_kw.keys()):
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)
    elif ax is not None and ("col" in plot_kw or "row" in plot_kw):
        raise ValueError("Cannot use 'ax' and 'col'/'row' at the same time.")
    elif ax is None:
        plot_kw = {"subplot_kws": {"projection": projection}} | plot_kw
        cfig_kw = fig_kw.copy()
        if "figsize" in fig_kw:  # add figsize to plot_kw for facetgrid
            plot_kw.setdefault("figsize", fig_kw["figsize"])
            cfig_kw.pop("figsize")
        if len(cfig_kw) >= 1:
            plot_kw = {"subplot_kws": {"projection": cfig_kw}} | plot_kw
            warnings.warn(
                "Only figsize and figure.add_subplot() arguments can be passed to fig_kw when using facetgrid.", stacklevel=2
            )

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
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError as e:
                logger.error(e)
                pass

    elif cmap is None:
        cmap = create_cmap(
            get_var_group(da=plot_data),
            divergent=divergent,
        )
    plot_kw.setdefault("cmap", cmap)

    if levels is not None:
        if isinstance(levels, Iterable):
            lin = levels
        else:
            lin = custom_cmap_norm(
                cmap,
                np.nanmin(plot_data.values),
                np.nanmax(plot_data.values),
                levels=levels,
                divergent=divergent,
                linspace_out=True,
            )
        plot_kw.setdefault("levels", lin)

    elif (divergent is not False) and ("levels" not in plot_kw):
        vmin = plot_kw.pop("vmin", np.nanmin(plot_data.values))
        vmax = plot_kw.pop("vmax", np.nanmax(plot_data.values))
        norm = custom_cmap_norm(
            cmap,
            vmin,
            vmax,
            levels=levels,
            divergent=divergent,
        )
        plot_kw.setdefault("norm", norm)

    # set defaults
    if divergent is not False:
        if isinstance(divergent, int | float):
            plot_kw.setdefault("center", divergent)
        else:
            plot_kw.setdefault("center", 0)

    if "add_colorbar" not in plot_kw or plot_kw["add_colorbar"] is not False:
        plot_kw.setdefault("cbar_kwargs", {})
        plot_kw["cbar_kwargs"].setdefault("label", wrap_text(cbar_label))

    # bug xlim / ylim + transform in facetgrids
    # (see https://github.com/pydata/xarray/issues/8562#issuecomment-1865189766)
    if transform and ("xlim" in plot_kw and "ylim" in plot_kw):
        extent = [
            plot_kw["xlim"][0],
            plot_kw["xlim"][1],
            plot_kw["ylim"][0],
            plot_kw["ylim"][1],
        ]
        plot_kw.pop("xlim")
        plot_kw.pop("ylim")
    elif transform and ("xlim" in plot_kw or "ylim" in plot_kw):
        extent = None
        warnings.warn(
            "Requires both xlim and ylim with 'transform'. Xlim or ylim was dropped", stacklevel=2
        )
        if "xlim" in plot_kw.keys():
            plot_kw.pop("xlim")
        if "ylim" in plot_kw.keys():
            plot_kw.pop("ylim")
    else:
        extent = None

    # plot
    if ax:
        plot_kw.setdefault("ax", ax)
    if transform:
        plot_kw.setdefault("transform", transform)

    if contourf is False:
        im = plot_data.plot.pcolormesh(**plot_kw)
    else:
        im = plot_data.plot.contourf(**plot_kw)

    if ax:
        if extent:
            ax.set_extent(extent)

        ax = add_features_map(
            data,
            ax,
            use_attrs,
            projection,
            features,
            geometries_kw,
            frame,
        )
        if show_time:
            if isinstance(show_time, bool):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc=show_time,
                    backgroundalpha=1,
                )

        # when im is an ax, it has a colorbar attribute. If it is a facetgrid, it has a cbar attribute.
        if (frame is False) and (
            (getattr(im, "colorbar", None) is not None)
            or (getattr(im, "cbar", None) is not None)
        ):
            im.colorbar.outline.set_visible(False)
        return ax

    else:
        for _i, fax in enumerate(im.axs.flat):
            add_features_map(
                data,
                fax,
                use_attrs,
                projection,
                features,
                geometries_kw,
                frame,
            )
            if extent:
                fax.set_extent(extent)

            # when im is an ax, it has a colorbar attribute. If it is a facetgrid, it has a cbar attribute.
        if (frame is False) and (
            (getattr(im, "colorbar", None) is not None)
            or (getattr(im, "cbar", None) is not None)
        ):
            im.cbar.outline.set_visible(False)

        if show_time:
            if isinstance(show_time, bool):
                plot_coords(
                    None,
                    plot_data,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    None,
                    plot_data,
                    param="time",
                    loc=show_time,
                    backgroundalpha=1,
                )

        use_attrs.setdefault("suptitle", "long_name")
        im = set_plot_attrs(use_attrs, data, facetgrid=im)
        if enumerate_subplots and isinstance(im, xr.plot.facetgrid.FacetGrid):
            for idx, ax in enumerate(im.axs.flat):
                ax.set_title(f"{string.ascii_lowercase[idx]}) {ax.get_title()}")

        return im


def gdfmap(
    df: gpd.GeoDataFrame,
    df_col: str,
    ax: cartopy.mpl.geoaxes.GeoAxes | cartopy.mpl.geoaxes.GeoAxesSubplot | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    projection: ccrs.Projection = ccrs.LambertConformal(),
    features: list[str] | dict[str, dict[str, Any]] | None = None,
    cmap: str | matplotlib.colors.Colormap | None = None,
    levels: int | list[int | float] | None = None,
    divergent: bool | int | float = False,
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
        If `boundary`, only the boundary of the geometries is plotted, without colorscale.
    ax : cartopy.mpl.geoaxes.GeoAxes or cartopy.mpl.geoaxes.GeoaxesSubplot, optional
        Matplotlib axis built with a projection, on which to plot.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw :  dict, optional
        Arguments to pass to the GeoDataFrame.plot() method.
    projection : ccrs.Projection
        The projection to use, taken from the cartopy.crs options. Ignored if ax is not None.
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
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
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
    if ax is None:
        df = gpd_to_ccrs(df=df, proj=projection)
    else:
        df = gpd_to_ccrs(df=df, proj=ax.projection)

    # setup fig, ax
    if ax is None:
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)
        ax.set_aspect("equal")  # recommended by geopandas

    # add features
    if features:
        add_cartopy_features(ax, features)

    if df_col == "boundary":
        plot = df.boundary.plot(ax=ax, **plot_kw)
        if cmap is not None or levels is not None or divergent is not False:
            warnings.warn("Colomap arguments are ignored when plotting 'boundary'.", stacklevel=2)
    else:

        # colormap
        if isinstance(cmap, str):
            if cmap in plt.colormaps():
                cmap = matplotlib.colormaps[cmap]
            else:
                try:
                    cmap = create_cmap(filename=cmap)
                except FileNotFoundError:
                    warnings.warn("invalid cmap, using default", stacklevel=2)
                    cmap = create_cmap(filename="slev_seq")

        elif cmap is None:
            cmap = create_cmap(
                get_var_group(unique_str=df_col),
                divergent=divergent,
            )

        # create normalization for colormap
        plot_kw.setdefault("vmin", df[df_col].min())
        plot_kw.setdefault("vmax", df[df_col].max())

        if (levels is not None) or (divergent is not False):
            norm = custom_cmap_norm(
                cmap,
                plot_kw["vmin"],
                plot_kw["vmax"],
                levels=levels,
                divergent=divergent,
            )
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
        if len(plot.figure.axes) > 1:  # only if it exists
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
    """
    Make violin plot using seaborn.

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
    if ax is None:
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
            except IndexError as err:
                raise IndexError("Index out of range of stylesheet colors") from err
        elif isinstance(color, list):
            for c, i in zip(color, np.arange(len(color)), strict=False):
                if isinstance(c, int):
                    try:
                        color[i] = style_colors[c]
                    except IndexError as err:
                        raise IndexError("Index out of range of stylesheet colors") from err
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
        will extend over the full time axis.
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/variables_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding diverging colormap, aligned with the IPCC Visual Style
        Guide 2022 (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
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
    if ax is None:
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
            except FileNotFoundError as e:
                logger.error(e)
                pass

    elif cmap is None:
        cmap = create_cmap(
            get_var_group(da=list(data.values())[0]),
            divergent=True,
        )

    # create cmap norm
    if cmap_center is not None:
        norm = matplotlib.colors.TwoSlopeNorm(cmap_center, vmin=data_min, vmax=data_max)
    else:
        norm = matplotlib.colors.Normalize(data_min, data_max)

    # plot
    for (_name, subax), (key, da) in zip(subaxes.items(), data.items(), strict=False):
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
                    va="center",
                    c="w",
                    weight="bold",
                )

    # colorbar
    if cbar is True:
        sm = ScalarMappable(cmap=cmap, norm=norm)
        cax = ax.inset_axes([0.01, 0.05, 0.35, 0.06])
        cbar_tcks = np.arange(math.floor(data_min), math.ceil(data_max), 2)
        # label
        da = list(data.values())[0]
        label = get_attributes("long_name", da)
        if label != "":
            if "units" in da.attrs:
                u = da.units
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


def heatmap(
    data: xr.DataArray | xr.Dataset | dict[str, Any],
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    transpose: bool = False,
    cmap: str | matplotlib.colors.Colormap | None = "RdBu",
    divergent: bool | int | float = False,
) -> matplotlib.axes.Axes:
    """
    Create heatmap from a DataArray.

    Parameters
    ----------
    data : dict or DataArray or Dataset
        Input data do plot. If dictionary, must have only one entry.
    ax : matplotlib axis, optional
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs : dict, optional
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'cbar_label': 'long_name'}.
        Only the keys found in the default dict can be used.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw :  dict, optional
        Arguments to pass to the 'seaborn.heatmap()' function.
        If 'data' is a dictionary, can be a nested dictionary with the same key as 'data'.
    transpose : bool
        If true, the 2D data will be transposed, so that the original x-axis becomes the y-axis and vice versa.
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/variables_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding colormap, aligned with the IPCC Visual Style Guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)

    # set default use_attrs values
    use_attrs.setdefault("cbar_label", "long_name")

    # if data is dict, extract
    if isinstance(data, dict):
        if plot_kw and list(data.keys())[0] in plot_kw.keys():
            plot_kw = plot_kw[list(data.keys())[0]]
        if len(data) == 1:
            data = list(data.values())[0]
        else:
            raise ValueError("If `data` is a dict, it must be of length 1.")

    # select data to plot
    if isinstance(data, xr.DataArray):
        da = data
    elif isinstance(data, xr.Dataset):
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        da = list(data.values())[0]
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    # setup fig, axis
    if ax is None and ("row" not in plot_kw.keys() and "col" not in plot_kw.keys()):
        fig, ax = plt.subplots(**fig_kw)
    elif ax is not None and ("col" in plot_kw or "row" in plot_kw):
        raise ValueError("Cannot use 'ax' and 'col'/'row' at the same time.")
    elif ax is None:
        if any([k != "figsize" for k in fig_kw.keys()]):
            warnings.warn(
                "Only figsize arguments can be passed to fig_kw when using facetgrid.", stacklevel=2
            )
        plot_kw.setdefault("col", None)
        plot_kw.setdefault("row", None)
        plot_kw.setdefault("margin_titles", True)
        heatmap_dims = list(
            set(da.dims)
            - {d for d in [plot_kw["col"], plot_kw["row"]] if d is not None}
        )
        if da.name is None:
            da = da.to_dataset(name="data").data
        da_name = da.name

    # create cbar label
    if (
        "cbar_units" in use_attrs
        and len(get_attributes(use_attrs["cbar_units"], data)) >= 1
    ):  # avoids '()' as label
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
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError as e:
                logger.error(e)
                pass

    elif cmap is None:
        cmap = create_cmap(
            get_var_group(da=da),
            divergent=divergent,
        )

    # convert data to DataFrame
    if transpose:
        da = da.transpose()
    if "col" not in plot_kw and "row" not in plot_kw:
        if len(da.dims) != 2:
            raise ValueError("DataArray must have exactly two dimensions")
        df = da.to_pandas()
    else:
        if len(heatmap_dims) != 2:
            raise ValueError("DataArray must have exactly two dimensions")
        df = da.to_dataframe().reset_index()

    # set defaults
    if divergent is not False:
        if isinstance(divergent, int | float):
            plot_kw.setdefault("center", divergent)
        else:
            plot_kw.setdefault("center", 0)

    if "cbar" not in plot_kw or plot_kw["cbar"] is not False:
        plot_kw.setdefault("cbar_kws", {})
        plot_kw["cbar_kws"].setdefault("label", wrap_text(cbar_label))

    plot_kw.setdefault("cmap", cmap)

    # plot
    def draw_heatmap(*args, **kwargs):
        data = kwargs.pop("data")
        d = (
            data
            if len(args) == 0
            # Any sorting should be performed before sending a DataArray in `fg.heatmap`
            else data.pivot_table(
                index=args[1], columns=args[0], values=args[2], sort=False
            )
        )
        ax = sns.heatmap(d, **kwargs)
        ax.set_xticklabels(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            rotation_mode="anchor",
        )
        ax.tick_params(axis="both", direction="out")
        set_plot_attrs(
            use_attrs,
            da,
            ax,
            title_loc="center",
            wrap_kw={"min_line_len": 35, "max_line_len": 44},
        )
        return ax

    if ax is not None:
        ax = draw_heatmap(data=df, ax=ax, **plot_kw)
        return ax
    elif "col" in plot_kw or "row" in plot_kw:
        # When using xarray's FacetGrid, `plot_kw` can be used in the FacetGrid and in the plotting function
        # With Seaborn, we need to be more careful and separate keywords.
        plot_kw_hm = {
            k: v for k, v in plot_kw.items() if k in signature(sns.heatmap).parameters
        }
        plot_kw_fg = {
            k: v for k, v in plot_kw.items() if k in signature(sns.FacetGrid).parameters
        }
        unused_keys = (
            set(plot_kw.keys()) - set(plot_kw_fg.keys()) - set(plot_kw_hm.keys())
        )
        if unused_keys != set():
            raise ValueError(
                f"`heatmap` got unexpected keywords in `plot_kw`: {unused_keys}. Keywords in `plot_kw` should be keywords "
                "allowed in `sns.heatmap` or `sns.FacetGrid`. "
            )

        g = sns.FacetGrid(df, **plot_kw_fg)
        cax = g.fig.add_axes([0.95, 0.05, 0.02, 0.9])
        g.map_dataframe(
            draw_heatmap,
            *heatmap_dims,
            da_name,
            **plot_kw_hm,
            cbar=True,
            cbar_ax=cax,
        )
        g.fig.subplots_adjust(right=0.9)
        if "figsize" in fig_kw.keys():
            g.fig.set_size_inches(*fig_kw["figsize"])
        return g


def scattermap(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    projection: ccrs.Projection = ccrs.LambertConformal(),
    transform: ccrs.Projection | None = None,
    features: list[str] | dict[str, dict[str, Any]] | None = None,
    geometries_kw: dict[str, Any] | None = None,
    sizes: str | bool | None = None,
    size_range: tuple = (10, 60),
    cmap: str | matplotlib.colors.Colormap | None = None,
    levels: int | None = None,
    divergent: bool | int | float = False,
    legend_kw: dict[str, Any] | None = None,
    show_time: bool | str | int | tuple[float, float] = False,
    frame: bool = False,
    enumerate_subplots: bool = False,
) -> matplotlib.axes.Axes:
    """
    Make a scatter plot of georeferenced data on a map.

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
    plot_kw :  dict, optional
        Arguments to pass to `plt.scatter()`.
        If 'data' is a dictionary, can be a dictionary with the same key as 'data'.
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
    sizes : bool or str, optional
        String name of the coordinate to use for determining point size. If True, use the same data as in the colorbar.
    size_range : tuple
        Tuple of the minimum and maximum size of the points.
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/variables_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding colormap, aligned with the IPCC Visual Style Guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    levels : int, optional
        Number of levels to divide the colormap into.
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
    legend_kw : dict, optional
        Arguments to pass to plt.legend(). Some defaults {"loc": "lower left", "facecolor": "w", "framealpha": 1,
            "edgecolor": "w", "bbox_to_anchor": (-0.05, 0)}
    show_time : bool, tuple, string or int.
        If True, show time (as date) at the bottom right of the figure.
        Can be a tuple of axis coordinates (0 to 1, as a fraction of the axis length) representing the location
        of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

        ==================   =============
        Location String      Location Code
        ==================   =============
        'upper right'        1
        'upper left'         2
        'lower left'         3
        'lower right'        4
        'right'              5
        'center left'        6
        'center right'       7
        'lower center'       8
        'upper center'       9
        'center'             10
        ==================   =============
    frame : bool
        Show or hide frame. Default False.
    enumerate_subplots: bool
        If True, enumerate subplots with letters.
        Only works with facetgrids (pass `col` or `row` in plot_kw).

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)
    legend_kw = empty_dict(legend_kw)

    # set default use_attrs values
    use_attrs = {"cbar_label": "long_name", "cbar_units": "units"} | use_attrs
    if "row" not in plot_kw and "col" not in plot_kw:
        use_attrs.setdefault("title", "description")

    # extract plot_kw from dict if needed
    if isinstance(data, dict) and plot_kw and list(data.keys())[0] in plot_kw.keys():
        plot_kw = plot_kw[list(data.keys())[0]]

    # figanos does not use xr.plot.scatter default markersize
    if "markersize" in plot_kw.keys():
        if not sizes:
            sizes = plot_kw["markersize"]
        plot_kw.pop("markersize")

    # if data is dict, extract
    if isinstance(data, dict):
        if len(data) == 1:
            data = list(data.values())[0].squeeze()
            if len(data.data_vars) > 1:
                warnings.warn(
                    "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
                )
        else:
            raise ValueError("If `data` is a dict, it must be of length 1.")

    # select data to plot and its xr.Dataset
    if isinstance(data, xr.DataArray):
        plot_data = data
        data = xr.Dataset({plot_data.name: plot_data})
    elif isinstance(data, xr.Dataset):
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        plot_data = data[list(data.keys())[0]]
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    # setup transform
    if transform is None:
        if "rlat" in data.dims and "rlon" in data.dims:
            transform = get_rotpole(data)
        elif (
            "lat" in data.coords and "lon" in data.coords
        ):  # need to work with station dims
            transform = ccrs.PlateCarree()

    # setup fig, ax
    if ax is None and ("row" not in plot_kw.keys() and "col" not in plot_kw.keys()):
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)
    elif ax is not None and ("col" in plot_kw or "row" in plot_kw):
        raise ValueError("Cannot use 'ax' and 'col'/'row' at the same time.")
    elif ax is None:
        plot_kw = {"subplot_kws": {"projection": projection}} | plot_kw
        cfig_kw = fig_kw.copy()
        if "figsize" in fig_kw:  # add figsize to plot_kw for facetgrid
            plot_kw.setdefault("figsize", fig_kw["figsize"])
            cfig_kw.pop("figsize")
        if len(cfig_kw) >= 1:
            plot_kw = {"subplot_kws": {"projection": projection}} | plot_kw
            warnings.warn(
                "Only figsize and figure.add_subplot() arguments can be passed to fig_kw when using facetgrid.", stacklevel=2
            )

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

    if "add_colorbar" not in plot_kw or plot_kw["add_colorbar"] is not False:
        plot_kw.setdefault("cbar_kwargs", {})
        plot_kw["cbar_kwargs"].setdefault("label", wrap_text(cbar_label))
        plot_kw["cbar_kwargs"].setdefault("pad", 0.015)

    # colormap
    if isinstance(cmap, str):
        if cmap not in plt.colormaps():
            try:
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError as e:
                logger.error(e)
                pass

    elif cmap is None:
        cmap = create_cmap(
            get_var_group(da=plot_data),
            divergent=divergent,
        )

    # nans (not required for plotting since xarray.plot handles np.nan, but needs to be found for sizes legend and to
    # inform user on how many stations were dropped)
    mask = ~np.isnan(plot_data.values)
    if np.sum(mask) < len(mask):
        warnings.warn(
            f"{len(mask) - np.sum(mask)} nan values were dropped when plotting the color values", stacklevel=2
        )

    # point sizes
    if sizes:
        if sizes is True:
            sdata = plot_data
        elif isinstance(sizes, str):
            if hasattr(data, "name") and data.name == sizes:
                sdata = plot_data
            elif sizes in list(data.coords.keys()):
                sdata = plot_data[sizes]
            else:
                raise ValueError(f"{sizes} not found")
        else:
            raise TypeError("sizes must be a string or a bool")

        # nans sizes
        smask = ~np.isnan(sdata.values) & mask
        if np.sum(smask) < np.sum(mask):
            warnings.warn(
                f"{np.sum(mask) - np.sum(smask)} nan values were dropped when setting the point size", stacklevel=2
            )
            mask = smask

        pt_sizes = norm2range(
            data=sdata.where(mask).values,
            target_range=size_range,
            data_range=None,
        )
        plot_kw.setdefault("add_legend", False)
        if ax:
            plot_kw.setdefault("s", pt_sizes)
        else:
            plot_kw.setdefault("s", pt_sizes[0])

    # norm
    plot_kw.setdefault("vmin", np.nanmin(plot_data.values[mask]))
    plot_kw.setdefault("vmax", np.nanmax(plot_data.values[mask]))
    if levels is not None:
        if isinstance(levels, Iterable):
            lin = levels
        else:
            lin = custom_cmap_norm(
                cmap,
                np.nanmin(plot_data.values[mask]),
                np.nanmax(plot_data.values[mask]),
                levels=levels,
                divergent=divergent,
                linspace_out=True,
            )
        plot_kw.setdefault("levels", lin)

    elif (divergent is not False) and ("levels" not in plot_kw):
        vmin = plot_kw.pop("vmin", np.nanmin(plot_data.values[mask]))
        vmax = plot_kw.pop("vmax", np.nanmax(plot_data.values[mask]))
        norm = custom_cmap_norm(
            cmap,
            vmin,
            vmax,
            levels=levels,
            divergent=divergent,
        )
        plot_kw.setdefault("norm", norm)

    # matplotlib.pyplot.scatter treats "edgecolor" and "edgecolors" as aliases so we accept "edgecolor" and convert it
    if "edgecolor" in plot_kw and "edgecolors" not in plot_kw:
        plot_kw["edgecolors"] = plot_kw["edgecolor"]
        plot_kw.pop("edgecolor")

    # set defaults and create copy without vmin, vmax (conflicts with norm)
    plot_kw = {
        "cmap": cmap,
        "transform": transform,
        "zorder": 8,
        "marker": "o",
    } | plot_kw

    # check if edgecolors in plot_kw and match len of plot_data
    if "edgecolors" in plot_kw:
        if matplotlib.colors.is_color_like(plot_kw["edgecolors"]):
            plot_kw["edgecolors"] = np.repeat(
                plot_kw["edgecolors"], len(plot_data.where(mask).values)
            )
        elif len(plot_kw["edgecolors"]) != len(plot_data.values):
            plot_kw["edgecolors"] = np.repeat(
                plot_kw["edgecolors"][0], len(plot_data.where(mask).values)
            )
            warnings.warn(
                "Length of edgecolors does not match length of data. Only first edgecolor is used for plotting.", stacklevel=2
            )
        else:
            if isinstance(plot_kw["edgecolors"], list):
                plot_kw["edgecolors"] = np.array(plot_kw["edgecolors"])
            plot_kw["edgecolors"] = plot_kw["edgecolors"][mask]
    else:
        plot_kw.setdefault("edgecolors", "none")

    for key in ["vmin", "vmax"]:
        plot_kw.pop(key, None)
    # plot
    plot_kw = {"x": "lon", "y": "lat", "hue": plot_data.name} | plot_kw
    if ax:
        plot_kw.setdefault("ax", ax)

    plot_data_masked = plot_data.where(mask).to_dataset()
    im = plot_data_masked.plot.scatter(**plot_kw)

    # add features
    if ax:
        ax = add_features_map(
            data,
            ax,
            use_attrs,
            projection,
            features,
            geometries_kw,
            frame,
        )

        if show_time:
            if isinstance(show_time, bool):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc=show_time,
                    backgroundalpha=1,
                )

        if (frame is False) and (im.colorbar is not None):
            im.colorbar.outline.set_visible(False)

    else:
        for i, fax in enumerate(im.axs.flat):
            fax = add_features_map(
                data,
                fax,
                use_attrs,
                projection,
                features,
                geometries_kw,
                frame,
            )

            if sizes:
                # correct markersize for facetgrid
                scat = fax.collections[0]
                scat.set_sizes(pt_sizes[i])

        if (frame is False) and (im.cbar is not None):
            im.cbar.outline.set_visible(False)

        if show_time:
            if isinstance(show_time, bool):
                plot_coords(
                    None,
                    plot_data,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    None,
                    plot_data,
                    param="time",
                    loc=show_time,
                    backgroundalpha=1,
                )

    # size legend
    if sizes:
        legend_elements = size_legend_elements(
            np.resize(sdata.values[mask], (sdata.values[mask].size, 1)),
            np.resize(pt_sizes[mask], (pt_sizes[mask].size, 1)),
            max_entries=6,
            marker=plot_kw["marker"],
        )
        # legend spacing
        if size_range[1] > 200:
            ls = 0.5 + size_range[1] / 100 * 0.125
        else:
            ls = 0.5

        legend_kw = {
            "loc": "lower left",
            "facecolor": "w",
            "framealpha": 1,
            "edgecolor": "w",
            "labelspacing": ls,
            "handles": legend_elements,
            "bbox_to_anchor": (-0.05, -0.1),
        } | legend_kw

        if "title" not in legend_kw:
            if hasattr(sdata, "long_name"):
                lgd_title = wrap_text(
                    sdata.long_name, min_line_len=1, max_line_len=15
                )
                if hasattr(sdata, "units"):
                    lgd_title += f" ({sdata.units})"
            else:
                lgd_title = sizes
            legend_kw.setdefault("title", lgd_title)

        if ax:
            lgd = ax.legend(**legend_kw)
            lgd.set_zorder(11)
        else:
            im.figlegend = im.fig.legend(**legend_kw)
        # im._adjust_fig_for_guide(im.figlegend)

    if ax:
        return ax
    else:
        im.fig.suptitle(get_attributes("long_name", data))
        im.set_titles(template="{value}")
        if enumerate_subplots and isinstance(im, xr.plot.facetgrid.FacetGrid):
            for idx, ax in enumerate(im.axs.flat):
                ax.set_title(f"{string.ascii_lowercase[idx]}) {ax.get_title()}")

        return im


def taylordiagram(
    data: xr.DataArray | dict[str, xr.DataArray],
    plot_kw: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    std_range: tuple = (0, 1.5),
    contours: int | None = 4,
    contours_kw: dict[str, Any] | None = None,
    ref_std_line: bool = False,
    legend_kw: dict[str, Any] | None = None,
    std_label: str | None = None,
    corr_label: str | None = None,
    colors_key: str | None = None,
    markers_key: str | None = None,
):
    """
    Build a Taylor diagram.

    Based on the following code: https://gist.github.com/ycopin/3342888.

    Parameters
    ----------
    data : xr.DataArray or dict
        DataArray or dictionary of DataArrays created by xsdba.measures.taylordiagram, each corresponding
        to a point on the diagram. The dictionary keys will become their labels.
    plot_kw : dict, optional
        Arguments to pass to the `plot()` function. Changes how the markers look.
        If 'data' is a dictionary, must be a nested dictionary with the same keys as 'data'.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    std_range : tuple
        Range of the x and y axes, in units of the highest standard deviation in the data.
    contours : int, optional
        Number of rsme contours to plot.
    contours_kw : dict, optional
        Arguments to pass to `plt.contour()` for the rmse contours.
    ref_std_line : bool, optional
        If True, draws a circular line on radius `std = ref_std`. Default: False
    legend_kw : dict, optional
        Arguments to pass to `plt.legend()`.
    std_label : str, optional
        Label for the standard deviation (x and y) axes.
    corr_label : str, optional
        Label for the correlation axis.
    colors_key : str, optional
        Attribute or dimension of DataArrays used to separate DataArrays into groups with different colors. If present,
        it overrides the "color" key in `plot_kw`.
    markers_key : str, optional
        Attribute or dimension of DataArrays used to separate DataArrays into groups with different markers. If present,
        it overrides the "marker" key in `plot_kw`.

    Returns
    -------
    (plt.figure, mpl_toolkits.axisartist.floating_axes.FloatingSubplot, plt.legend)
    """
    plot_kw = empty_dict(plot_kw)
    fig_kw = empty_dict(fig_kw)
    contours_kw = empty_dict(contours_kw)
    legend_kw = empty_dict(legend_kw)

    # preserve order of dimensions if used for marker/color
    ordered_markers_type = None
    ordered_colors_type = None

    # convert SSP, RCP, CMIP formats in keys
    if isinstance(data, dict):
        data = process_keys(data, convert_scen_name)
    if isinstance(plot_kw, dict):
        plot_kw = process_keys(plot_kw, convert_scen_name)

    # if only one data input, insert in dict.
    if not isinstance(data, dict):
        data = {"_no_label": data}  # mpl excludes labels starting with "_" from legend
        plot_kw = {"_no_label": empty_dict(plot_kw)}
    elif not plot_kw:
        plot_kw = {k: {} for k in data.keys()}
    # check type
    for key, v in data.items():
        if not isinstance(v, xr.DataArray):
            raise TypeError("All objects in 'data' must be xarray DataArrays.")
        if "taylor_param" not in v.dims:
            raise ValueError("All DataArrays must contain a 'taylor_param' dimension.")
        if key == "reference":
            raise ValueError("'reference' is not allowed as a key in data.")

    # If there are other dimensions than 'taylor_param', create a bigger dict with them
    data_keys = list(data.keys())
    for data_key in data_keys:
        da = data[data_key]
        dims = list(set(da.dims) - {"taylor_param"})
        if dims != []:
            if markers_key in dims:
                ordered_markers_type = da[markers_key].values
            if colors_key in dims:
                ordered_colors_type = da[colors_key].values

            da = da.stack(pl_dims=dims)
            for i, dim_key in enumerate(da.pl_dims.values):
                if isinstance(dim_key, list) or isinstance(dim_key, tuple):
                    dim_key = "-".join([str(k) for k in dim_key])
                da0 = da.isel(pl_dims=i)
                # if colors_key/markers_key is a dimension, add it as an attribute for later use
                if markers_key in dims:
                    da0.attrs[markers_key] = da0[markers_key].values.item()
                if colors_key in dims:
                    da0.attrs[colors_key] = da0[colors_key].values.item()
                new_data_key = (
                    f"{data_key}-{dim_key}" if data_key != "_no_label" else dim_key
                )
                data[new_data_key] = da0
                plot_kw[new_data_key] = empty_dict(plot_kw[f"{data_key}"])
            data.pop(data_key)
            plot_kw.pop(data_key)

    # remove negative correlations
    initial_len = len(data)
    removed = [
        key for key, da in data.items() if da.sel(taylor_param="corr").values < 0
    ]
    data = {
        key: da for key, da in data.items() if da.sel(taylor_param="corr").values >= 0
    }
    if len(data) != initial_len:
        warnings.warn(
            f"{initial_len - len(data)} points with negative correlations will not be plotted: {', '.join(removed)}", stacklevel=2
        )

    # add missing keys to plot_kw
    for key in data.keys():
        if key not in plot_kw:
            plot_kw[key] = {}

    # extract ref to be used in plot
    ref_std = list(data.values())[0].sel(taylor_param="ref_std").values
    # check if ref is the same in all DataArrays and get the highest std (for ax limits)
    if len(data) > 1:
        for da in data.values():
            if da.sel(taylor_param="ref_std").values != ref_std:
                raise ValueError(
                    "All reference standard deviation values must be identical"
                )

    # get highest std for axis limits
    max_std = [ref_std]
    for da in data.values():
        max_std.extend(
            [
                max(
                    da.sel(taylor_param="ref_std").values,
                    da.sel(taylor_param="sim_std").values,
                ).astype(float)
            ]
        )

    # make labels
    if not std_label:
        try:
            units = list(data.values())[0].units
            std_label = get_localized_term("standard deviation")
            std_label = std_label if units == "" else f"{std_label} ({units})"
        except AttributeError:
            std_label = get_localized_term("standard deviation").capitalize()

    if not corr_label:
        try:
            if "Pearson" in list(data.values())[0].correlation_type:
                corr_label = get_localized_term("pearson correlation").capitalize()
            else:
                corr_label = get_localized_term("correlation").capitalize()
        except AttributeError:
            corr_label = get_localized_term("correlation").capitalize()

    # build diagram
    transform = PolarAxes.PolarTransform()

    # Setup the axis, here we map angles in degrees to angles in radius
    # Correlation labels
    rlocs = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])
    tlocs = np.arccos(rlocs)  # Conversion to polar angles
    gl1 = gf.FixedLocator(tlocs)  # Positions
    tf1 = gf.DictFormatter(dict(zip(tlocs, map(str, rlocs), strict=False)))
    # Standard deviation axis extent
    radius_min = std_range[0] * max(max_std)
    radius_max = std_range[1] * max(max_std)

    # Set up the axes range in the parameter "extremes"
    ghelper = GridHelperCurveLinear(
        transform,
        extremes=(0, np.pi / 2, radius_min, radius_max),
        grid_locator1=gl1,
        tick_formatter1=tf1,
    )

    fig = plt.figure(**fig_kw)
    floating_ax = FloatingSubplot(fig, 111, grid_helper=ghelper)
    fig.add_subplot(floating_ax)

    # Adjust axes
    floating_ax.axis["top"].set_axis_direction("bottom")  # "Angle axis"
    floating_ax.axis["top"].toggle(ticklabels=True, label=True)
    floating_ax.axis["top"].major_ticklabels.set_axis_direction("top")
    floating_ax.axis["top"].label.set_axis_direction("top")
    floating_ax.axis["top"].label.set_text(corr_label)

    floating_ax.axis["left"].set_axis_direction("bottom")  # "X axis"
    floating_ax.axis["left"].label.set_text(std_label)

    floating_ax.axis["right"].set_axis_direction("top")  # "Y axis"
    floating_ax.axis["right"].toggle(ticklabels=True, label=True)
    floating_ax.axis["right"].major_ticklabels.set_axis_direction("left")
    floating_ax.axis["right"].label.set_text(std_label)

    floating_ax.axis["bottom"].set_visible(False)  # Useless

    # Contours along standard deviations
    floating_ax.grid(visible=True, alpha=0.4)
    floating_ax.set_title("")

    ax = floating_ax.get_aux_axes(transform)  # return the axes that can be plotted on

    # plot reference
    if "reference" in plot_kw:
        ref_kw = plot_kw.pop("reference")
    else:
        ref_kw = {}
    ref_kw = {
        "color": "#154504",
        "marker": "s",
        "label": get_localized_term("reference"),
    } | ref_kw

    ref_pt = ax.scatter(0, ref_std, **ref_kw)

    points = [ref_pt]  # set up for later

    # plot a circular line along `ref_std`
    if ref_std_line:
        angles_for_line = np.linspace(0, np.pi / 2, 100)
        radii_for_line = np.full_like(angles_for_line, ref_std)
        ax.plot(
            angles_for_line,
            radii_for_line,
            color=ref_kw["color"],
            linewidth=0.5,
            linestyle="-",
        )

    # rmse contours from reference standard deviation
    if contours:
        radii, angles = np.meshgrid(
            np.linspace(radius_min, radius_max),
            np.linspace(0, np.pi / 2),
        )
        # Compute centered RMS difference
        rms = np.sqrt(ref_std**2 + radii**2 - 2 * ref_std * radii * np.cos(angles))

        contours_kw = {"linestyles": "--", "linewidths": 0.5} | contours_kw
        ct = ax.contour(angles, radii, rms, levels=contours, **contours_kw)

        ax.clabel(ct, ct.levels, fontsize=8)

        # points.append(ct_line)
        ct_line = ax.plot(
            [0],
            [0],
            ls=contours_kw["linestyles"],
            lw=1,
            c="k" if "colors" not in contours_kw else contours_kw["colors"],
            label="rmse",
        )
        points.append(ct_line[0])

    # get color options
    style_colors = matplotlib.rcParams["axes.prop_cycle"].by_key()["color"]
    if len(data) > len(style_colors):
        style_colors = style_colors * math.ceil(len(data) / len(style_colors))
    cat_colors = Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
    # get marker options (only used if `markers_key` is set)
    style_markers = "oDv^<>p*hH+x|_"
    if len(data) > len(style_markers):
        style_markers = style_markers * math.ceil(len(data) / len(style_markers))

    # set colors and markers styles based on discrimnating attributes (if specified)
    if colors_key or markers_key:
        if colors_key:
            # get_scen_color : look for SSP, RCP, CMIP model color
            colors_type = (
                ordered_colors_type
                if ordered_colors_type is not None
                else {da.attrs[colors_key] for da in data.values()}
            )
            colorsd = {
                k: get_scen_color(k, cat_colors) or style_colors[i]
                for i, k in enumerate(colors_type)
            }
        if markers_key:
            markers_type = (
                ordered_markers_type
                if ordered_markers_type is not None
                else {da.attrs[markers_key] for da in data.values()}
            )
            markersd = {k: style_markers[i] for i, k in enumerate(markers_type)}

        for key, da in data.items():
            if colors_key:
                plot_kw[key]["color"] = colorsd[da.attrs[colors_key]]
            if markers_key:
                plot_kw[key]["marker"] = markersd[da.attrs[markers_key]]

    # plot scatter
    for (key, da), i in zip(data.items(), range(len(data)), strict=False):
        # look for SSP, RCP, CMIP model color
        if colors_key is None:
            plot_kw[key].setdefault(
                "color", get_scen_color(key, cat_colors) or style_colors[i]
            )
        # set defaults
        plot_kw[key] = {"label": key} | plot_kw[key]

        # legend will be handled later in this case
        if markers_key or colors_key:
            plot_kw[key]["label"] = ""

        # plot
        pt = ax.scatter(
            np.arccos(da.sel(taylor_param="corr").values),
            da.sel(taylor_param="sim_std").values,
            **plot_kw[key],
        )
        points.append(pt)

    # legend
    legend_kw.setdefault("loc", "upper right")
    legend = fig.legend(points, [pt.get_label() for pt in points], **legend_kw)

    # plot new legend if markers/colors represent a certain dimension
    if colors_key or markers_key:
        handles = list(floating_ax.get_legend_handles_labels()[0])
        if markers_key:
            for k, m in markersd.items():
                handles.append(Line2D([0], [0], color="k", label=k, marker=m, ls=""))
        if colors_key:
            for k, c in colorsd.items():
                handles.append(Line2D([0], [0], color=c, label=k, ls="-"))
        legend.remove()
        legend = fig.legend(handles=handles, **legend_kw)

    return fig, floating_ax, legend


def hatchmap(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    projection: ccrs.Projection = ccrs.LambertConformal(),
    transform: ccrs.Projection | None = None,
    features: list[str] | dict[str, dict[str, Any]] | None = None,
    geometries_kw: dict[str, Any] | None = None,
    levels: int | None = None,
    legend_kw: dict[str, Any] | bool = True,
    show_time: bool | str | int | tuple[float, float] = False,
    frame: bool = False,
    enumerate_subplots: bool = False,
) -> matplotlib.axes.Axes:
    """
    Create map of hatches from 2D data.

    Parameters
    ----------
    data : dict, DataArray or Dataset
        Input data do plot.
    ax : matplotlib axis, optional
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs : dict, optional
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description'}.
        Only the keys found in the default dict can be used.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw:  dict, optional
        Arguments to pass to 'xarray.plot.contourf()' function.
        If 'data' is a dictionary, can be a nested dictionary with the same keys as 'data'.
    projection : ccrs.Projection
        The projection to use, taken from the cartopy.ccrs options. Ignored if ax is not None.
    transform : ccrs.Projection, optional
        Transform corresponding to the data coordinate system. If None, an attempt is made to find dimensions matching
        ccrs.PlateCarree() or ccrs.RotatedPole().
    features : list or dict, optional
        Features to use, as a list or a nested dict containing kwargs. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers', 'states'].
    geometries_kw : dict, optional
        Arguments passed to cartopy ax.add_geometry() which adds given geometries (GeoDataFrame geometry) to axis.
    legend_kw : dict or boolean, optional
        Arguments to pass to `ax.legend()`. No legend is added if legend_kw == False.
    show_time : bool, tuple, string or int.
        If True, show time (as date) at the bottom right of the figure.
        Can be a tuple of axis coordinates (0 to 1, as a fraction of the axis length) representing the location
        of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

        ==================   =============
        Location String      Location Code
        ==================   =============
        'upper right'        1
        'upper left'         2
        'lower left'         3
        'lower right'        4
        'right'              5
        'center left'        6
        'center right'       7
        'lower center'       8
        'upper center'       9
        'center'             10
        ==================   =============
    frame : bool
        Show or hide frame. Default False.
    enumerate_subplots: bool
        If True, enumerate subplots with letters.
        Only works with facetgrids (pass `col` or `row` in plot_kw).

    Returns
    -------
    matplotlib.axes.Axes
    """
    # default hatches
    dfh = [
        "/",
        "\\",
        "|",
        "-",
        "+",
        "x",
        "o",
        "O",
        ".",
        "*",
        "//",
        "\\\\",
        "||",
        "--",
        "++",
        "xx",
        "oo",
        "OO",
        "..",
        "**",
    ]

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)
    legend_kw = empty_dict(legend_kw)

    dattrs = None
    plot_data = {}

    # convert data to dict (if not one)
    if not isinstance(data, dict):
        if isinstance(data, xr.DataArray):
            plot_data = {data.name: data}
            if data.name not in plot_kw.keys():
                plot_kw = {data.name: plot_kw}
        elif isinstance(data, xr.Dataset):
            dattrs = data
            plot_data = {var: data[var] for var in data.data_vars}
            for v in plot_data.keys():
                if v not in plot_kw.keys():
                    plot_kw[v] = plot_kw
    else:
        for k, v in data.items():
            if k not in plot_kw.keys():
                plot_kw[k] = plot_kw
            if isinstance(v, xr.Dataset):
                dattrs = k
                plot_data[k] = v[list(v.data_vars)[0]]
                warnings.warn("Only first variable of Dataset is plotted.", stacklevel=2)
            else:
                plot_data[k] = v

    # setup transform from first data entry
    trdata = list(plot_data.values())[0]
    if transform is None:
        if "lat" in trdata.dims and "lon" in trdata.dims:
            transform = ccrs.PlateCarree()
        elif "rlat" in trdata.dims and "rlon" in trdata.dims:
            transform = get_rotpole(list(plot_data.values())[0])

    # bug xlim / ylim + transform in facetgrids
    # (see https://github.com/pydata/xarray/issues/8562#issuecomment-1865189766)
    if transform and (
        "xlim" in list(plot_kw.values())[0] and "ylim" in list(plot_kw.values())[0]
    ):
        extent = [
            list(plot_kw.values())[0]["xlim"][0],
            list(plot_kw.values())[0]["xlim"][1],
            list(plot_kw.values())[0]["ylim"][0],
            list(plot_kw.values())[0]["ylim"][1],
        ]
        [v.pop(lim) for lim in ["xlim", "ylim"] for v in plot_kw.values() if lim in v]

    elif transform and (
        "xlim" in list(plot_kw.values())[0] or "ylim" in list(plot_kw.values())[0]
    ):
        extent = None
        warnings.warn(
            "Requires both xlim and ylim with 'transform'. Xlim or ylim was dropped", stacklevel=2
        )
        [v.pop(lim) for lim in ["xlim", "ylim"] for v in plot_kw.values() if lim in v]

    else:
        extent = None

    # setup fig, ax
    if ax is None and (
        "row" not in list(plot_kw.values())[0].keys()
        and "col" not in list(plot_kw.values())[0].keys()
    ):
        fig, ax = plt.subplots(subplot_kw={"projection": projection}, **fig_kw)
    elif ax is not None and (
        "col" in list(plot_kw.values())[0].keys()
        or "row" in list(plot_kw.values())[0].keys()
    ):
        raise ValueError("Cannot use 'ax' and 'col'/'row' at the same time.")
    elif ax is None:
        [
            v.setdefault("subplot_kws", {}).setdefault("projection", projection)
            for v in plot_kw.values()
        ]
        cfig_kw = copy.deepcopy(fig_kw)
        if "figsize" in fig_kw:  # add figsize to plot_kw for facetgrid
            plot_kw[0].setdefault("figsize", fig_kw["figsize"])
            cfig_kw.pop("figsize")
        if cfig_kw:
            for v in plot_kw.values():
                {"subplots_kws": cfig_kw} | v
            warnings.warn(
                "Only figsize and figure.add_subplot() arguments can be passed to fig_kw when using facetgrid.", stacklevel=2
            )

    pat_leg = []
    n = 0
    for k, v in plot_data.items():
        # if levels plot multiple hatching from one data entry
        if "levels" in plot_kw[k] and len(plot_data) == 1:
            # nans
            mask = ~np.isnan(v.values)
            if np.sum(mask) < len(mask):
                warnings.warn(
                    f"{len(mask) - np.sum(mask)} nan values were dropped when plotting the pattern values", stacklevel=2
                )
            if "hatches" in plot_kw[k] and plot_kw[k]["levels"] != len(
                plot_kw[k]["hatches"]
            ):
                warnings.warn("Hatches number is not equivalent to number of levels", stacklevel=2)
                hatches = dfh[0:levels]
            if "hatches" not in plot_kw[k]:
                hatches = dfh[0:levels]

            plot_kw[k] = {
                "hatches": hatches,
                "colors": "none",
                "add_colorbar": False,
            } | plot_kw[k]

            if "lat" in v.dims:
                v.coords["mask"] = (("lat", "lon"), mask)
            else:
                v.coords["mask"] = (("rlat", "rlon"), mask)

            plot_kw[k].setdefault("transform", transform)
            if ax:
                plot_kw[k].setdefault("ax", ax)

            im = v.where(mask is not True).plot.contourf(**plot_kw[k])
            artists, labels = im.legend_elements(str_format="{:2.1f}".format)

            if ax and legend_kw:
                ax.legend(artists, labels, **legend_kw)
            elif legend_kw:
                im.figlegend = im.fig.legend(**legend_kw)

        elif len(plot_data) > 1 and "levels" in plot_kw[k]:
            raise TypeError(
                "To plot levels only one xr.DataArray or xr.Dataset accepted"
            )
        else:
            # since pattern remove colors and colorbar from plotting (done by gridmap)
            plot_kw[k] = {"colors": "none", "add_colorbar": False} | plot_kw[k]

            if "hatches" not in plot_kw[k].keys():
                plot_kw[k]["hatches"] = dfh[n]
                n += 1
            elif isinstance(
                plot_kw[k]["hatches"], str
            ):  # make sure the hatches are in a list
                warnings.warn(
                    "Hatches argument must be of type 'list'. Wrapping string argument as list.", stacklevel=2
                )
                plot_kw[k]["hatches"] = [plot_kw[k]["hatches"]]

            plot_kw[k].setdefault("transform", transform)
            if ax:
                im = v.plot.contourf(ax=ax, **plot_kw[k])

            if not ax:
                if k == list(plot_data.keys())[0]:
                    c_pkw = plot_kw[k].copy()
                    if "col" in plot_kw[k].keys() or "row" in plot_kw[k].keys():
                        if c_pkw["colors"] == "none":
                            c_pkw.pop("colors")
                        im = v.plot.contourf(**c_pkw)

                for i, fax in enumerate(im.axs.flat):
                    if (
                        k == list(plot_data.keys())[0]
                        and plot_kw[k]["colors"] == "none"
                    ):
                        fax.clear()
                    if len(plot_data) > 1:
                        # select data to plot from DataSet in loop to plot on facetgrids axis
                        c_pkw = plot_kw[k].copy()
                        c_pkw.pop("subplot_kws")
                        sel = {}
                        if "row" in c_pkw.keys():
                            sel[c_pkw["row"]] = i
                            c_pkw.pop("row")
                        elif "col" in c_pkw.keys():
                            sel[c_pkw["col"]] = i
                            c_pkw.pop("col")
                        v.isel(sel).plot.contourf(ax=fax, **c_pkw)

                    if k == list(plot_data.keys())[-1]:
                        add_features_map(
                            dattrs,
                            fax,
                            use_attrs,
                            projection,
                            features,
                            geometries_kw,
                            frame,
                        )
                        if extent:
                            fax.set_extent(extent)

            pat_leg.append(
                matplotlib.patches.Patch(
                    hatch=plot_kw[k]["hatches"][0], fill=False, label=k
                )
            )

    if pat_leg and legend_kw:
        legend_kw = {
            "loc": "lower right",
            "handleheight": 2,
            "handlelength": 4,
        } | legend_kw

        if ax and legend_kw:
            ax.legend(handles=pat_leg, **legend_kw)
        elif legend_kw:
            im.figlegend = im.fig.legend(handles=pat_leg, **legend_kw)

    # add features
    if ax:
        if extent:
            ax.set_extent(extent)
        if dattrs:
            use_attrs.setdefault("title", "description")

        ax = add_features_map(
            dattrs,
            ax,
            use_attrs,
            projection,
            features,
            geometries_kw,
            frame,
        )

        if show_time:
            if isinstance(show_time, bool):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    ax,
                    plot_data,
                    param="time",
                    loc=show_time,
                    backgroundalpha=1,
                )

        # when im is an ax, it has a colorbar attribute. If it is a facetgrid, it has a cbar attribute.
        if (frame is False) and (
            (getattr(im, "colorbar", None) is not None)
            or (getattr(im, "cbar", None) is not None)
        ):
            im.colorbar.outline.set_visible(False)

            set_plot_attrs(use_attrs, dattrs, ax, wrap_kw={"max_line_len": 60})
        return ax

    else:
        # when im is an ax, it has a colorbar attribute. If it is a facetgrid, it has a cbar attribute.
        if (frame is False) and (
            (getattr(im, "colorbar", None) is not None)
            or (getattr(im, "cbar", None) is not None)
        ):
            im.cbar.outline.set_visible(False)

        if show_time:
            if show_time is True:
                plot_coords(
                    None,
                    dattrs,
                    param="time",
                    loc="lower right",
                    backgroundalpha=1,
                )
            elif isinstance(show_time, str | tuple | int):
                plot_coords(
                    None, dattrs, param="time", loc=show_time, backgroundalpha=1
                )
        if dattrs:
            use_attrs.setdefault("suptitle", "long_name")
            set_plot_attrs(use_attrs, dattrs, facetgrid=im)

        if enumerate_subplots and isinstance(im, xr.plot.facetgrid.FacetGrid):
            for idx, ax in enumerate(im.axs.flat):
                ax.set_title(f"{string.ascii_lowercase[idx]}) {ax.get_title()}")

        return im


def _add_lead_time_coord(da, ref):
    """Add a lead time coordinate to the data. Modifies da in-place."""
    lead_time = da.time.dt.year - int(ref)
    da["Lead time"] = lead_time
    da["Lead time"].attrs["units"] = f"years from {ref}"
    return lead_time


def partition(
    data: xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    start_year: str | None = None,
    show_num: bool = True,
    fill_kw: dict[str, Any] | None = None,
    line_kw: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    legend_kw: dict[str, Any] | None = None,
) -> matplotlib.axes.Axes:
    """
    Figure of the partition of total uncertainty by components.

    Uncertainty fractions can be computed with xclim (https://xclim.readthedocs.io/en/stable/api.html#uncertainty-partitioning).
    Make sure the use `fraction=True` in the xclim function call.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Variance over time of the different components of uncertainty.
        Output of a `xclim.ensembles._partitioning` function.
    ax : matplotlib axis, optional
        Matplotlib axis on which to plot.
    start_year : str
        If None, the x-axis will be the time in year.
        If str, the x-axis will show the number of year since start_year.
    show_num : bool
        If True, show the number of elements for each uncertainty components in parentheses in the legend.
        `data` should have attributes named after the components with a list of its the elements.
    fill_kw : dict
        Keyword arguments passed to `ax.fill_between`.
        It is possible to pass a dictionary of keywords for each component (uncertainty coordinates).
    line_kw : dict
        Keyword arguments passed to `ax.plot` for the lines in between the components.
        The default is {color="k", lw=2}. We recommend always using lw>=2.
    fig_kw : dict
        Keyword arguments passed to `plt.subplots`.
    legend_kw : dict
        Keyword arguments passed to `ax.legend`.

    Returns
    -------
    mpl.axes.Axes
    """
    if isinstance(data, xr.Dataset):
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        data = data[list(data.keys())[0]].squeeze()

    if data.attrs["units"] != "%":
        raise ValueError(
            "The units are not %. Use `fraction=True` in the xclim function call."
        )

    fill_kw = empty_dict(fill_kw)
    line_kw = empty_dict(line_kw)
    fig_kw = empty_dict(fig_kw)
    legend_kw = empty_dict(legend_kw)

    # select data to plot
    if isinstance(data, xr.DataArray):
        data = data.squeeze()
    elif isinstance(data, xr.Dataset):  # in case, it was saved to disk before plotting.
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        data = data[list(data.keys())[0]].squeeze()
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    if ax is None:
        fig, ax = plt.subplots(**fig_kw)

    # Select data from reference year onward
    if start_year:
        data = data.sel(time=slice(start_year, None))

        # Lead time coordinate
        time = _add_lead_time_coord(data, start_year)
        ax.set_xlabel(f"Lead time (years from {start_year})")
    else:
        time = data.time.dt.year

    # fill_kw that are direct (not with uncertainty as key)
    fk_direct = {k: v for k, v in fill_kw.items() if (k not in data.uncertainty.values)}

    # Draw areas
    past_y = 0
    black_lines = []
    for u in data.uncertainty.values:
        if u not in ["total", "variability"]:
            present_y = past_y + data.sel(uncertainty=u)
            num = len(data.attrs.get(u, []))  # compatible with pre PR PR #1529
            label = f"{u} ({num})" if show_num and num else u
            ax.fill_between(
                time,
                past_y,
                present_y,
                label=label,
                **fill_kw.get(u, fk_direct),
            )
            black_lines.append(present_y)
            past_y = present_y
    ax.fill_between(
        time,
        past_y,
        100,
        label="variability",
        **fill_kw.get("variability", fk_direct),
    )

    # Draw black lines
    line_kw.setdefault("color", "k")
    line_kw.setdefault("lw", 2)
    ax.plot(time, np.array(black_lines).T, **line_kw)

    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(20))
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n=5))

    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(10))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(n=2))

    ax.set_ylabel(f"{data.attrs['long_name']} ({data.attrs['units']})")  #

    ax.set_ylim(0, 100)
    ax.legend(**legend_kw)

    return ax


def triheatmap(
    data: xr.DataArray | xr.Dataset,
    z: str,
    ax: matplotlib.axes.Axes | None = None,
    use_attrs: dict[str, Any] | None = None,
    fig_kw: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None | list = None,
    cmap: str | matplotlib.colors.Colormap | None = None,
    divergent: bool | int | float = False,
    cbar: bool | str = "unique",
    cbar_kw: dict[str, Any] | None | list = None,
) -> matplotlib.axes.Axes:
    """
    Create a triangle heatmap from a DataArray.

    Note that most of the code comes from:
    https://stackoverflow.com/questions/66048529/how-to-create-a-heatmap-where-each-cell-is-divided-into-4-triangles

    Parameters
    ----------
    data : DataArray or Dataset
        Input data do plot.
    z: str
        Dimension to plot on the triangles. Its length should be 2 or 4.
    ax : matplotlib axis, optional
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs : dict, optional
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'cbar_label': 'long_name',"cbar_units": "units"}.
        Valid keys are: 'title', 'xlabel', 'ylabel', 'cbar_label', 'cbar_units'.
    fig_kw : dict, optional
        Arguments to pass to `plt.figure()`.
    plot_kw :  dict, optional
        Arguments to pass to the 'plt.tripcolor()' function.
        It can be a list of dictionaries to pass different arguments to each type of triangles (upper/lower or north/east/south/west).
    cmap : matplotlib.colors.Colormap or str, optional
        Colormap to use. If str, can be a matplotlib or name of the file of an IPCC colormap (see data/ipcc_colors).
        If None, look for common variables (from data/ipcc_colors/variables_groups.json) in the name of the DataArray
        or its 'history' attribute and use corresponding colormap, aligned with the IPCC Visual Style Guide 2022
        (https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf).
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
    cbar : {False, True, 'unique', 'each'}
        If False, don't show the colorbar.
        If True or 'unique', show a unique colorbar for all triangle types. (The cbar of the first triangle is used).
        If 'each', show a colorbar for each triangle type.
    cbar_kw : dict or list
        Arguments to pass to 'fig.colorbar()'.
        It can be a list of dictionaries to pass different arguments to each type of triangles (upper/lower or north/east/south/west).

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    fig_kw = empty_dict(fig_kw)
    plot_kw = empty_dict(plot_kw)
    cbar_kw = empty_dict(cbar_kw)

    # select data to plot
    if isinstance(data, xr.DataArray):
        da = data
    elif isinstance(data, xr.Dataset):
        if len(data.data_vars) > 1:
            warnings.warn(
                "data is xr.Dataset; only the first variable will be used in plot", stacklevel=2
            )
        da = list(data.values())[0]
    else:
        raise TypeError("`data` must contain a xr.DataArray or xr.Dataset")

    # setup fig, axis
    if ax is None:
        fig, ax = plt.subplots(**fig_kw)

    # colormap
    if isinstance(cmap, str):
        if cmap not in plt.colormaps():
            try:
                cmap = create_cmap(filename=cmap)
            except FileNotFoundError:
                pass
                logging.log("Colormap not found. Using default.")

    elif cmap is None:
        cmap = create_cmap(
            get_var_group(da=da),
            divergent=divergent,
        )

    # prep data
    d = [da.sel(**{z: v}).values for v in da[z].values]

    other_dims = [di for di in da.dims if di != z]
    if len(other_dims) > 2:
        warnings.warn(
            "More than 3 dimensions in data. The first two after dim will be used as the dimensions of the heatmap.", stacklevel=2
        )
    if len(other_dims) < 2:
        raise ValueError(
            "Data must have 3 dimensions. If you only have 2 dimensions, use fg.heatmap."
        )

    if plot_kw == {} and cbar in ["unique", True]:
        warnings.warn(
            'With cbar="unique" only the colorbar of the first triangle'
            " will be shown. No `plot_kw` was passed. vmin and vmax will be set the max"
            " and min of data.", stacklevel=2
        )
        plot_kw = {"vmax": da.max().values, "vmin": da.min().values}

    if isinstance(plot_kw, dict):
        plot_kw.setdefault("cmap", cmap)
        plot_kw.setdefault("ec", "white")
        plot_kw = [plot_kw for _ in range(len(d))]

    labels_x = da[other_dims[0]].values
    labels_y = da[other_dims[1]].values
    m, n = d[0].shape[0], d[0].shape[1]

    # plot
    if len(d) == 2:
        x = np.arange(m + 1)
        y = np.arange(n + 1)
        xss, ys = np.meshgrid(x, y)
        (xss * ys) % 10
        triangles1 = [
            (i + j * (m + 1), i + 1 + j * (m + 1), i + (j + 1) * (m + 1))
            for j in range(n)
            for i in range(m)
        ]
        triangles2 = [
            (
                i + 1 + j * (m + 1),
                i + 1 + (j + 1) * (m + 1),
                i + (j + 1) * (m + 1),
            )
            for j in range(n)
            for i in range(m)
        ]
        triang1 = Triangulation(xss.ravel(), ys.ravel(), triangles1)
        triang2 = Triangulation(xss.ravel(), ys.ravel(), triangles2)
        triangul = [triang1, triang2]

        imgs = [
            ax.tripcolor(t, np.ravel(val), **plotkw)
            for t, val, plotkw in zip(triangul, d, plot_kw, strict=False)
        ]

        ax.set_xticks(np.array(range(m)) + 0.5, labels=labels_x, rotation=45)
        ax.set_yticks(np.array(range(n)) + 0.5, labels=labels_y, rotation=90)

    elif len(d) == 4:
        xv, yv = np.meshgrid(
            np.arange(-0.5, m), np.arange(-0.5, n)
        )  # vertices of the little squares
        xc, yc = np.meshgrid(
            np.arange(0, m), np.arange(0, n)
        )  # centers of the little squares
        x = np.concatenate([xv.ravel(), xc.ravel()])
        y = np.concatenate([yv.ravel(), yc.ravel()])
        cstart = (m + 1) * (n + 1)  # indices of the centers

        triangles_n = [
            (i + j * (m + 1), i + 1 + j * (m + 1), cstart + i + j * m)
            for j in range(n)
            for i in range(m)
        ]
        triangles_e = [
            (i + 1 + j * (m + 1), i + 1 + (j + 1) * (m + 1), cstart + i + j * m)
            for j in range(n)
            for i in range(m)
        ]
        triangles_s = [
            (
                i + 1 + (j + 1) * (m + 1),
                i + (j + 1) * (m + 1),
                cstart + i + j * m,
            )
            for j in range(n)
            for i in range(m)
        ]
        triangles_w = [
            (i + (j + 1) * (m + 1), i + j * (m + 1), cstart + i + j * m)
            for j in range(n)
            for i in range(m)
        ]
        triangul = [
            Triangulation(x, y, triangles)
            for triangles in [
                triangles_n,
                triangles_e,
                triangles_s,
                triangles_w,
            ]
        ]

        imgs = [
            ax.tripcolor(t, np.ravel(val), **plotkw)
            for t, val, plotkw in zip(triangul, d, plot_kw, strict=False)
        ]
        ax.set_xticks(np.array(range(m)), labels=labels_x, rotation=45)
        ax.set_yticks(np.array(range(n)), labels=labels_y, rotation=90)

    else:
        raise ValueError(
            f"The length of the dimensiondim ({z},{len(d)}) should be either 2 or 4. It represents the number of triangles."
        )

    ax.set_title(get_attributes(use_attrs.get("title", None), data))
    ax.set_xlabel(other_dims[0])
    ax.set_ylabel(other_dims[1])
    if "xlabel" in use_attrs:
        ax.set_xlabel(get_attributes(use_attrs["xlabel"], data))
    if "ylabel" in use_attrs:
        ax.set_ylabel(get_attributes(use_attrs["ylabel"], data))
    ax.set_aspect("equal", "box")
    ax.invert_yaxis()
    ax.tick_params(left=False, bottom=False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # create cbar label
    # set default use_attrs values
    use_attrs.setdefault("cbar_label", "long_name")
    use_attrs.setdefault("cbar_units", "units")
    if (
        "cbar_units" in use_attrs
        and len(get_attributes(use_attrs["cbar_units"], data)) >= 1
    ):  # avoids '()' as label
        cbar_label = (
            get_attributes(use_attrs["cbar_label"], data)
            + " ("
            + get_attributes(use_attrs["cbar_units"], data)
            + ")"
        )
    else:
        cbar_label = get_attributes(use_attrs["cbar_label"], data)

    if isinstance(cbar_kw, dict):
        cbar_kw.setdefault("label", cbar_label)
        cbar_kw = [cbar_kw for _ in range(len(d))]
    if cbar == "unique":
        plt.colorbar(imgs[0], ax=ax, **cbar_kw[0])

    elif (cbar == "each") or (cbar is True):
        for i in reversed(range(len(d))):  # switch order of colour bars
            plt.colorbar(imgs[i], ax=ax, **cbar_kw[i])

    return ax
