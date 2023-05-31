from __future__ import annotations

import json
import math
import pathlib
import re
import warnings
from typing import Any, Callable

import cartopy.crs as ccrs
import cartopy.feature as cfeature  # noqa
import geopandas as gpd
import matplotlib as mpl
import matplotlib.axes
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import xarray as xr

warnings.simplefilter("always", UserWarning)


def empty_dict(param):
    """Return empty dict if input is None."""
    if param is None:
        param = {}
    return param


def check_timeindex(
    xr_objs: xr.DataArray | xr.Dataset | dict[str, Any]
) -> xr.DataArray | xr.Dataset | dict[str, Any]:
    """Check if the time index of Xarray objects in a dict is CFtime
    and convert to pd.DatetimeIndex if True.

    Parameters
    ----------
    xr_dict : dict
        Dictionary containing Xarray DataArrays or Datasets.

    Returns
    -------
    dict
        Dictionary of xarray objects with a pandas DatetimeIndex
    """
    if isinstance(xr_objs, dict):
        for name, obj in xr_objs.items():
            if "time" in obj.dims:
                if isinstance(obj.get_index("time"), xr.CFTimeIndex):
                    conv_obj = obj.convert_calendar("standard", use_cftime=None)
                    xr_objs[name] = conv_obj
                    warnings.warn(
                        "CFTimeIndex converted to pandas DatetimeIndex with a 'standard' calendar."
                    )

    else:
        if "time" in xr_objs.dims:
            if isinstance(xr_objs.get_index("time"), xr.CFTimeIndex):
                conv_obj = xr_objs.convert_calendar("standard", use_cftime=None)
                xr_objs = conv_obj
                warnings.warn(
                    "CFTimeIndex converted to pandas DatetimeIndex with a 'standard' calendar."
                )

    return xr_objs


def get_array_categ(array: xr.DataArray | xr.Dataset) -> str:
    """Get an array category, which determines how to plot the array.

    Parameters
    __________
    array : Dataset or DataArray
        The array being categorized.

    Returns
    _________
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


def get_attributes(string: str, xr_obj: xr.DataArray | xr.Dataset) -> str:
    """
    Fetch attributes or dims corresponding to keys from Xarray objects. Look in DataArray attributes first,
    then the first variable (DataArray) of the Dataset, then the Dataset attributes.

    Parameters
    ----------
    string : str
        String corresponding to an attribute name.
    xr_obj : DataArray or Dataset
        The Xarray object containing the attributes.

    Returns
    -------
    str
        Xarray attribute value as string or empty string if not found
    """
    if isinstance(xr_obj, xr.DataArray) and string in xr_obj.attrs:
        return xr_obj.attrs[string]

    elif (
        isinstance(xr_obj, xr.Dataset)
        and string in xr_obj[list(xr_obj.data_vars)[0]].attrs
    ):  # DataArray of first variable
        return xr_obj[list(xr_obj.data_vars)[0]].attrs[string]

    elif isinstance(xr_obj, xr.Dataset) and string in xr_obj.attrs:
        return xr_obj.attrs[string]

    else:
        warnings.warn(f'Attribute "{string}" not found.')
        return ""


def set_plot_attrs(
    attr_dict: dict[str, Any],
    xr_obj: xr.DataArray | xr.Dataset,
    ax: matplotlib.axes.Axes,
    title_loc: str = "center",
    wrap_kw: dict[str, Any] | None = None,
) -> matplotlib.axes.Axes:
    """
    Set plot elements according to Dataset or DataArray attributes.  Uses get_attributes()
    to check for and get the string.

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
        ]:
            warnings.warn(f'Use_attrs element "{key}" not supported')

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

    return ax


def get_suffix(string: str) -> str:
    """Get suffix of typical Xclim variable names."""
    if re.search("[0-9]{1,2}$|_[Mm]ax$|_[Mm]in$|_[Mm]ean$", string):
        suffix = re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", string).group()
        return suffix
    else:
        raise ValueError(f"Mean, min or max not found in {string}")


def sort_lines(array_dict: dict[str, Any]) -> dict[str, str]:
    """Label arrays as 'middle', 'upper' and 'lower' for ensemble plotting.

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


def plot_coords(
    ax: matplotlib.axes.Axes,
    xr_obj: xr.DataArray | xr.Dataset,
    loc: str | tuple[float, float] | int,
    param: str | None = None,
    backgroundalpha: float = 1,
) -> matplotlib.axes.Axes:
    """Place coordinates on bottom right of plot area.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes object on which to place the text.
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
                'show_lat_lon set to True, but "lat" and/or "lon" not found in coords'
            )
    if param == "time":
        if "time" in xr_obj.coords:
            text = str(xr_obj.time.dt.strftime("%Y-%m-%d").values)

        else:
            warnings.warn('show_time set to True, but "time" not found in coords')

    # location
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
        except IndexError:
            raise ValueError("loc must be between 1 and 10, inclusively")

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
        elif loc == "upper left":
            loc = (0.03, 0.97)
        elif loc == "lower left":
            loc = (0.03, 0.03)
        elif loc == "lower right":
            loc = (0.97, 0.03)
        elif loc == "right":
            loc = (0.97, 0.5)
        elif loc == "center left":
            loc = (0.03, 0.5)
        elif loc == "center right":
            loc = (0.97, 0.5)
        elif loc == "lower center":
            loc = (0.5, 0.03)
        elif loc == "upper center":
            loc = (0.5, 0.97)
        elif loc == "center":
            loc = (0.5, 0.5)

    elif isinstance(loc, tuple):
        for i in loc:
            if i > 1 or i < 0:
                raise ValueError(
                    "Text location coordinates must be between 0 and 1, inclusively"
                )

    if text:
        t = ax.text(loc[0], loc[1], text, transform=ax.transAxes, ha=ha, va=va)
        t.set_bbox(dict(facecolor="w", alpha=backgroundalpha, edgecolor="w"))

    return ax


def split_legend(
    ax: matplotlib.axes.Axes,
    in_plot: bool = False,
    axis_factor: float = 0.15,
    label_gap: float = 0.02,
) -> matplotlib.axes.Axes:
    #  TODO: check for and fix overlapping labels
    """Draw line labels at the end of each line, or outside the plot.

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
    for handle, label in zip(handles, labels):
        last_x = handle.get_xdata()[-1]
        last_y = handle.get_ydata()[-1]

        if isinstance(last_x, np.datetime64):
            last_x = mpl.dates.date2num(last_x)

        color = handle.get_color()
        # ls = handle.get_linestyle()

        if in_plot is True:
            ax.text(
                last_x + label_bump, last_y, label, ha="left", va="center", color=color
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
    sorted_lines: dict[str, Any], name: str, array_categ: dict[str, Any], legend: str
) -> str:
    """Create a label for the shading around a line in line plots.

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
    elif array_categ[name] in ["ENS_PCT_VAR_DS", "ENS_PCT_DIM_DS", "ENS_PCT_DIM_DA"]:
        label = "{}th-{}th percentiles".format(
            get_suffix(sorted_lines["lower"]), get_suffix(sorted_lines["upper"])
        )
    elif array_categ[name] == "ENS_STATS_VAR_DS":
        label = "min-max range"
    else:
        label = None

    return label


def get_var_group(
    path_to_json: str | pathlib.Path,
    da: xr.DataArray | None = None,
    unique_str: str = None,
) -> str:
    """Get IPCC variable group from DataArray or a string using a json file (spirograph/data/ipcc_colors/variable_groups.json).
    If da is a Dataset,  look in the DataArray of the first variable."""

    # create dict
    with open(path_to_json) as f:
        var_dict = json.load(f)

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
            "Colormap warning: Variable group not found. Use the cmap argument."
        )
        return "misc"
    elif len(matches) >= 2:
        warnings.warn(
            "Colormap warning: More than one variable group found. Use the cmap argument."
        )
        return "misc"
    else:
        return matches[0]


def create_cmap(
    var_group: str | None = None,
    levels: int | None = None,
    divergent: bool = False,
    filename: str | None = None,
) -> matplotlib.colors.Colormap:
    """Create colormap according to variable group.

    Parameters
    ----------
    var_group : str, optional
        Variable group from IPCC scheme.
    levels : int, optional
        Number of levels for discrete colormaps. Must be between 2 and 21, inclusive. If None, use continuous colormap.
    divergent : bool
        Diverging colormap. If False, use sequential colormap.
    filename : str, optional
        Name of IPCC colormap file. If not None, 'var_group' and 'divergent' are not used.

    Returns
    -------
    matplotlib.colors.Colormap
    """

    # func to get position of sequential cmap in txt file
    def skip_rows(levels: int) -> int:
        """Get number of rows to skip depending on levels."""
        skiprows = 1

        if levels > 5:
            for i in np.arange(5, levels):
                skiprows += i + 1
        return skiprows

    if filename:
        if "disc" in filename:
            folder = "discrete_colormaps_rgb_0-255"
        else:
            folder = "continuous_colormaps_rgb_0-255"

        filename = filename.replace(".txt", "")

    else:
        # filename
        if divergent is not False:
            filename = var_group + "_div"
        else:
            if var_group == "misc":
                filename = var_group + "_seq_3"  # Batlow
            else:
                filename = var_group + "_seq"

        # continuous or discrete
        if levels:
            folder = "discrete_colormaps_rgb_0-255"
            filename = filename + "_disc"
        else:
            folder = "continuous_colormaps_rgb_0-255"

    # parent should be 'spirograph/'
    path = (
        pathlib.Path(__file__).parents[1]
        / "data/ipcc_colors"
        / folder
        / (filename + ".txt")
    )

    if levels:
        rgb_data = np.loadtxt(path, skiprows=skip_rows(levels), max_rows=levels)
    else:
        rgb_data = np.loadtxt(path)

    # convert to 0-1 RGB
    rgb_data = rgb_data / 255

    if levels or "_disc" in filename:
        N = levels
    else:
        N = 256  # default value

    cmap = mcolors.LinearSegmentedColormap.from_list("cmap", rgb_data, N=N)

    return cmap


def cbar_ticks(plot_obj: matplotlib.axes.Axes, levels: int) -> list:
    """Create a list of ticks for the colorbar based on data, to avoid crowded ax."""
    vmin = plot_obj.colorbar.vmin
    vmax = plot_obj.colorbar.vmax

    ticks = np.linspace(vmin, vmax, levels + 1)

    # if there are more than 7 levels, return every second label
    if levels >= 7:
        ticks = [ticks[i] for i in np.arange(0, len(ticks), 2)]

    return ticks


def get_rotpole(xr_obj: xr.DataArray | xr.Dataset) -> ccrs.RotatedPole | None:
    """Create a Cartopy crs rotated pole projection/transform from DataArray or Dataset attributes.

    Parameters
    ----------
    xr_obj : xr.DataArray or xr.Dataset
        The xarray object from which to look for the attributes.

    Returns
    -------
    ccrs.RotatedPole or None
    """
    try:
        rotpole = ccrs.RotatedPole(
            pole_longitude=xr_obj.rotated_pole.grid_north_pole_longitude,
            pole_latitude=xr_obj.rotated_pole.grid_north_pole_latitude,
            central_rotated_longitude=xr_obj.rotated_pole.north_pole_grid_longitude,
        )
        return rotpole

    except AttributeError:  # noqa
        warnings.warn("Rotated pole not found. Specify a transform if necessary.")
        return None


def wrap_text(text: str, min_line_len: int = 18, max_line_len: int = 30) -> str:
    """Wrap text.

    Arguments
    ---------
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
                warnings.warn("No spaces, points or colons to break line at.")
                break

            text = sep.join([text[:pos], text[pos + 1 :]])

            remaining = len(text) - len(text[:pos])
            start = pos + 1 + min_line_len
            stop = pos + 1 + max_line_len

    return text


def gpd_to_ccrs(df: gpd.GeoDataFrame, proj: ccrs.CRS) -> gpd.GeoDataFrame:
    """Open shapefile with geopandas and convert to cartopy projection.

    Parameters
    ----------
    df : gpd.GeoDataFrame
        GeoDataFrame (geopandas) geometry to be added to axis.
    proj : ccrs.CRS
        Projection to use, taken from the cartopy.crs options.

    Returns
    --------
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
    with open(path_to_dict) as f:
        color_dict = json.load(f)

    color = None
    for entry in color_dict:
        if entry in name:
            color = color_dict[entry]
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
    with open(path) as f:
        cat = json.load(f)

        return cat


def get_mpl_styles() -> dict[str, str]:
    """Get the available matplotlib styles and their paths, as a dictionary."""
    folder = pathlib.Path(__file__).parent / "style/"
    paths = sorted(folder.glob("*.mplstyle"))
    names = [str(p).split("/")[-1].removesuffix(".mplstyle") for p in paths]
    styles = {name: path for name, path in zip(names, paths)}

    return styles


def set_mpl_style(*args: str, reset: bool = False) -> None:
    """Set the matplotlib style using one or more stylesheets.

    Parameters
    ----------
    args : str
        Name(s) of spirograph matplotlib style ('ouranos', 'paper, 'poster') or path(s) to matplotlib stylesheet(s).
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
            warnings.warn(f"Style {s} not found.")


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

    for f in features:
        if "scale" not in features[f]:
            ax.add_feature(getattr(cfeature, f.upper()), **features[f])
        else:
            scale = features[f].pop("scale")
            ax.add_feature(
                getattr(cfeature, f.upper()).with_scale(scale), **features[f]
            )
            features[f]["scale"] = scale  # put back
    return ax


def custom_cmap_norm(
    cmap,
    vmin: int | float,
    vmax: int | float,
    levels: int | list[int | float] | None = None,
    divergent: bool | int | float = False,
) -> matplotlib.colors.Normalize:
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

    Returns
    -------
    matplotlib.colors.Normalize

    """

    # make vmin and vmax prettier
    if (vmax - vmin) >= 25:
        rvmax = np.round(math.ceil(vmax), -1)
        rvmin = np.round(math.floor(vmin), -1)
    elif 1 <= (vmax - vmin) < 25:
        rvmax = np.round(math.ceil(vmax), 0)
        rvmin = np.round(math.floor(vmin), 0)
    elif 0.1 <= (vmax - vmin) < 1:
        rvmax = np.round(math.ceil(vmax), 1)
        rvmin = np.round(math.floor(vmin), 1)
    else:
        rvmax = np.round(math.ceil(vmax), 2)
        rvmin = np.round(math.floor(vmin), 2)

    # center
    center = None
    if divergent:
        if divergent is True:
            center = 0
        else:
            center = divergent

    # build norm with options
    if levels and center:
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
    elif levels:
        if isinstance(levels, list):
            norm = matplotlib.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
        else:
            lin = np.linspace(rvmin, rvmax, num=levels + 1)
            norm = matplotlib.colors.BoundaryNorm(boundaries=lin, ncolors=cmap.N)

    elif center:
        norm = matplotlib.colors.TwoSlopeNorm(center, vmin=rvmin, vmax=rvmax)
    else:
        norm = matplotlib.colors.Normalize(rvmin, rvmax)

    return norm
