"""Figanos plotting module."""

from ._partitioning import (
    graph_fraction_of_total_variance,
    graph_fractional_uncertainty,
    graph_variance,
)
from .plot import (
    gdfmap,
    gridmap,
    hatchmap,
    heatmap,
    scattermap,
    stripes,
    taylordiagram,
    timeseries,
    violin,
)
from .utils import categorical_colors, plot_logo, set_mpl_style
