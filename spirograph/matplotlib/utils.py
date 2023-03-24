import json
import re
import warnings
from pathlib import Path
from typing import Any, Dict, Union

import cartopy.crs as ccrs
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


def check_timeindex(xr_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the time index of Xarray objects in a dict is CFtime
    and convert to pd.DatetimeIndex if True.

    Parameters
    ----------
    xr_dict: dict
        Dictionary containing Xarray DataArrays or Datasets.

    Returns
    -------
    dict
    """

    for name, xr_obj in xr_dict.items():
        if "time" in xr_obj.dims:
            if isinstance(xr_obj.get_index("time"), xr.CFTimeIndex):
                conv_obj = xr_obj.convert_calendar("standard", use_cftime=None)
                xr_dict[name] = conv_obj
        else:
            raise ValueError(f'"time" dimension not found in {xr_obj}')
    return xr_dict


def get_array_categ(array: Union[xr.DataArray, xr.Dataset]) -> str:
    """Return an array category, which determines how to plot.

    Parameters
    __________
    array: Dataset or DataArray
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
            pd.notnull([re.search("_p[0-9]{1,2}", v) for v in array.data_vars]).sum()
            >= 2
        ):
            cat = "ENS_PCT_VAR_DS"
        elif (
            pd.notnull([re.search("_[Mm]ax|_[Mm]in", v) for v in array.data_vars]).sum()
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


def get_attributes(string: str, xr_obj: Union[xr.DataArray, xr.Dataset]) -> str:
    """
    Fetch attributes or dims corresponding to keys from Xarray objects. Look in DataArray attributes first,
    then the first variable (DataArray) of the Dataset, then the Dataset attributes.

    Parameters
    ----------
    string: str
        String corresponding to an attribute name.
    xr_obj: DataArray or Dataset
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
    attr_dict: Dict[str, Any],
    xr_obj: Union[xr.DataArray, xr.Dataset],
    ax: matplotlib.axes.Axes,
) -> matplotlib.axes.Axes:
    """
    Set plot elements according to Dataset or DataArray attributes.  Uses get_attributes()
    to check for and return the string.

    Parameters
    ----------
    attr_dict: dict
        Dictionary containing specified attribute keys.
    xr_obj: Dataset or DataArray
        The Xarray object containing the attributes.
    ax: matplotlib axis
        The matplotlib axis of the plot.

    Returns
    -------
    matplotlib.axes.Axes
    """
    #  check
    for key in attr_dict:
        if key not in ["title", "ylabel", "yunits", "cbar_label", "cbar_units"]:
            warnings.warn(f'Use_attrs element "{key}" not supported')

    if "title" in attr_dict:
        title = get_attributes(attr_dict["title"], xr_obj)
        ax.set_title(wrap_text(title))

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
        raise Exception(f"No suffix found in {string}")


def sort_lines(array_dict: Dict[str, Any]) -> Dict[str, str]:
    """Label arrays as 'middle', 'upper' and 'lower' for ensemble plotting.

    Parameters
    ----------
    array_dict: dict
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
            raise Exception('Arrays names must end in format "_mean" or "_p50" ')
    return sorted_lines


def plot_coords(
    ax: matplotlib.axes.Axes,
    xr_obj: Union[xr.DataArray, xr.Dataset],
    param: str = None,
    backgroundalpha: int = 0,
) -> matplotlib.axes.Axes:
    """Place coordinates on bottom right of plot area. Param options are 'location' or 'time'."""
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
            text = np.datetime_as_string(xr_obj.time.values, unit="D")
        else:
            warnings.warn('show_time set to True, but "time" not found in coords')

    if text:
        t = ax.text(0.98, 0.03, text, transform=ax.transAxes, ha="right", va="bottom")
        t.set_bbox(dict(facecolor="w", alpha=backgroundalpha, edgecolor="w"))

    return ax


def split_legend(
    ax: matplotlib.axes.Axes,
    in_plot: bool = False,
    axis_factor: float = 0.15,
    label_gap: float = 0.02,
) -> matplotlib.axes.Axes:
    #  TODO: check for and fix overlapping labels
    """Drawline labels at the end of each line, or outside the plot.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        The axis containing the legend.
    in_plot: bool
        If True, prolong plot area to fit labels. If False, print labels outside of plot area. Default: False.
    axis_factor: float
        If in_plot is True, fraction of the x-axis length to add at the far right of the plot. Default: 0.15.
    label_gap: float
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
    sorted_lines: Dict[str, Any], name: str, array_categ: Dict[str, Any], legend: str
) -> str:
    """Create label for shading in line plots."""
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


def get_var_group(da: xr.DataArray, path_to_json: Union[str, Path]) -> str:
    """Get IPCC variable group from DataArray using a json file (spirograph/data/ipcc_colors/variable_groups.json)."""

    # create dict
    with open(path_to_json) as f:
        var_dict = json.load(f)

    matches = []

    # look in DataArray name
    if hasattr(da, "name"):
        for v in var_dict:
            regex = rf"(?:^|[^a-zA-Z])({v})(?:[^a-zA-Z]|$)"
            if re.search(regex, da.name):
                matches.append(var_dict[v])

    # look in history
    if hasattr(da, "history") and len(matches) == 0:
        for v in var_dict:
            regex = rf"(?:^|[^a-zA-Z])({v})(?:[^a-zA-Z]|$)"  # matches when variable is not inside word
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
    var_group: str = None,
    levels: int = None,
    divergent: Union[int, float, bool] = False,
    filename: str = None,
) -> matplotlib.colors.Colormap:
    """Create colormap according to variable group.

    Parameters
    ----------
    var_group: str
        Variable group from IPCC scheme.
    levels: int
        Number of levels for discrete colormaps. Must be between 2 and 21, inclusive. If None, use continuous colormap.
    divergent: bool or int, float
        Diverging colormap. If False, use sequential colormap.
    filename: str
        Name of IPCC colormap file. If not None, 'var_group' and 'divergent' are not used.

    Returns
    -------
    matplotlib.colors.Colormap
    """

    # func to get position of sequential cmap in txt file
    def skip_rows(levels: int) -> int:
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
    path = Path(__file__).parents[1] / "data/ipcc_colors" / folder / (filename + ".txt")

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


def cbar_ticks(plot_obj: matplotlib.axes.Axes, levels: int):
    """create list of ticks for colorbar based on DataArray values, to avoid crowded ax."""
    vmin = plot_obj.colorbar.vmin
    vmax = plot_obj.colorbar.vmax

    ticks = np.linspace(vmin, vmax, levels + 1)

    # if there are more than 7 levels, return every second label
    if levels >= 7:
        ticks = [ticks[i] for i in np.arange(0, len(ticks), 2)]

    return ticks


def get_rotpole(xr_obj: Union[xr.DataArray, xr.Dataset]):
    try:
        rotpole = ccrs.RotatedPole(
            pole_longitude=xr_obj.rotated_pole.grid_north_pole_longitude,
            pole_latitude=xr_obj.rotated_pole.grid_north_pole_latitude,
            central_rotated_longitude=xr_obj.rotated_pole.north_pole_grid_longitude,
        )
        return rotpole

    # FIXME: what kinds of exceptions can be raised here?
    except:  # noqa
        warnings.warn("Rotated pole not found. Specify a transform if necessary.")
        return None


def wrap_text(text: str, threshold: int = 30, min_line_len: int = 12) -> str:
    """Wrap text from characters or central whitespace."""
    if len(text) >= threshold:
        if ". " in text:
            text = text.replace(". ", ".\n")
        if ": " in text:
            text = text.replace(": ", ":\n")
        if ". " not in text and ": " not in text:  # if neither, find the middle space.
            center = len(text) // 2
            spaces = [
                m.start() for m in re.finditer(r"\s", text)
            ]  # position of whitespaces
            relative = [abs(s - center) for s in spaces]
            central = spaces[np.argmin(relative)]
            text = text[:central] + "\n" + text[central + 1 :]

        # if one of the middle lines is too short, put it back.
        lines = text.splitlines(keepends=True)
        if len(lines) > 2:
            lengths = [len(line) for line in lines[1:-1]]
            for line_len, i in zip(lengths, range(len(lengths))):
                if line_len < min_line_len:
                    lines[i] = lines[i].replace("\n", " ")
            sep = ""
            text = sep.join(lines)

    return text


def gpd_to_ccrs(df, proj):
    """Opens shapefile with geopandas and convert to cartopy projection.

    Parameters
    ----------
    df: GeoDataFrame
        GeoDataFrame (geopandas) geometry to be added to axis.
    proj: ccrs projection
        Projection to use, taken from the cartopy.crs options.

    Returns
    --------
    GeoDataFrame
        GeoDataFrame adjusted to given projection
    """
    prj4 = proj.proj4_init
    return df.to_crs(prj4)


def convert_scen_name(name: str) -> str:
    """Convert SSP, RCP, CMIP strings to proper format"""

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


def get_scen_color(name, path_to_dict):
    """Get color corresponding to SSP,RCP, model or CMIP substring."""
    with open(path_to_dict) as f:
        color_dict = json.load(f)

    color = None
    for entry in color_dict:
        if entry in name:
            color = color_dict[entry]
            break

    return color


def process_keys(dict, function):
    old_keys = [key for key in dict]
    for old_key in old_keys:
        new_key = function(old_key)
        dict[new_key] = dict.pop(old_key)
    return dict


def categorical_colors():
    """Return a list of the categorical colors associated with certain strings (SSP,RCP,CMIP)."""
    path = Path(__file__).parents[1] / "data/ipcc_colors/categorical_colors.json"
    with open(path) as f:
        cat = json.load(f)

        return cat


def get_mpl_styles():
    """Get the available matplotlib styles and their paths, as a dictionary."""
    folder = Path(__file__).parent / "style/"
    paths = sorted(folder.glob("*.mplstyle"))
    names = [str(p).split("/")[-1].removesuffix(".mplstyle") for p in paths]
    styles = {name: path for name, path in zip(names, paths)}

    return styles


def set_mpl_style(*args: str, reset: bool = False):
    """Set the matplotlib style using one or more stylesheets.

    Parameters
    ----------
    args: str
        Name(s) of spirograph matplotlib style ('ouranos', 'paper, 'poster') or path(s) to matplotlib stylesheet(s).
    reset: bool
        If True, reset style to matplotlib default before applying the stylesheets.
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
