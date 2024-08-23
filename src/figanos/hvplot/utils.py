"""Utility functions for figanos hvplot figure-creation."""

import collections.abc
import pathlib
import warnings
from functools import partial
from typing import Any

import holoviews as hv
import xarray as xr
from bokeh.models import (
    ColumnDataSource,
    GlyphRenderer,
    HoverTool,
    Label,
    LegendItem,
    Line,
    Range1d,
    Text,
)
from bokeh.themes import Theme

from figanos.matplotlib.utils import (
    convert_scen_name,
    empty_dict,
    get_attributes,
    process_keys,
    wrap_text,
)


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
    """Hook function to be passed to hvplot.opts to modify hover tooltips."""
    for hov_id, hover in plot.handles["hover_tools"].items():
        if hover.tooltips[0][0] != x:
            hover.tooltips[-2:] = [
                (att["xhover"], "$x{%F}"),
                (att["yhover"], "$y{" + form + "}"),
            ]
        else:
            hover.tooltips = [
                (att["xhover"], "$x{%F}"),
                (att["yhover"], "$y{" + form + "}"),
            ]
        hover.formatters = {
            "$x": "datetime",
        }


def curve_hover_tool(att, form, r=None) -> list[HoverTool]:
    """Tool to be passed to hvplot.opts to modify hover tooltips."""
    tips = [
        (att["xhover"], "$x{%F}"),
        (att["yhover"], "$y{" + form + "}"),
    ]
    if r is not None:
        tips.insert(0, ("realization", f"{r}"))
    return [HoverTool(tooltips=tips, formatters={"$x": "datetime"})]


# can probably delete this function
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


def add_default_opts_overlay(opts_kw, legend, show_lat_lon, data) -> dict:
    """Add default opts to curve plot.

    Parameters
    ----------
    opts_kw : dict
        Custom options to be passed to opts() of holoviews overlay figure.
    legend : str
        Type of legend.
    show_lat_lon : bool, tuple, str or int
        Show latitude and longitude on figure
    data : xr.DataArray | xr.Dataset | dict
        Data to be plotted.

    Returns
    -------
        dict

    """
    if legend == "edge":
        warnings.warn(
            "Legend 'edge' is not supported in hvplot. Using 'in_plot' instead."
        )
        legend = "in_plot"
    elif legend == "in_plot":
        opts_kw["show_legend"] = False
        if "hooks" in list(opts_kw.keys()):
            opts_kw["hooks"].append(edge_legend)
        else:
            opts_kw["hooks"] = [edge_legend]
    if not legend:
        opts_kw.setdefault("show_legend", False)

    if show_lat_lon:
        sll = plot_coords(
            list(data.values())[0],
            loc=show_lat_lon,
            param="location",
            backgroundalpha=1,
        )
        if "hooks" in list(opts_kw.keys()):
            opts_kw["hooks"].append(sll)
        else:
            opts_kw["hooks"] = [sll]

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


def x_timeseries(data, plot_kw) -> None:
    """Get x coordinate for timeseries plot."""
    if "x" not in plot_kw.keys():
        if "time" in data.coords:
            plot_kw["x"] = "time"
        elif "month" in data.coords:
            plot_kw["x"] = "month"
        elif "season" in data.coords:
            plot_kw["x"] = "season"
        elif "year" in data.coords:
            plot_kw["x"] = "year"
        elif "dayofyear" in data.coords:
            plot_kw["x"] = "dayofyear"
        elif "annual_cycle" in data.coords:
            plot_kw["x"] = "annual_cycle"
        elif "x" in data.coords:
            plot_kw["x"] = "x"
        else:
            raise ValueError(
                "None if these coordinates; time, month, year,"
                " season, dayofyear, annual_cycle and x were found in data."
                "Please specify x coordinate in plot_kw."
            )


def set_plot_attrs_hv(
    use_attrs: dict[str, Any],
    xr_obj: xr.DataArray | xr.Dataset,
    plot_kw: dict[str, Any],
    wrap_kw: dict[str, Any] | None = None,
) -> [dict, dict]:
    """Set plot attributes with the last plot_kw entry based on use_attr."""
    # set default use_attrs values
    use_attrs = {
        "title": "description",
        "ylabel": "long_name",
        "yunits": "units",
        "yhover": "standart_name",
    } | use_attrs

    wrap_kw = empty_dict(wrap_kw)

    # last plot_kw entry
    name = list(plot_kw.keys())[0]

    for key in use_attrs.keys():
        if key not in [
            "title",
            "ylabel",
            "yunits",
            "xunits",
            "xhover",
            "yhover",
            # "xlabel",
            # "cbar_label",
            # "cbar_units",
            # "suptitle",
        ]:
            warnings.warn(f'Use_attrs element "{key}" not supported')

    if "title" in use_attrs:
        title = get_attributes(use_attrs["title"], xr_obj)
        plot_kw[name].setdefault("title", wrap_text(title, **wrap_kw))

    if "ylabel" in use_attrs:
        if (
            "yunits" in use_attrs
            and len(get_attributes(use_attrs["yunits"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            ylabel = wrap_text(
                get_attributes(use_attrs["ylabel"], xr_obj)
                + " ("
                + get_attributes(use_attrs["yunits"], xr_obj)
                + ")"
            )
        else:
            ylabel = wrap_text(get_attributes(use_attrs["ylabel"], xr_obj))

        plot_kw[name].setdefault("ylabel", ylabel)

    if "xlabel" in use_attrs:
        if (
            "xunits" in use_attrs
            and len(get_attributes(use_attrs["xunits"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            xlabel = wrap_text(
                get_attributes(use_attrs["xlabel"], xr_obj)
                + " ("
                + get_attributes(use_attrs["xunits"], xr_obj)
                + ")"
            )
        else:
            xlabel = wrap_text(get_attributes(use_attrs["xlabel"], xr_obj))
    else:
        xlabel = plot_kw[name]["x"]
    plot_kw[name].setdefault("xlabel", xlabel)

    if "yhover" in use_attrs:
        if (
            "yunits" in use_attrs
            and len(get_attributes(use_attrs["yhover"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            yhover = wrap_text(
                get_attributes(use_attrs["yhover"], xr_obj)
                + " ("
                + get_attributes(use_attrs["yunits"], xr_obj)
                + ")"
            )
        else:
            yhover = get_attributes(use_attrs["yhover"], xr_obj)
        use_attrs["yhover"] = yhover

    if "xhover" in use_attrs:
        if (
            "xunits" in use_attrs
            and len(get_attributes(use_attrs["xunits"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            xhover = wrap_text(
                get_attributes(use_attrs["xhover"], xr_obj)
                + " ("
                + get_attributes(use_attrs["xunits"], xr_obj)
                + ")"
            )
        else:
            xhover = wrap_text(get_attributes(use_attrs["xhover"], xr_obj))
    else:
        xhover = plot_kw[name]["x"]
    use_attrs["xhover"] = xhover
    return use_attrs, plot_kw


def plot_coords_hook(plot, element, text, loc, bgc) -> None:
    """Hook to add text to plot. Use hooks to have access to screen units."""
    pk = {}
    pk["background_fill_alpha"] = bgc

    if isinstance(loc, str):
        pk["x_units"] = "screen"
        pk["y_units"] = "screen"

        width, height = plot.state.width, plot.state.height

        if loc == "center":
            pk["y"] = (height - 150) / 2
            pk["x"] = (width - 300) / 2
        else:
            if "upper" in loc:
                pk["y"] = height - 150
            if "lower" in loc:
                pk["y"] = 10
            if "right" in loc:
                pk["x"] = width - 180
                pk["text_align"] = "right"
            if "left" in loc:
                pk["x"] = 10
                pk["text_align"] = "left"
            if "center" in loc:
                if loc[0] == "c":
                    pk["y"] = (height - 150) / 2
                else:
                    pk["x"] = (width - 300) / 2
    elif isinstance(loc, tuple):
        pk["x_units"] = "data"
        pk["y_units"] = "data"
        pk["x"] = loc[0]
        pk["y"] = loc[1]

    label = Label(text=text, **pk)
    plot.state.add_layout(label)


def plot_coords(
    xr_obj: xr.DataArray | xr.Dataset,
    loc: str | tuple[float, float] | int,
    param: str | None = None,
    backgroundalpha: float = 1,
) -> hv.Text:
    """Plot the coordinates of an xarray object.

    Parameters
    ----------
    xr_obj : xr.DataArray | xr.Dataset
        The xarray object from which to plot the coordinates.
    loc : str | tuple[float, float] | int
        Location of text, replicating https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html.
        If a tuple, must be in axes coordinates.
    param : {"location", "time"}, optional
        The parameter used.
    backgroundalpha : float
        Transparency of the text background. 1 is opaque, 0 is transparent.
    projection: str
        Custom projection. Default is None.

    Returns
    -------
    hv.Text
    """
    text = None
    if param == "location":
        if "lat" in xr_obj.coords and "lon" in xr_obj.coords:
            text = "lat={:.2f}, lon={:.2f}".format(
                float(xr_obj["lat"]), float(xr_obj["lon"])
            )
        else:
            warnings.warn(
                'show_lat_lon set to True, but "lat" and/or "lon" not found in coords'
            )
    if param == "time":
        if "time" in xr_obj.coords:
            text = str(xr_obj.time.dt.strftime("%Y-%m-%d").values)

        else:
            warnings.warn('show_time set to True, but "time" not found in coords')

    if isinstance(loc, int):
        equiv = {
            1: "upper right",
            2: "upper left",
            3: "lower left",
            4: "lower right",
            6: "center left",
            7: "center right",
            8: "lower center",
            9: "upper center",
            10: "center",
        }
        loc = equiv[loc]
    if isinstance(loc, bool):
        loc = "lower left"

    return partial(plot_coords_hook, text=text, loc=loc, bgc=backgroundalpha)
