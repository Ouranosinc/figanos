"""Utility functions for figanos figure-creation."""

import collections.abc

import holoviews as hv
from bokeh.models import (
    ColumnDataSource,
    GlyphRenderer,
    HoverTool,
    LegendItem,
    Line,
    Range1d,
    Text,
)


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


def curve_hover_hook(plot, element, att) -> None:
    """Hook to pass to hover curve to show correct format."""
    # min - max data
    ymin = plot.handles["y_range"].start
    ymax = plot.handles["y_range"].end
    diff = ymax - ymin

    if ymin > 10000:
        format = "0 a"
        if diff < 1000 and diff > 100:
            format = "0.00 a"
        elif diff <= 100:
            format = "0.000 a"
    elif ymin > 10:
        format = "0"
        if diff < 10 and diff > 1:
            format = "0.0"
        elif diff <= 1:
            format = "0.00"
    elif ymin > 2:
        format = "0.0"
        if diff < 1:
            format = "0.00"
    else:
        format = "0.00"

    hover = HoverTool(
        tooltips=[("time", "$x{%F}"), (att, "$y")],
        formatters={"$x": "datetime", "$y": format},
    )
    return hover
