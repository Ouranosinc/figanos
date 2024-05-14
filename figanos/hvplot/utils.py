"""Utility functions for figanos hvplot figure-creation."""

import collections.abc
import pathlib
import warnings
from functools import partial

import holoviews as hv
import xarray as xr
from bokeh.models import (
    ColumnDataSource,
    GlyphRenderer,
    LegendItem,
    Line,
    Range1d,
    Text,
)
from bokeh.themes import Theme

from figanos.matplotlib.utils import convert_scen_name, empty_dict, process_keys


def get_hv_styles() -> dict[str, str]:
    """Get the available matplotlib styles and their paths, as a dictionary."""
    folder = pathlib.Path(__file__).parent / "style/"
    paths = sorted(p for ext in ["*.yaml", "*.json", "*.yml"] for p in folder.glob(ext))
    names = [
        str(p)
        .split("/")[-1]
        .removesuffix(".yaml")
        .removesuffix(".yml")
        .removesuffix(".json")
        for p in paths
    ]
    return {str(name): path for name, path in zip(names, paths)}


def set_hv_style(*args: str | dict) -> None:
    """Set the holoviews bokeh style using a yaml file or a dict.

    Parameters
    ----------
    args : str or dict
        Name(s) of figanos bokeh style ('ouranos'), build-ing bokeh theme, path(s) to json or yaml or dict.

    Returns
    -------
    None
    """
    for s in args:
        if isinstance(s, dict):
            hv.renderer("bokeh").theme = Theme(json=s)
        elif s.endswith(".json") is True or s.endswith(".yaml") is True:
            hv.renderer("bokeh").theme = Theme(filename=s)
        elif s in get_hv_styles():
            hv.renderer("bokeh").theme = Theme(get_hv_styles()[s])
        elif s in [
            "light_minimal",
            "dark_minimal",
            "caliber",
            "night_sky",
            "contrast",
        ]:  # bokeh build in themes
            hv.renderer("bokeh").theme = s
        else:
            warnings.warn(f"Style {s} not found.")

    # Add Ouranos defaults that can't be directly added to the bokeh theme yaml file
    if "ouranos" in args:
        defaults_curves()


def defaults_curves() -> None:
    """Adds Ouranos defaults to curves that can't be added to bokeh theme."""
    return hv.opts.defaults(
        hv.opts.Curve(
            color=hv.Cycle(
                [
                    "#052946",
                    "#ce153d",
                    "#18bbbb",
                    "#fdc414",
                    "#6850af",
                    "#196a5e",
                    "#7a5315",
                ]
            ),  # ouranos colors
            gridstyle={"ygrid_line_width": 0.5},
            show_grid=True,
        )
    )


def get_glyph_param(hplt, param) -> str:
    """Returns bokeh glyph parameters from hvplot object."""
    # Get the Bokeh renderer
    renderer = hv.renderer("bokeh")
    plot = renderer.get_plot(hplt)
    return getattr(plot.handles["glyph"], param)


def hook_real_dict(plot, element) -> None:
    """Creates hook between hvplot and bokeh to have custom legend to link all realizations insde a key to the same label in legend."""
    # Iterate over the elements in the overlay to get their labels
    if isinstance(element, hv.Overlay):
        labels = []
        for sub_element in element.values():
            labels.append(
                sub_element.label
            )  # would be better if added check for LineType of sub elements

    rends = {}  # store glyph to create legend
    colors = []  # store new colors to know which glyph to add to legend
    n = -1
    for renderer in plot.handles["plot"].renderers:
        if isinstance(renderer.glyph, Line):
            if renderer.glyph.line_color not in colors:
                n += 1  # would be better if found a link between label and glyphs...
                colors.append(renderer.glyph.line_color)
                rends[labels[n]] = [renderer]
            else:
                rends[labels[n]].append(renderer)

    plot.state.legend.items = [
        LegendItem(label=k, renderers=v)
        for k, v in zip(list(rends.keys()), list(rends.values()))
    ]


def edge_legend(plot, element) -> None:
    """Creates hook between hvplot and bokeh to have custom legend to link all realizations insde a key to the same label in legend."""
    l_txt = []

    for renderer in plot.handles["plot"].renderers:

        if isinstance(renderer.glyph, Line):
            data = renderer.data_source.data
            ll = {t: v[-1] for t, v in data.items()}

            # if only one curve does not have label linked to the curve in z
            if len(data) < 3 and isinstance(element.label, str):
                txt = element.label
            else:
                txt = f"{list(ll.keys())[-1]}: {list(ll.values())[-1]}"

            l_txt.append(len(txt))  # store len of texts

            source = ColumnDataSource(
                data=dict(
                    x=[ll[renderer.glyph.x]], y=[ll[renderer.glyph.y]], text=[txt]
                )
            )

            tt = Text(
                x="x",
                y="y",
                text="text",
                text_align="left",
                text_baseline="middle",
                text_color=renderer.glyph.line_color,
                text_font_size="12px",
                x_offset=5,
            )
            glyph_renderer = GlyphRenderer(data_source=source, glyph=tt)
            plot.state.renderers.append(glyph_renderer)

    if plot.state.legend:
        plot.state.legend.items = []

    # increase x_range to show text when plotting
    plot.state.x_range = Range1d(
        start=plot.state.x_range.start,
        end=plot.state.x_range.end
        + 0.0125 * max(l_txt) * (plot.state.x_range.end - plot.state.x_range.start),
    )


def get_all_values(nested_dictionary) -> list:
    """Get all values from a nested dictionary."""
    for key, value in nested_dictionary.items():
        if isinstance(value, collections.abc.Mapping):
            yield from get_all_values(value)
        else:
            yield value


def curve_hover_hook(plot, element, att, form, x) -> None:
    """Hook to pass to hover curve to show correct format"""
    # ToDo: remove this part after use_attrs is fixed
    att = {}
    att["xhover"] = "temps"
    att["yhover"] = "valeur"

    if plot.handles["hover"].tooltips[0][0] != x:
        plot.handles["hover"].tooltips[-2:] = [
            (att["xhover"], "$x{%F}"),
            (att["yhover"], "$y{" + form + "}"),
        ]
    else:
        plot.handles["hover"].tooltips = [
            (att["xhover"], "$x{%F}"),
            (att["yhover"], "$y{" + form + "}"),
        ]
    plot.handles["hover"].formatters = {
        "$x": "datetime",
    }


def rm_curve_hover_hook(plot, element) -> None:
    """Hook to remove hover curve."""
    plot.handles["hover"].tooltips = None


def get_min_max(data) -> tuple:
    """Get min and max values from data."""
    minn = []
    maxx = []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, xr.Dataset):
                for vv in v.values():
                    minn.append(vv.min().values.item())
                    maxx.append(vv.max().values.item())
            else:
                minn.append(v.min().values.item())
                maxx.append(v.max().values.item())
    elif isinstance(data, xr.Dataset):
        for v in data.values():
            minn.append(v.min().values.item())
            maxx.append(v.max().values.item())
    else:
        minn.append(data.min().values.item())
        maxx.append(data.max().values.item())
    return min(minn), max(maxx)


def formatters_data(data) -> str:
    """Get the correct formatter for the data."""
    ymin, ymax = get_min_max(data)
    diff = ymax - ymin

    if abs(ymin) > 1000:
        form = "0 a"
        if diff < 1000 and diff > 100:
            form = "0.00 a"
        elif diff <= 100:
            form = "0.000 a"
    elif diff > 50:
        form = "0"
    elif 10 < diff <= 50:
        form = "0.0"
    elif 1 < diff <= 10:
        form = "0.00"
    elif diff <= 1:
        form = "0.000"
    else:
        form = "0.00"
    return form


def add_default_opts_overlay(opts_kw, form, legend, att, x, array_categ) -> dict:
    """Add default opts to curve plot.

    Parameters
    ----------
    opts_kw : dict
        Custom options to be passed to opts().
    form : str
        Bokeh format.
    legend : str
        Type of legend.
    att : dict
        user_attrs.
    x : str
        Xarray coordinate to be used for plotting xaxis (ex: time).
    array_categ : dict
        Type of data array (ex: ENS_STATS_VAR_DS).

    Returns
    -------
        dict

    """
    if not any(
        map(
            lambda v: v
            in [
                "ENS_STATS_VAR_DS",
                "ENS_PCT_VAR_DS",
                "ENS_PCT_DIM_DS",
                "ENS_PCT_DIM_DA",
            ],
            list(array_categ.values()),
        )
    ):
        # add default tooltips hooks (x and y)
        # should it be added to hook lists if already exists?
        opts_kw["overlay"].setdefault(
            "hooks", [partial(curve_hover_hook, att=att, form=form, x=x)]
        )

    if legend == "'edge":
        warnings.warn(
            "Legend 'edge' is not supported in hvplot. Using 'in_plot' instead."
        )
        legend = "in_plot"
    elif legend == "in_plot":
        opts_kw["overlay"]["hooks"].append(
            edge_legend
        )  # test if should be overlay or to each nested dicts
    if not legend:
        opts_kw["overlay"].setdefault("show_legend", False)
    return opts_kw


def create_dict_timeseries(
    use_attrs, data, plot_kw, opts_kw
) -> [dict, dict, dict, dict, dict]:
    """Create default dicts for timeseries plot."""
    # convert SSP, RCP, CMIP formats in keys
    if isinstance(data, dict):
        data = process_keys(data, convert_scen_name)
    if isinstance(plot_kw, dict):
        plot_kw = process_keys(plot_kw, convert_scen_name)
    if isinstance(opts_kw, dict):
        opts_kw = process_keys(opts_kw, convert_scen_name)

    # create empty dicts if None
    use_attrs = empty_dict(use_attrs)
    opts_kw = empty_dict(opts_kw)
    plot_kw = empty_dict(plot_kw)

    # if only one data input, insert in dict.
    non_dict_data = False
    if not isinstance(data, dict):
        non_dict_data = True
        data = {"_no_label": data}  # mpl excludes labels starting with "_" from legend
        plot_kw = {"_no_label": plot_kw}
        opts_kw = {"_no_label": opts_kw}

    # add overlay option if absent in opts_ke
    opts_kw.setdefault("overlay", {})
    return use_attrs, data, plot_kw, opts_kw, non_dict_data
