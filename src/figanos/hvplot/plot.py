"""Hvplot figanos plotting functions."""

import copy
import warnings
from functools import partial
from pathlib import Path
from typing import Any

import holoviews as hv
import hvplot  # noqa: F401
import hvplot.xarray  # noqa: F401
import xarray as xr

from figanos.matplotlib.utils import (
    check_timeindex,
    fill_between_label,
    get_array_categ,
    get_scen_color,
    sort_lines,
)

from .utils import (
    add_default_opts_overlay,
    create_dict_timeseries,
    curve_hover_hook,
    curve_hover_tool,
    defaults_curves,
    formatters_data,
    get_all_values,
    get_glyph_param,
    set_plot_attrs_hv,
    x_timeseries,
)


def _plot_ens_reals(
    name: str,
    array_categ: dict[str, str],
    arr: xr.DataArray,
    non_dict_data: bool,
    plot_kw: dict[str, Any],
    opts_kw: dict[str, Any] | list,
    form: str,
    use_attrs: dict[str, Any],
) -> dict:
    """Plot realizations ensembles."""
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
            "groupby" in plot_kw[name].keys()
            and plot_kw[name]["groupby"] == "realization"
        ):
            plot_kw[name] = {"by": "realization", "x": "time"} | plot_kw[
                name
            ]  # why did i put this two times?
        plot_kw[name] = {"by": "realization", "x": "time"} | plot_kw[name]
        opts_kw[name].setdefault(
            "hooks",
            [
                partial(
                    curve_hover_hook,
                    att=use_attrs,
                    form=form,
                    x=list(plot_kw.values())[-1]["x"],
                )
            ],
        )
        return arr.hvplot.line(**plot_kw[name]).opts(**opts_kw[name])
    else:
        plot_kw[name].setdefault("label", name)
        # opts_kw[name].setdefault("hooks", [
        #  partial(curve_hover_hook, att=use_attrs, form=form, x=list(plot_kw.values())[-1]["x"])])
        for r in arr.realization:
            hv_fig[f"realization_{r.values.item()}"] = (
                arr.sel(realization=r)
                .hvplot.line(hover=False, **plot_kw[name])
                .opts(
                    tools=curve_hover_tool(use_attrs, form, r=r.values.item()),
                    **opts_kw[name],
                )
            )
        return hv_fig


def _plot_ens_pct_stats(
    name: str,
    arr: xr.DataArray,
    array_categ: dict[str, str],
    array_data: dict[str, xr.DataArray],
    plot_kw: dict[str, Any],
    opts_kw: dict[str, Any],
    legend: str,
    form: str,
    use_attrs: dict[str, Any],
    sub_name: str | None = None,
) -> dict:
    """Plot ensembles with percentiles and statistics (min/moy/max)."""
    hv_fig = {}

    # create a dictionary labeling the middle, upper and lower line
    sorted_lines = sort_lines(array_data)

    # which label to use
    if sub_name:
        lab = sub_name
    else:
        lab = name

    plot_kw_line = copy.deepcopy(plot_kw[name])
    plot_kw_line = {"label": lab, "hover": False} | plot_kw_line
    # plot
    hv_fig["line"] = (
        array_data[sorted_lines["middle"]]
        .hvplot.line(**plot_kw_line)
        .opts(**opts_kw[name])
    )

    c = get_glyph_param(hv_fig["line"], "line_color")
    lab_area = fill_between_label(sorted_lines, name, array_categ, legend)
    opts_kw_area = copy.deepcopy(opts_kw[name])
    opts_kw_area.setdefault("tools", curve_hover_tool(use_attrs, form))
    plot_kw[name].setdefault("color", c)
    if "ENS_PCT_DIM" in array_categ[name]:
        arr = arr.to_dataset(dim="percentiles")
        arr = arr.rename({k: str(k) for k in arr.keys()})
    hv_fig["area"] = arr.hvplot.area(
        y=sorted_lines["lower"],
        y2=sorted_lines["upper"],
        label=lab_area,
        line_color=None,
        alpha=0.2,
        **plot_kw[name],
    ).opts(**opts_kw_area)
    return hv_fig


def _plot_timeseries(
    name: str,
    arr: xr.DataArray | xr.Dataset,
    array_categ: dict[str, str],
    plot_kw: dict[str, Any],
    opts_kw: dict[str, Any],
    non_dict_data: bool,
    legend: str,
    form: str,
    use_attrs: dict[str, Any],
) -> dict | hv.element.chart.Curve | hv.core.overlay.Overlay:
    """Plot time series from 1D Xarray Datasets or DataArrays as line plots."""
    hv_fig = {}

    if (
        array_categ[name] == "ENS_REALS_DA" or array_categ[name] == "ENS_REALS_DS"
    ):  # ensemble with 'realization' dim, as DataArray or Dataset
        return _plot_ens_reals(
            name,
            array_categ,
            arr,
            non_dict_data,
            plot_kw,
            opts_kw,
            form,
            use_attrs,
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
                plot_kw,
                opts_kw,
                legend,
                form,
                use_attrs,
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
            name,
            arr,
            array_categ,
            array_data,
            plot_kw,
            opts_kw,
            legend,
            form,
            use_attrs,
        )
        #  non-ensemble Datasets
    elif array_categ[name] == "DS":
        ignore_label = False
        for k, sub_arr in arr.data_vars.items():
            sub_name = (
                sub_arr.name if non_dict_data is True else (name + "_" + sub_arr.name)
            )
            #  if kwargs are specified by user, all lines are the same and we want one legend entry
            if plot_kw[name]:
                label = name if not ignore_label else ""
                ignore_label = True
            else:
                label = sub_name
            hv_fig[sub_name] = sub_arr.hvplot.line(
                x="time", label=label, **plot_kw[name]
            ).opts(**opts_kw[name])

        #  non-ensemble DataArrays
    elif array_categ[name] in ["DA"]:
        return arr.hvplot.line(label=name, **plot_kw[name]).opts(**opts_kw[name])
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
    opts_kw: dict, optional
        Arguments to pass to the `holoviews/hvplot.opts()` function. Changes figure options and access to hooks.
        If 'data' is a dictionary, must be a nested dictionary with the same keys as 'data' to pass nested to each
        individual figure or key 'overlay' to pass to overlayed figures.
    legend : str (default 'lines') or dict
        'full' (lines and shading), 'lines' (lines only), 'in_plot' (end of lines), 'none' (no legend).
    show_lat_lon : bool, tuple, str or int
        If True, show latitude and longitude at the bottom right of the figure.
        Can be a tuple of axis coordinates (from 0 to 1, as a fraction of the axis length) representing
        the location of the text. If a string or an int, the same values as those of the 'loc' parameter
        of matplotlib's legends are accepted.

    Returns
    -------
        hvplot.Overlay
    """
    # timeseries dict/data
    use_attrs, data, plot_kw, opts_kw, non_dict_data = create_dict_timeseries(
        use_attrs, data, plot_kw, opts_kw
    )

    # add ouranos default cycler colors
    defaults_curves()

    # assign keys to plot_kw if not there
    if non_dict_data is False:
        for name in data:
            if name not in plot_kw:
                plot_kw[name] = {}
                warnings.warn(
                    f"Key {name} not found in plot_kw. Using empty dict instead."
                )
            if name not in opts_kw:
                opts_kw[name] = {}
                warnings.warn(
                    f"Key {name} not found in opts_kw. Using empty dict instead."
                )
        for key in plot_kw:
            # add "x" to plot_kw if not there
            x_timeseries(data[key], plot_kw[key])
            if key not in data:
                raise KeyError(
                    'plot_kw must be a nested dictionary with keys corresponding to the keys in "data"'
                )
    else:
        x_timeseries(data["_no_label"], plot_kw["_no_label"])

    # check: type
    for name, arr in data.items():
        if not isinstance(arr, (xr.Dataset, xr.DataArray)):
            raise TypeError(
                '"data" must be a xr.Dataset, a xr.DataArray or a dictionary of such objects.'
            )

    # check: 'time' dimension and calendar format
    data = check_timeindex(data)

    # add use attributes defaults
    use_attrs, plot_kw = set_plot_attrs_hv(use_attrs, list(data.values())[-1], plot_kw)

    # dict of array 'categories'
    array_categ = {name: get_array_categ(array) for name, array in data.items()}

    # formatters for data
    form = formatters_data(data)

    # dictionary of hvplots plots
    figs = {}

    # get data and plot
    for name, arr in data.items():
        #  remove 'label' to avoid error due to double 'label' args
        if "label" in plot_kw[name]:
            del plot_kw[name]["label"]
            warnings.warn(f'"label" entry in plot_kw[{name}] will be ignored.')

        # SSP, RCP, CMIP model colors
        cat_colors = (
            Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
        )
        if get_scen_color(name, cat_colors):
            plot_kw[name].setdefault("color", get_scen_color(name, cat_colors))

        figs[name] = _plot_timeseries(
            name,
            arr,
            array_categ,
            plot_kw,
            opts_kw,
            non_dict_data,
            legend,
            form,
            use_attrs,
        )

    # overlay opts_kw
    if "overlay" not in opts_kw:
        opts_kw["overlay"] = {}
    opts_overlay = add_default_opts_overlay(
        opts_kw["overlay"].copy(), legend, show_lat_lon, list(data.values())[0]
    )
    return hv.Overlay(list(get_all_values(figs))).opts(**opts_overlay)
