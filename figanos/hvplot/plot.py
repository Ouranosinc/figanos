"""Hvplot figanos plotting functions."""

import warnings
from pathlib import Path
from typing import Any

import holoviews as hv
import hvplot  # noqa: F401
import hvplot.xarray  # noqa: F401
import xarray as xr

from figanos.matplotlib.utils import (
    check_timeindex,
    convert_scen_name,
    empty_dict,
    fill_between_label,
    get_array_categ,
    get_scen_color,
    process_keys,
    sort_lines,
)

from .utils import defaults_curves, get_all_values, get_glyph_param


def _plot_ens_reals(
    name: str,
    array_categ: dict[str, str],
    arr: xr.DataArray,
    non_dict_data: bool,
    cplot_kw: dict[str, Any],
    copts_kw: dict[str, Any] | list,
) -> dict:
    """Plot realizations ensembles"""
    hv_fig = {}
    if array_categ[name] == "ENS_REALS_DS":
        if len(arr.data_vars) >= 2:
            raise TypeError(
                "To plot multiple ensembles containing realizations, use DataArrays outside a Dataset"
            )
        else:
            arr = arr[list(arr.data_vars)[0]]

    if non_dict_data is True:
        if not (
            "groupby" in cplot_kw[name].keys()
            and cplot_kw[name]["groupby"] == "realization"
        ):
            cplot_kw[name] = {"by": "realization", "x": "time"} | cplot_kw[name]
        cplot_kw[name] = {"by": "realization", "x": "time"} | cplot_kw[name]
        return arr.hvplot.line(**cplot_kw[name]).opts(**copts_kw)
    else:
        cplot_kw[name].setdefault("label", name)
        for r in arr.realization:
            hv_fig[f"realization_{r.values.item()}"] = (
                arr.sel(realization=r).hvplot.line(**cplot_kw[name]).opts(**copts_kw)
            )
        return hv_fig


def _plot_ens_pct_stats(
    name: str,
    arr: xr.DataArray,
    array_categ: dict[str, str],
    array_data: dict[str, xr.DataArray],
    cplot_kw: dict[str, Any],
    copts_kw: dict[str, Any],
    legend: str,
    sub_name: str | None = None,
) -> dict:
    """Plot ensembles with percentiles and statistics (min/moy/max)"""
    hv_fig = {}

    # create a dictionary labeling the middle, upper and lower line
    sorted_lines = sort_lines(array_data)

    # which label to use
    if sub_name:
        lab = sub_name
    else:
        lab = name

    # plot
    hv_fig["line"] = (
        array_data[sorted_lines["middle"]]
        .hvplot.line(label=lab, **cplot_kw[name])
        .opts(**copts_kw)
    )
    c = get_glyph_param(hv_fig["line"], "line_color")
    lab_area = fill_between_label(sorted_lines, name, array_categ, legend)
    cplot_kw[name].setdefault("color", c)
    if "ENS_PCT_DIM" in array_categ[name]:
        arr = arr.to_dataset(dim="percentiles")
        arr = arr.rename({k: str(k) for k in arr.keys()})
    hv_fig["area"] = arr.hvplot.area(
        y=sorted_lines["lower"],
        y2=sorted_lines["upper"],
        label=lab_area,
        line_color=None,
        alpha=0.2,
        **cplot_kw[name],
    ).opts(**copts_kw)
    return hv_fig


def _plot_timeseries(
    name: str,
    arr: xr.DataArray | xr.Dataset,
    array_categ: dict[str, str],
    cplot_kw: dict[str, Any],
    copts_kw: dict[str, Any],
    non_dict_data: bool,
    legend: str,
) -> dict | hv.element.chart.Curve | hv.core.overlay.Overlay:
    """Plot time series from 1D Xarray Datasets or DataArrays as line plots."""
    hv_fig = {}

    if (
        array_categ[name] == "ENS_REALS_DA" or array_categ[name] == "ENS_REALS_DS"
    ):  # ensemble with 'realization' dim, as DataArray or Dataset
        return _plot_ens_reals(
            name, array_categ, arr, non_dict_data, cplot_kw, copts_kw
        )
    elif (
        array_categ[name] == "ENS_PCT_DIM_DS"
    ):  # ensemble percentiles stored as dimension coordinates, DataSet
        for k, sub_arr in arr.data_vars.items():
            sub_name = (
                sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)
            )
            hv_fig[sub_name] = {}
            # extract each percentile array from the dims
            array_data = {}
            for pct in sub_arr.percentiles.values:
                array_data[str(pct)] = sub_arr.sel(percentiles=pct)

            hv_fig[sub_name] = _plot_ens_pct_stats(
                name,
                sub_arr,
                array_categ,
                array_data,
                cplot_kw,
                copts_kw,
                legend,
                sub_name,
            )
    elif array_categ[name] in [
        "ENS_PCT_VAR_DS",  # ensemble statistics (min, mean, max) stored as variables
        "ENS_STATS_VAR_DS",  # ensemble percentiles stored as variables
        "ENS_PCT_DIM_DA",  # ensemble percentiles stored as dimension coordinates, DataArray
    ]:
        # extract each array from the datasets
        array_data = {}
        if array_categ[name] == "ENS_PCT_DIM_DA":
            for pct in arr.percentiles:
                array_data[str(int(pct))] = arr.sel(percentiles=int(pct))
        else:
            for k, v in arr.data_vars.items():
                array_data[k] = v

        return _plot_ens_pct_stats(
            name, arr, array_categ, array_data, cplot_kw, copts_kw, legend
        )
        #  non-ensemble Datasets
    elif array_categ[name] == "DS":
        ignore_label = False
        for k, sub_arr in arr.data_vars.items():
            sub_name = (
                sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)
            )
            #  if kwargs are specified by user, all lines are the same and we want one legend entry
            if cplot_kw[name]:
                label = name if not ignore_label else ""
                ignore_label = True
            else:
                label = sub_name

            hv_fig[sub_name] = sub_arr.hvplot.line(
                x="time", label=label, **cplot_kw[name]
            ).opts(**copts_kw[name])

        #  non-ensemble DataArrays
    elif array_categ[name] in ["DA"]:
        return arr.hvplot.line(label=name, **cplot_kw[name]).opts(**copts_kw[name])
    else:
        raise ValueError(
            "Data structure not supported"
        )  # can probably be removed along with elif logic above,
        # given that get_array_categ() also does this check
    if hv_fig:
        return hv_fig


def timeseries(
    data: dict[str, Any] | xr.DataArray | xr.Dataset,
    use_attrs: dict[str, Any] | None = None,
    plot_kw: dict[str, Any] | None = None,
    opts_kw: dict[str, Any] | None = None,
    legend: str = "lines",
    show_lat_lon: bool | str | int | tuple[float, float] = True,
) -> hv.element.chart.Curve | hv.core.overlay.Overlay:
    """Plot time series from 1D Xarray Datasets or DataArrays as line plots.

    Parameters
    ----------
    data : dict or Dataset/DataArray
        Input data to plot. It can be a DataArray, Dataset or a dictionary of DataArrays and/or Datasets.
    use_attrs : dict, optional
        A dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'ylabel': 'long_name', 'yunits': 'units'}.
        Only the keys found in the default dict can be used.
    plot_kw : dict, optional
        Arguments to pass to the `hvplot.line()` or hvplot.area() function. Changes how the line looks.
        If 'data' is a dictionary, must be a nested dictionary with the same keys as 'data'.
    legend : str (default 'lines') or dict
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines),
         'edge' (out of plot), 'none' (no legend).
    show_lat_lon : bool, tuple, str or int
        If True, show latitude and longitude at the bottom right of the figure.
        Can be a tuple of axis coordinates (from 0 to 1, as a fraction of the axis length) representing
        the location of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

    Returns
    -------
        hvplot.Overlay

    """
    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    copts_kw = empty_dict(opts_kw)
    cplot_kw = empty_dict(plot_kw)

    # convert SSP, RCP, CMIP formats in keys
    if isinstance(data, dict):
        data = process_keys(data, convert_scen_name)
    if isinstance(plot_kw, dict):
        cplot_kw = process_keys(cplot_kw, convert_scen_name)

    # add ouranos default cycler colors
    defaults_curves()

    # if only one data input, insert in dict.
    non_dict_data = False
    if not isinstance(data, dict):
        non_dict_data = True
        data = {"_no_label": data}  # mpl excludes labels starting with "_" from legend
        cplot_kw = {"_no_label": cplot_kw}

    # assign keys to plot_kw if not there
    if non_dict_data is False:
        for name in data:
            if name not in cplot_kw:
                cplot_kw[name] = {}
                warnings.warn(
                    f"Key {name} not found in plot_kw. Using empty dict instead."
                )
        for key in cplot_kw:
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

    # add use attributes defaults ToDo: Adapt use_attrs to hvplot (already an option in hvplot with xarray)
    use_attrs = {
        "title": "description",
        "ylabel": "long_name",
        "yunits": "units",
    } | use_attrs

    # dict of array 'categories'
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # dictionary of hvplots plots
    figs = {}

    # get data and plot
    for name, arr in data.items():
        # ToDo: Add user_attrs here and grey backgrounds lines
        # ToDo: if legend = 'edge' add hook in opts_kw

        #  remove 'label' to avoid error due to double 'label' args
        if "label" in cplot_kw[name]:
            del cplot_kw[name]["label"]
            warnings.warn(f'"label" entry in plot_kw[{name}] will be ignored.')

        # SSP, RCP, CMIP model colors
        cat_colors = (
            Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
        )
        if get_scen_color(name, cat_colors):
            cplot_kw[name].setdefault("color", get_scen_color(name, cat_colors))

        figs[name] = _plot_timeseries(
            name, arr, array_categ, cplot_kw, copts_kw, non_dict_data, legend
        )

    if not legend:
        return hv.Overlay(list(get_all_values(figs))).opts(show_legend=False)
    else:
        return hv.Overlay(list(get_all_values(figs)))
