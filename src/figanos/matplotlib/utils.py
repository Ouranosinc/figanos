"""Utility functions for figanos figure-creation."""

from __future__ import annotations
import json
import math
import pathlib
import re
import warnings
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import cairosvg
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib as mpl
import matplotlib.axes
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn
import xarray as xr
import yaml
from matplotlib.lines import Line2D
from skimage.transform import resize
from xclim.core.options import METADATA_LOCALES
from xclim.core.options import OPTIONS as XC_OPTIONS

from .._logo import Logos


# file to map variable key words to variable group for IPCC color scheme
VARJSON = Path(__file__).parents[1] / "data/ipcc_colors/variable_groups.json"

TERMS: dict = {}
"""
A translation directory for special terms to appear on the plots.

Keys are terms to translate and they map to "locale": "translation" dictionaries.
The "official" figanos terms are based on figanos/data/terms.yml.
"""


# Load terms translations
with (pathlib.Path(__file__).resolve().parents[1] / "data" / "terms.yml").open() as f:
    TERMS = yaml.safe_load(f)


def get_localized_term(term, locale=None):
    """
    Get `term` translated into `locale`.

    Terms are pulled from the :py:data:`TERMS` dictionary.

    Parameters
    ----------
    term : str
        A word or short phrase to translate.
    locale : str, optional
        A 2-letter locale name to translate to.
        Default is None, which will pull the locale from xclim's "metadata_locales" option (taking the first).

    Returns
    -------
    str
        Translated term.
    """
    locale = locale or (XC_OPTIONS[METADATA_LOCALES] or ["en"])[0]
    if locale == "en":
        return term

    if term not in TERMS:
        warnings.warn(f"No translation known for term '{term}'.", stacklevel=2)
        return term

    if locale not in TERMS[term]:
        warnings.warn(f"No {locale} translation known for term '{term}'.", stacklevel=2)
        return term

    return TERMS[term][locale]


def empty_dict(param) -> dict:
    """Return empty dict if input is None."""
    if param is None:
        param = dict()
    return deepcopy(param)  # avoid modifying original input dict when popping items


def check_timeindex(
    xr_objs: xr.DataArray | xr.Dataset | dict[str, Any],
) -> xr.DataArray | xr.Dataset | dict[str, Any]:
    """
    Check if the time index of Xarray objects in a dict is CFtime and convert to pd.DatetimeIndex if True.

    Parameters
    ----------
    xr_objs : xr.DataArray or xr.Dataset or dict
        Dictionary containing Xarray DataArrays or Datasets.

    Returns
    -------
    xr.DataArray or xr.Dataset or dict
        Dictionary of xarray objects with a pandas DatetimeIndex
    """
    if isinstance(xr_objs, dict):
        for name, obj in xr_objs.items():
            if "time" in obj.dims:
                if isinstance(obj.get_index("time"), xr.CFTimeIndex):
                    conv_obj = obj.convert_calendar(
                        "standard", use_cftime=None, align_on="year"
                    )
                    xr_objs[name] = conv_obj
                    warnings.warn(
                        "CFTimeIndex converted to pandas DatetimeIndex with a 'standard' calendar.", stacklevel=2
                    )

    else:
        if "time" in xr_objs.dims:
            if isinstance(xr_objs.get_index("time"), xr.CFTimeIndex):
                conv_obj = xr_objs.convert_calendar(
                    "standard", use_cftime=None, align_on="year"
                )
                xr_objs = conv_obj
                warnings.warn(
                    "CFTimeIndex converted to pandas DatetimeIndex with a 'standard' calendar.", stacklevel=2
                )

    return xr_objs


def get_array_categ(array: xr.DataArray | xr.Dataset) -> str:
    """
    Get an array category, which determines how to plot the array.

    Parameters
    ----------
    array : Dataset or DataArray
        The array being categorized.

    Returns
    -------
    str
        ENS_PCT_VAR_DS: ensemble percentiles stored as variables
        ENS_PCT_DIM_DA: ensemble percentiles stored as dimension coordinates, DataArray
        ENS_PCT_DIM_DS: ensemble percentiles stored as dimension coordinates, DataSet
        ENS_STATS_VAR_DS: ensemble statistics (min, mean, max) stored as variables
        ENS_REALS_DA: ensemble with 'realization' dim, as DataArray
        ENS_REALS_DS: ensemble with 'realization' dim, as Dataset
        DS: any Dataset that is not  recognized as an ensemble
        DA: DataArray
    """
    if isinstance(array, xr.Dataset):
        if (
            pd.notnull(
                [re.search("_p[0-9]{1,2}", var) for var in array.data_vars]
            ).sum()
            >= 2
        ):
            cat = "ENS_PCT_VAR_DS"
        elif (
            pd.notnull(
                [re.search("_[Mm]ax|_[Mm]in", var) for var in array.data_vars]
            ).sum()
            >= 2
        ):
            cat = "ENS_STATS_VAR_DS"
        elif "percentiles" in array.dims:
            cat = "ENS_PCT_DIM_DS"
        elif "realization" in array.dims:
            cat = "ENS_REALS_DS"
        else:
            cat = "DS"

    elif isinstance(array, xr.DataArray):
        if "percentiles" in array.dims:
            cat = "ENS_PCT_DIM_DA"
        elif "realization" in array.dims:
            cat = "ENS_REALS_DA"
        else:
            cat = "DA"
    else:
        raise TypeError("Array is not an Xarray Dataset or DataArray")

    return cat


def get_attributes(
    string: str, xr_obj: xr.DataArray | xr.Dataset, locale: str | None = None
) -> str:
    """
    Fetch attributes or dims corresponding to keys from Xarray objects.

    Searches DataArray attributes first, then the first variable (DataArray) of the Dataset, then Dataset attributes.
    If a locale is activated in xclim's options or a locale is passed, a localized version is given if available.

    Parameters
    ----------
    string : str
        String corresponding to an attribute name.
    xr_obj : DataArray or Dataset
        The Xarray object containing the attributes.
    locale : str, optional
        A 2-letter locale name to translate to.
        Default is None, which will pull the locale
        from xclim's "metadata_locales" option (taking the first).

    Returns
    -------
    str
        Xarray attribute value as string or empty string if not found
    """
    locale = locale or (XC_OPTIONS[METADATA_LOCALES] or ["en"])[0]
    if locale != "en":
        names = [f"{string}_{locale}", string]
    else:
        names = [string]

    for name in names:
        if isinstance(xr_obj, xr.DataArray) and name in xr_obj.attrs:
            return xr_obj.attrs[name]

        if (
            isinstance(xr_obj, xr.Dataset)
            and name in xr_obj[list(xr_obj.data_vars)[0]].attrs
        ):  # DataArray of first variable
            return xr_obj[list(xr_obj.data_vars)[0]].attrs[name]

        if isinstance(xr_obj, xr.Dataset) and name in xr_obj.attrs:
            return xr_obj.attrs[name]

    warnings.warn(f'Attribute "{string}" not found.', stacklevel=2)
    return ""


def set_plot_attrs(
    attr_dict: dict[str, Any],
    xr_obj: xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes | None = None,
    title_loc: str = "center",
    facetgrid: seaborn.axisgrid.FacetGrid | None = None,
    wrap_kw: dict[str, Any] | None = None,
) -> matplotlib.axes.Axes:
    """
    Set plot elements according to Dataset or DataArray attributes.

    Uses get_attributes() to check for and get the string.

    Parameters
    ----------
    attr_dict : dict
        Dictionary containing specified attribute keys.
    xr_obj : Dataset or DataArray
        The Xarray object containing the attributes.
    ax : matplotlib axis
        The matplotlib axis of the plot.
    title_loc : str
        Location of the title.
    wrap_kw : dict, optional
        Arguments to pass to the wrap_text function for the title.

    Returns
    -------
    matplotlib.axes.Axes
    """
    wrap_kw = empty_dict(wrap_kw)

    #  check
    for key in attr_dict:
        if key not in [
            "title",
            "ylabel",
            "yunits",
            "xlabel",
            "xunits",
            "cbar_label",
            "cbar_units",
            "suptitle",
        ]:
            warnings.warn(f'Use_attrs element "{key}" not supported', stacklevel=2)

    if "title" in attr_dict:
        title = get_attributes(attr_dict["title"], xr_obj)
        ax.set_title(wrap_text(title, **wrap_kw), loc=title_loc)

    if "ylabel" in attr_dict:
        if (
            "yunits" in attr_dict
            and len(get_attributes(attr_dict["yunits"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            ylabel = wrap_text(
                get_attributes(attr_dict["ylabel"], xr_obj)
                + " ("
                + get_attributes(attr_dict["yunits"], xr_obj)
                + ")"
            )
        else:
            ylabel = wrap_text(get_attributes(attr_dict["ylabel"], xr_obj))

        ax.set_ylabel(ylabel)

    if "xlabel" in attr_dict:
        if (
            "xunits" in attr_dict
            and len(get_attributes(attr_dict["xunits"], xr_obj)) >= 1
        ):  # second condition avoids '[]' as label
            xlabel = wrap_text(
                get_attributes(attr_dict["xlabel"], xr_obj)
                + " ("
                + get_attributes(attr_dict["xunits"], xr_obj)
                + ")"
            )
        else:
            xlabel = wrap_text(get_attributes(attr_dict["xlabel"], xr_obj))

        ax.set_xlabel(xlabel)

    # cbar label has to be assigned in main function, ignore.
    if "cbar_label" in attr_dict:
        pass

    if "cbar_units" in attr_dict:
        pass

    if facetgrid:
        if "suptitle" in attr_dict:
            suptitle = get_attributes(attr_dict["suptitle"], xr_obj)
            facetgrid.fig.suptitle(suptitle, y=1.05)
            facetgrid.set_titles(template="{value}")
        return facetgrid

    else:
        return ax


def get_suffix(string: str) -> str:
    """Get suffix of typical Xclim variable names."""
    if re.search("[0-9]{1,2}$|_[Mm]ax$|_[Mm]in$|_[Mm]ean$", string):
        suffix = re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", string).group()
        return suffix
    else:
        raise ValueError(f"Mean, min or max not found in {string}")


def sort_lines(array_dict: dict[str, Any]) -> dict[str, str]:
    """
    Label arrays as 'middle', 'upper' and 'lower' for ensemble plotting.

    Parameters
    ----------
    array_dict : dict
        Dictionary of format {'name': array...}.

    Returns
    -------
    dict
        Dictionary of {'middle': 'name', 'upper': 'name', 'lower': 'name'}.
    """
    if len(array_dict) != 3:
        raise ValueError("Ensembles must contain exactly three arrays")

    sorted_lines = {}

    for name in array_dict.keys():
        suffix = get_suffix(name)

        if suffix.isalpha():
            if suffix in ["max", "Max"]:
                sorted_lines["upper"] = name
            elif suffix in ["min", "Min"]:
                sorted_lines["lower"] = name
            elif suffix in ["mean", "Mean"]:
                sorted_lines["middle"] = name
        elif suffix.isdigit():
            if int(suffix) >= 51:
                sorted_lines["upper"] = name
            elif int(suffix) <= 49:
                sorted_lines["lower"] = name
            elif int(suffix) == 50:
                sorted_lines["middle"] = name
        else:
            raise ValueError('Arrays names must end in format "_mean" or "_p50" ')
    return sorted_lines


def loc_mpl(
    loc: str | tuple[int | float, int | float] | int,
) -> tuple[tuple[float, float], tuple[int | float, int | float], str, str]:
    """
    Find coordinates and alignment associated to loc string.

    Parameters
    ----------
    loc : string, int, or tuple[float, float]
        Location of text, replicating https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html.
        If a tuple, must be in axes coordinates.

    Returns
    -------
    tuple(float, float), tuple(float, float), str, str
    """
    ha = "left"
    va = "bottom"

    loc_strings = [
        "upper right",
        "upper left",
        "lower left",
        "lower right",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    ]

    if isinstance(loc, int):
        try:
            loc = loc_strings[loc - 1]
        except IndexError as err:
            raise ValueError("loc must be between 1 and 10, inclusively") from err

    if loc in loc_strings:
        # ha
        if "left" in loc:
            ha = "left"
        elif "right" in loc:
            ha = "right"
        else:
            ha = "center"

        # va
        if "lower" in loc:
            va = "bottom"
        elif "upper" in loc:
            va = "top"
        else:
            va = "center"

        # transAxes
        if loc == "upper right":
            loc = (0.97, 0.97)
            box_a = (1, 1)
        elif loc == "upper left":
            loc = (0.03, 0.97)
            box_a = (0, 1)
        elif loc == "lower left":
            loc = (0.03, 0.03)
            box_a = (0, 0)
        elif loc == "lower right":
            loc = (0.97, 0.03)
            box_a = (1, 0)
        elif loc == "right":
            loc = (0.97, 0.5)
            box_a = (1, 0.5)
        elif loc == "center left":
            loc = (0.03, 0.5)
            box_a = (0, 0.5)
        elif loc == "center right":
            loc = (0.97, 0.5)
            box_a = (0.97, 0.5)
        elif loc == "lower center":
            loc = (0.5, 0.03)
            box_a = (0.5, 0)
        elif loc == "upper center":
            loc = (0.5, 0.97)
            box_a = (0.5, 1)
        else:
            loc = (0.5, 0.5)
            box_a = (0.5, 0.5)

    elif isinstance(loc, tuple):
        box_a = []
        for i in loc:
            if i > 1 or i < 0:
                raise ValueError(
                    "Text location coordinates must be between 0 and 1, inclusively"
                )
            elif i > 0.5:
                box_a.append(1)
            else:
                box_a.append(0)
        box_a = tuple(box_a)
    else:
        raise ValueError(
            "loc must be a string, int or tuple. "
            "See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html"
        )

    return loc, box_a, ha, va


def plot_coords(
    ax: matplotlib.axes.Axes | None,
    xr_obj: xr.DataArray | xr.Dataset,
    loc: str | tuple[float, float] | int,
    param: str | None = None,
    backgroundalpha: float = 1,
) -> matplotlib.axes.Axes:
    """
    Place coordinates on plot area.

    Parameters
    ----------
    ax : matplotlib.axes.Axes or None
        Matplotlib axes object on which to place the text.
        If None, will use plt.figtext instead (should be used for facetgrids).
    xr_obj : xr.DataArray or xr.Dataset
        The xarray object from which to fetch the text content.
    param : {"location", "time"}, optional
        The parameter used.
    loc : string, int or tuple
        Location of text, replicating https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html.
        If a tuple, must be in axes coordinates.
    backgroundalpha : float
        Transparency of the text background. 1 is opaque, 0 is transparent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    text = None
    if param == "location":
        if "lat" in xr_obj.coords and "lon" in xr_obj.coords:
            text = "lat={:.2f}, lon={:.2f}".format(
                float(xr_obj["lat"]), float(xr_obj["lon"])
            )
        else:
            warnings.warn(
                'show_lat_lon set to True, but "lat" and/or "lon" not found in coords', stacklevel=2
            )
    if param == "time":
        if "time" in xr_obj.coords:
            text = str(xr_obj.time.dt.strftime("%Y-%m-%d").values)

        else:
            warnings.warn('show_time set to True, but "time" not found in coords', stacklevel=2)

    loc, box_a, ha, va = loc_mpl(loc)

    if text:
        if ax:
            t = mpl.offsetbox.TextArea(
                text, textprops=dict(transform=ax.transAxes, ha=ha, va=va)
            )

            tt = mpl.offsetbox.AnnotationBbox(
                t,
                loc,
                xycoords="axes fraction",
                box_alignment=box_a,
                pad=0.05,
                bboxprops=dict(
                    facecolor="white",
                    alpha=backgroundalpha,
                    edgecolor="w",
                    boxstyle="Square, pad=0.5",
                ),
            )
            ax.add_artist(tt)
            return ax
        elif not ax:
            """
            if loc == "top left":
                plt.figtext(0.8, 1.025, text, ha="center", fontsize=12)
            elif loc == "top right":
                plt.figtext(0.2, -0.075, text, ha="center", fontsize=12)
            elif loc == "bottom left":
                plt.figtext(0.2, -0.075, text, ha="center", fontsize=12)
            elif loc == "bottom right" or loc is True:
                plt.figtext(0.8, -0.075, text, ha="center", fontsize=12)
            elif isinstance(loc, tuple):
                        else:
                raise ValueError(
                    f"{loc} option does not work with facetgrids. Try 'top left', ''top right', 'bottom left', "
                    f"'bottom right' or a tuple of coordinates."
                )
            """
            plt.figtext(
                loc[0],
                loc[1],
                text,
                ha=ha,
                va=va,
                fontsize=12,
            )

            return None


def find_logo(logo: str | pathlib.Path) -> str:
    """Read a logo file."""
    logos = Logos()
    if logo:
        logo_path = logos[logo]
    else:
        logo_path = logos.default

    if logo_path is None:
        raise ValueError(
            "No logo found. Please install one with the figanos.Logos().set_logo() method."
        )
    return logo_path


def load_image(
    im: str | pathlib.Path,
    height: float | None,
    width: float | None,
    keep_ratio: bool = True,
) -> np.ndarray:
    """
    Scale an image to a specified height and width.

    Parameters
    ----------
    im : str or Path
        The image to be scaled. PNG and SVG formats are supported.
    height : float, optional
        The desired height of the image. If None, the original height is used.
    width : float, optional
        The desired width of the image. If None, the original width is used.
    keep_ratio : bool
        If True, the aspect ratio of the original image is maintained. Default is True.

    Returns
    -------
    np.ndarray
        The scaled image.
    """
    if pathlib.Path(im).suffix == ".png":
        image = mpl.pyplot.imread(im)
        original_height, original_width = image.shape[:2]

        if height is None and width is None:
            return image

        warnings.warn(
            "The scikit-image library is used to resize PNG images. This may affect logo image quality.", stacklevel=2
        )
        if not keep_ratio:
            height = original_height or height
            width = original_width or width
        else:
            if width is not None:
                if height is not None:
                    warnings.warn("Both height and width provided, using height.", stacklevel=2)
                # Only width is provided, derive zoom factor for height based on aspect ratio
                height = (width / original_width) * original_height
            elif height is not None:
                # Only height is provided, derive zoom factor for width based on aspect ratio
                width = (height / original_height) * original_width

        return resize(image, (height, width, image.shape[2]), anti_aliasing=True)

    elif pathlib.Path(im).suffix == ".svg":
        cairo_kwargs = dict(url=im)
        if not keep_ratio:
            if height is not None and width is not None:
                cairo_kwargs.update(output_height=height, output_width=width)
        elif width is not None:
            if height is not None:
                warnings.warn("Both height and width provided, using height.", stacklevel=2)
            cairo_kwargs.update(output_width=width)
        elif height is not None:
            cairo_kwargs.update(output_height=height)

        with NamedTemporaryFile(suffix=".png") as png_file:
            cairo_kwargs.update(write_to=png_file.name)
            cairosvg.svg2png(**cairo_kwargs)
            return mpl.pyplot.imread(png_file.name)


def plot_logo(
    ax: matplotlib.axes.Axes,
    loc: str | tuple[float, float] | int,
    logo: str | pathlib.Path | Logos | None = None,
    height: float | None = None,
    width: float | None = None,
    keep_ratio: bool = True,
    **offset_image_kwargs,
) -> matplotlib.axes.Axes:
    r"""
    Place logo of plot area.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes object on which to place the text.
    loc : string, int or tuple
        Location of text, replicating https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html.
        If a tuple, must be in axes coordinates.
    logo : str, Path, figanos.Logos, optional
        A name (str) or Path to a logo file, or a name of an already-installed logo.
        If an existing is not found, the logo will be installed and accessible via the filename.
        The default logo is the Figanos logo. To install the Ouranos (or another) logo consult the Usage page.
        The logo must be in 'png' format.
    height : float, optional
        The desired height of the image. If None, the original height is used.
    width : float, optional
        The desired width of the image. If None, the original width is used.
    keep_ratio : bool, optional
        If True, the aspect ratio of the original image is maintained. Default is True.
    \*\*offset_image_kwargs
        Arguments to pass to matplotlib.offsetbox.OffsetImage().

    Returns
    -------
    matplotlib.axes.Axes
    """
    if offset_image_kwargs is None:
        offset_image_kwargs = {}

    if isinstance(logo, Logos):
        logo_path = logo.default
    else:
        logo_path = find_logo(logo)

    image = load_image(logo_path, height, width, keep_ratio)
    imagebox = mpl.offsetbox.OffsetImage(image, **offset_image_kwargs)

    loc, box_a, ha, va = loc_mpl(loc)
    ab = mpl.offsetbox.AnnotationBbox(
        imagebox,
        loc,
        frameon=False,
        xycoords="axes fraction",
        box_alignment=box_a,
        pad=0.05,
    )
    ax.add_artist(ab)
    return ax


def split_legend(
    ax: matplotlib.axes.Axes,
    in_plot: bool = False,
    axis_factor: float = 0.15,
    label_gap: float = 0.02,
) -> matplotlib.axes.Axes:
    #  TODO: check for and fix overlapping labels
    """
    Draw line labels at the end of each line, or outside the plot.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis containing the legend.
    in_plot : bool
        If True, prolong plot area to fit labels. If False, print labels outside of plot area. Default: False.
    axis_factor : float
        If in_plot is True, fraction of the x-axis length to add at the far right of the plot. Default: 0.15.
    label_gap : float
        If in_plot is True, fraction of the x-axis length to add as a gap between line and label. Default: 0.02.

    Returns
    -------
    matplotlib.axes.Axes
    """
    # create extra space
    init_xbound = ax.get_xbound()

    ax_bump = (init_xbound[1] - init_xbound[0]) * axis_factor
    label_bump = (init_xbound[1] - init_xbound[0]) * label_gap

    if in_plot is True:
        ax.set_xbound(lower=init_xbound[0], upper=init_xbound[1] + ax_bump)

    # get legend and plot

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels, strict=False):
        last_x = handle.get_xdata()[-1]
        last_y = handle.get_ydata()[-1]

        if isinstance(last_x, np.datetime64):
            last_x = mpl.dates.date2num(last_x)

        color = handle.get_color()
        # ls = handle.get_linestyle()

        if in_plot is True:
            ax.text(
                last_x + label_bump,
                last_y,
                label,
                ha="left",
                va="center",
                color=color,
            )
        else:
            trans = mpl.transforms.blended_transform_factory(ax.transAxes, ax.transData)
            ax.text(
                1.01,
                last_y,
                label,
                ha="left",
                va="center",
                color=color,
                transform=trans,
            )

    return ax


def fill_between_label(
    sorted_lines: dict[str, Any],
    name: str,
    array_categ: dict[str, Any],
    legend: str,
) -> str:
    """
    Create a label for the shading around a line in line plots.

    Parameters
    ----------
    sorted_lines : dict
        Dictionary created by the sort_lines() function.
    name : str
        Key associated with the object being plotted in the 'data' argument of the timeseries() function.
    array_categ : dict
        The categories of the array, as created by the get_array_categ function.
    legend : str
        Legend mode.

    Returns
    -------
    str
        Label to be applied to the legend element representing the shading.
    """
    if legend != "full":
        label = None
    elif array_categ[name] in [
        "ENS_PCT_VAR_DS",
        "ENS_PCT_DIM_DS",
        "ENS_PCT_DIM_DA",
    ]:
        label = get_localized_term("{}th-{}th percentiles").format(
            get_suffix(sorted_lines["lower"]), get_suffix(sorted_lines["upper"])
        )
    elif array_categ[name] == "ENS_STATS_VAR_DS":
        label = get_localized_term("min-max range")
    else:
        label = None

    return label


def get_var_group(
    da: xr.DataArray | None = None,
    unique_str: str | None = None,
    path_to_json: str | pathlib.Path | None = None,
) -> str:
    """
    Get IPCC variable group from DataArray or a string using a json file (figanos/data/ipcc_colors/variable_groups.json).

    If `da` is a Dataset, look in the DataArray of the first variable.
    """
    if path_to_json is None:
        path_to_json = VARJSON

    # create dict
    with pathlib.Path(path_to_json).open(encoding="utf-8") as _f:
        var_dict = json.load(_f)

    matches = []

    if unique_str:
        for v in var_dict:
            regex = rf"(?:^|[^a-zA-Z])({v})(?:[^a-zA-Z]|$)"  # matches when variable is not inside word
            if re.search(regex, unique_str):
                matches.append(var_dict[v])

    else:
        if isinstance(da, xr.Dataset):
            da = da[list(da.data_vars)[0]]
        # look in DataArray name
        if hasattr(da, "name") and isinstance(da.name, str):
            for v in var_dict:
                regex = rf"(?:^|[^a-zA-Z])({v})(?:[^a-zA-Z]|$)"
                if re.search(regex, da.name):
                    matches.append(var_dict[v])

        # look in history
        if hasattr(da, "history") and len(matches) == 0:
            for v in var_dict:
                regex = rf"(?:^|[^a-zA-Z])({v})(?:[^a-zA-Z]|$)"
                if re.search(regex, da.history):
                    matches.append(var_dict[v])

    matches = np.unique(matches)

    if len(matches) == 0:
        warnings.warn(
            "Colormap warning: Variable group not found. Use the cmap argument.", stacklevel=2
        )
        return "misc"
    elif len(matches) >= 2:
        warnings.warn(
            "Colormap warning: More than one variable group found. Use the cmap argument.", stacklevel=2
        )
        return "misc"
    else:
        return matches[0]


def create_cmap(
    var_group: str | None = None,
    divergent: bool | int = False,
    filename: str | None = None,
) -> matplotlib.colors.Colormap:
    """
    Create colormap according to variable group.

    Parameters
    ----------
    var_group : str, optional
        Variable group from IPCC scheme.
    divergent : bool or int
        Diverging colormap. If False, use sequential colormap.
    filename : str, optional
        Name of IPCC colormap file. If not None, 'var_group' and 'divergent' are not used.

    Returns
    -------
    matplotlib.colors.Colormap
    """
    reverse = False

    if filename:
        folder = "continuous_colormaps_rgb_0-255"
        filename = filename.replace(".txt", "")

        if filename.endswith("_r"):
            reverse = True
            filename = filename[:-2]

    else:
        # filename
        if divergent is not False:
            if var_group == "misc2":
                var_group = "misc"
            filename = var_group + "_div"
        else:
            if var_group == "misc":
                filename = var_group + "_seq_3"  # Batlow
            elif var_group == "misc2":
                filename = "misc_seq_2"  # freezing rain
            else:
                filename = var_group + "_seq"

        folder = "continuous_colormaps_rgb_0-255"

    # parent should be 'figanos/'
    path = (
        pathlib.Path(__file__).parents[1]
        / "data"
        / "ipcc_colors"
        / folder
        / (filename + ".txt")
    )

    rgb_data = np.loadtxt(path)

    # convert to 0-1 RGB
    rgb_data = rgb_data / 255

    cmap = mcolors.LinearSegmentedColormap.from_list("cmap", rgb_data, N=256)
    if reverse is True:
        cmap = cmap.reversed()

    return cmap


def get_rotpole(xr_obj: xr.DataArray | xr.Dataset) -> ccrs.RotatedPole | None:
    """
    Create a Cartopy crs rotated pole projection/transform from DataArray or Dataset attributes.

    Parameters
    ----------
    xr_obj : xr.DataArray or xr.Dataset
        The xarray object from which to look for the attributes.

    Returns
    -------
    ccrs.RotatedPole or None
    """
    try:

        if isinstance(xr_obj, xr.Dataset):
            gridmap = xr_obj.cf.grid_mapping_names.get("rotated_latitude_longitude", [])

            if len(gridmap) > 1:
                warnings.warn(
                    f"There are conflicting grid_mapping attributes in the dataset. Assuming {gridmap[0]}.", stacklevel=2
                )

            coord_name = gridmap[0] if gridmap else "rotated_pole"
        else:
            # If it can't find grid_mapping, assume it's rotated_pole
            coord_name = xr_obj.attrs.get("grid_mapping", "rotated_pole")

        rotpole = ccrs.RotatedPole(
            pole_longitude=xr_obj[coord_name].grid_north_pole_longitude,
            pole_latitude=xr_obj[coord_name].grid_north_pole_latitude,
            central_rotated_longitude=xr_obj[coord_name].north_pole_grid_longitude,
        )
        return rotpole

    except AttributeError:
        warnings.warn("Rotated pole not found. Specify a transform if necessary.", stacklevel=2)
        return None


def wrap_text(text: str, min_line_len: int = 18, max_line_len: int = 30) -> str:
    """
    Wrap text.

    Parameters
    ----------
    text : str
        The text to wrap.
    min_line_len : int
        Minimum length of each line.
    max_line_len : int
        Maximum length of each line.

    Returns
    -------
    str
        Wrapped text
    """
    start = min_line_len
    stop = max_line_len
    sep = "\n"
    remaining = len(text)

    if len(text) >= max_line_len:
        while remaining > max_line_len:
            if ". " in text[start:stop]:
                pos = text.find(". ", start, stop) + 1
            elif ": " in text[start:stop]:
                pos = text.find(": ", start, stop) + 1
            elif " " in text[start:stop]:
                pos = text.rfind(" ", start, stop)
            else:
                warnings.warn("No spaces, points or colons to break line at.", stacklevel=2)
                break

            text = sep.join([text[:pos], text[pos + 1 :]])

            remaining = len(text) - len(text[:pos])
            start = pos + 1 + min_line_len
            stop = pos + 1 + max_line_len

    return text


def gpd_to_ccrs(df: gpd.GeoDataFrame, proj: ccrs.CRS) -> gpd.GeoDataFrame:
    """
    Open shapefile with geopandas and convert to cartopy projection.

    Parameters
    ----------
    df : gpd.GeoDataFrame
        GeoDataFrame (geopandas) geometry to be added to axis.
    proj : ccrs.CRS
        Projection to use, taken from the cartopy.crs options.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame adjusted to given projection
    """
    prj4 = proj.proj4_init
    return df.to_crs(prj4)


def convert_scen_name(name: str) -> str:
    """Convert strings containing SSP, RCP or CMIP to their proper format."""
    matches = re.findall(r"(?:SSP|RCP|CMIP)[0-9]{1,3}", name, flags=re.I)
    if matches:
        for s in matches:
            if sum(c.isdigit() for c in s) == 3:
                new_s = s.replace(
                    s[-3:], s[-3] + "-" + s[-2] + "." + s[-1]
                ).upper()  # ssp245 to SSP2-4.5
                new_name = name.replace(s, new_s)  # put back in name
            elif sum(c.isdigit() for c in s) == 2:
                new_s = s.replace(
                    s[-2:], s[-2] + "." + s[-1]
                ).upper()  # rcp45 to RCP4.5
                new_name = name.replace(s, new_s)
            else:
                new_s = s.upper()  # cmip5 to CMIP5
                new_name = name.replace(s, new_s)

        return new_name
    else:
        return name


def get_scen_color(name: str, path_to_dict: str | pathlib.Path) -> str:
    """Get color corresponding to SSP,RCP, model or CMIP substring from a dictionary."""
    with pathlib.Path(path_to_dict).open(encoding="utf-8") as _f:
        color_dict = json.load(_f)

    color = None
    for entry in color_dict:
        if entry in name:
            color = color_dict[entry]
            color = tuple([i / 255 for i in color])
            break

    return color


def process_keys(dct: dict[str, Any], func: Callable) -> dict[str, Any]:
    """Apply function to dictionary keys."""
    old_keys = [key for key in dct]
    for old_key in old_keys:
        new_key = func(old_key)
        dct[new_key] = dct.pop(old_key)
    return dct


def categorical_colors() -> dict[str, str]:
    """Get a list of the categorical colors associated with certain substrings (SSP,RCP,CMIP)."""
    path = (
        pathlib.Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
    )
    with path.open(encoding="utf-8") as _f:
        cat = json.load(_f)

        return cat


def get_mpl_styles() -> dict[str, pathlib.Path]:
    """Get the available matplotlib styles and their paths as a dictionary."""
    files = sorted(pathlib.Path(__file__).parent.joinpath("style").glob("*.mplstyle"))
    styles = {style.stem: style for style in files}
    return styles


def set_mpl_style(*args: str, reset: bool = False) -> None:
    """
    Set the matplotlib style using one or more stylesheets.

    Parameters
    ----------
    args : str
        Name(s) of figanos matplotlib style ('ouranos', 'paper, 'poster') or path(s) to matplotlib stylesheet(s).
    reset : bool
        If True, reset style to matplotlib default before applying the stylesheets.

    Returns
    -------
    None
    """
    if reset is True:
        mpl.style.use("default")
    for s in args:
        if s.endswith(".mplstyle") is True:
            mpl.style.use(s)
        elif s in get_mpl_styles():
            mpl.style.use(get_mpl_styles()[s])
        else:
            warnings.warn(f"Style {s} not found.", stacklevel=2)


def add_cartopy_features(
    ax: matplotlib.axes.Axes, features: list[str] | dict[str, dict[str, Any]]
) -> matplotlib.axes.Axes:
    """
    Add cartopy features to matplotlib axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes on which to add the features.
    features : list or dict
        List of features, or nested dictionary of format {'feature': {'kwarg':'value'}}

    Returns
    -------
    matplotlib.axes.Axes
        The axis with added features.
    """
    if isinstance(features, list):
        features = {f: {} for f in features}

    for feat in features:
        if "scale" not in features[feat]:
            ax.add_feature(getattr(cfeature, feat.upper()), **features[feat])
        else:
            scale = features[feat].pop("scale")
            ax.add_feature(
                getattr(cfeature, feat.upper()).with_scale(scale),
                **features[feat],
            )
            features[feat]["scale"] = scale  # put back
    return ax


def custom_cmap_norm(
    cmap,
    vmin: int | float,
    vmax: int | float,
    levels: int | list[int | float] | None = None,
    divergent: bool | int | float = False,
    linspace_out: bool = False,
) -> matplotlib.colors.Normalize | np.ndarray:
    """
    Get matplotlib normalization according to main function arguments.

    Parameters
    ----------
    cmap: matplotlib.colormap
        Colormap to be used with the normalization.
    vmin: int or float
        Minimum of the data to be plotted with the colormap.
    vmax: int or float
        Maximum of the data to be plotted with the colormap.
    levels : int or list, optional
        Number of  levels or list of level boundaries (in data units) to use to divide the colormap.
    divergent : bool or int or float
        If int or float, becomes center of cmap. Default center is 0.
    linspace_out: bool
        If True, return array created by np.linspace() instead of normalization instance.

    Returns
    -------
    matplotlib.colors.Normalize
    """
    # get cmap if string
    if isinstance(cmap, str):
        if cmap in plt.colormaps():
            cmap = matplotlib.colormaps[cmap]
        else:
            raise ValueError("Colormap not found")

    # make vmin and vmax prettier
    if (vmax - vmin) >= 25:
        rvmax = math.ceil(vmax / 10.0) * 10
        rvmin = math.floor(vmin / 10.0) * 10
    elif 1 <= (vmax - vmin) < 25:
        rvmax = math.ceil(vmax / 1) * 1
        rvmin = math.floor(vmin / 1) * 1
    elif 0.1 <= (vmax - vmin) < 1:
        rvmax = math.ceil(vmax / 0.1) * 0.1
        rvmin = math.floor(vmin / 0.1) * 0.1
    else:
        rvmax = math.ceil(vmax / 0.01) * 0.01
        rvmin = math.floor(vmin / 0.01) * 0.01

    # center
    center = None
    if divergent is not False:
        if divergent is True:
            center = 0
        elif isinstance(divergent, int | float):
            center = divergent

    # build norm with options
    if center is not None and isinstance(levels, int):
        if center <= rvmin or center >= rvmax:
            raise ValueError("vmin, center and vmax must be in ascending order.")
        if levels % 2 == 1:
            half_levels = int((levels + 1) / 2) + 1
        else:
            half_levels = int(levels / 2) + 1

        lin = np.concatenate(
            (
                np.linspace(rvmin, center, num=half_levels),
                np.linspace(center, rvmax, num=half_levels)[1:],
            )
        )
        norm = matplotlib.colors.BoundaryNorm(boundaries=lin, ncolors=cmap.N)

        if linspace_out:
            return lin

    elif levels is not None:
        if isinstance(levels, list):
            if center is not None:
                warnings.warn(
                    "Divergent argument ignored when levels is a list. Use levels as a number instead.", stacklevel=2
                )
            norm = matplotlib.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
        else:
            lin = np.linspace(rvmin, rvmax, num=levels + 1)
            norm = matplotlib.colors.BoundaryNorm(boundaries=lin, ncolors=cmap.N)

            if linspace_out:
                return lin

    elif center is not None:
        norm = matplotlib.colors.TwoSlopeNorm(center, vmin=rvmin, vmax=rvmax)
    else:
        norm = matplotlib.colors.Normalize(rvmin, rvmax)

    return norm


def norm2range(
    data: np.ndarray, target_range: tuple, data_range: tuple | None = None
) -> np.ndarray:
    """Normalize data across a specific range."""
    if data_range is None:
        if len(data) > 1:
            data_range = (np.nanmin(data), np.nanmax(data))
        else:
            raise ValueError(" if data is not an array, data_range must be specified")

    norm = (data - data_range[0]) / (data_range[1] - data_range[0])

    return target_range[0] + (norm * (target_range[1] - target_range[0]))


def size_legend_elements(
    data: np.ndarray, sizes: np.ndarray, marker: str, max_entries: int = 6
) -> list[matplotlib.lines.Line2D]:
    """
    Create handles to use in a point-size legend.

    Parameters
    ----------
    data : np.ndarray
        Data used to determine the point sizes.
    sizes : np.ndarray
        Array of point sizes.
    max_entries : int
        Maximum number of entries in the legend.
    marker: str
        Marker to use in legend.

    Returns
    -------
    list of matplotlib.lines.Line2D
    """
    # how many increments of 10 pts**2 are there in the sizes
    n = int(np.round(max(sizes) - min(sizes), -1) / 10)

    # divide data in those increments
    lgd_data = np.linspace(min(data), max(data), n)

    # round according to range
    ratio = abs(max(data) - min(data) / n)

    if ratio >= 1000:
        rounding = 1000
    elif 100 <= ratio < 1000:
        rounding = 100
    elif 10 <= ratio < 100:
        rounding = 10
    elif 5 <= ratio < 10:
        rounding = 5
    elif 1 <= ratio < 5:
        rounding = 1
    elif 0.1 <= ratio < 1:
        rounding = 0.1
    elif 0.01 <= ratio < 0.1:
        rounding = 0.01
    else:
        rounding = 0.001

    lgd_data = np.unique(rounding * np.round(lgd_data / rounding))

    # convert back to sizes
    lgd_sizes = norm2range(
        data=lgd_data,
        data_range=(min(data), max(data)),
        target_range=(min(sizes), max(sizes)),
    )

    legend_elements = []

    for s, d in zip(lgd_sizes, lgd_data, strict=False):
        if isinstance(d, float) and d.is_integer():
            label = str(int(d))
        else:
            label = str(d)

        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                color="k",
                lw=0,
                markerfacecolor="w",
                label=label,
                markersize=np.sqrt(np.abs(s)),
            )
        )

    if len(legend_elements) > max_entries:
        return [legend_elements[i] for i in np.arange(0, max_entries + 1, 2)]
    else:
        return legend_elements


def add_features_map(
    data,
    ax,
    use_attrs,
    projection,
    features,
    geometries_kw,
    frame,
) -> matplotlib.axes.Axes:
    """
    Add features such as cartopy, time label, and geometries to a map on a given matplotlib axis.

    Parameters
    ----------
    data : dict, DataArray or Dataset
        Input data do plot. If dictionary, must have only one entry.
    ax : matplotlib axis
        Matplotlib axis on which to plot, with the same projection as the one specified.
    use_attrs : dict
        Dict linking a plot element (key, e.g. 'title') to a DataArray attribute (value, e.g. 'Description').
        Default value is {'title': 'description', 'cbar_label': 'long_name', 'cbar_units': 'units'}.
        Only the keys found in the default dict can be used.
    projection : ccrs.Projection
        The projection to use, taken from the cartopy.crs options. Ignored if ax is not None.
    features : list or dict
        Features to use, as a list or a nested dict containing kwargs. Options are the predefined features from
        cartopy.feature: ['coastline', 'borders', 'lakes', 'land', 'ocean', 'rivers', 'states'].
    geometries_kw : dict
        Arguments passed to cartopy ax.add_geometry() which adds given geometries (GeoDataFrame geometry) to axis.
    frame : bool
        Show or hide frame. Default False.

    Returns
    -------
    matplotlib.axes.Axes
    """
    # add features
    if features:
        add_cartopy_features(ax, features)

    set_plot_attrs(use_attrs, data, ax)

    if frame is False:
        ax.spines["geo"].set_visible(False)

    # add geometries
    if geometries_kw:
        if "geoms" not in geometries_kw.keys():
            warnings.warn(
                'geoms missing from geometries_kw (ex: {"geoms": df["geometry"]})', stacklevel=2
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


def masknan_sizes_key(data, sizes) -> xr.Dataset:
    """
    Mask the np.Nan values between variables used to plot hue and markersize in xr.plot.scatter().

    Parameters
    ----------
    data: xr.Dataset
        xr.Dataset used to plot
    sizes: str
        Variable used to plot markersize

    Returns
    -------
    xr.Dataset
    """
    # find variable name
    kl = list(data.keys())
    kl.remove(sizes)
    key = kl[0]

    # Create a mask for missing 'sizes' data
    size_mask = np.isnan(data[sizes])

    # Set 'key' values to NaN where 'sizes' is missing
    data[key] = data[key].where(~size_mask)

    # Create a mask for missing 'key' data
    key_mask = np.isnan(data[key])

    # Set 'sizes' values to NaN where 'key' is missing
    data[sizes] = data[sizes].where(~key_mask)
    return data
