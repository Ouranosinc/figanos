"""Figanos plotting module."""

from ._style import get_mpl_styles
from .plot import (
    gdfmap,
    gridmap,
    hatchmap,
    heatmap,
    partition,
    scattermap,
    stripes,
    taylordiagram,
    timeseries,
    violin,
)
from .utils import categorical_colors, plot_logo, set_mpl_style
