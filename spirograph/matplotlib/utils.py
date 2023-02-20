import pandas as pd
import re
import warnings
import xarray as xr
import matplotlib as mpl
import numpy as np

warnings.simplefilter('always', UserWarning)


def empty_dict(param):
    """ Return empty dict if input is None. """
    if param is None:
        param = {}
    return param


def check_timeindex(xr_dict):
    """ Check if the time index of Xarray objects in a dict is CFtime
    and convert to pd.DatetimeIndex if True.

    Parameters
    _________
    xr_dict: dict
        Dictionary containing Xarray DataArrays or Datasets.
    Returns
    _______
    dict
    """

    for name, xr_obj in xr_dict.items():
        if 'time' in xr_obj.dims:
            if isinstance(xr_obj.get_index('time'), xr.CFTimeIndex):
                conv_obj = xr_obj.convert_calendar('standard', use_cftime=None)
                xr_dict[name] = conv_obj
        else:
            raise ValueError('"time" dimension not found in {}'.format(xr_obj))
    return xr_dict


def get_array_categ(array):
    """Return an array category, which determines how to plot.

    Parameters
    __________
    array: Dataset or DataArray
        The array being categorized.

    Returns
    _________
    array: str
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
        if pd.notnull([re.search("_p[0-9]{1,2}", var) for var in array.data_vars]).sum() >= 2:
            cat = "ENS_PCT_VAR_DS"
        elif pd.notnull([re.search("_[Mm]ax|_[Mm]in", var) for var in array.data_vars]).sum() >= 2:
            cat = "ENS_STATS_VAR_DS"
        elif 'percentiles' in array.dims:
            cat = "ENS_PCT_DIM_DS"
        elif 'realization' in array.dims:
            cat = "ENS_REALS_DS"
        else:
            cat = "DS"

    elif isinstance(array, xr.DataArray):
        if 'percentiles' in array.dims:
            cat = "ENS_PCT_DIM_DA"
        elif 'realization' in array.dims:
            cat = "ENS_REALS_DA"
        else:
            cat = "DA"
    else:
        raise TypeError('Array is not an Xarray Dataset or DataArray')

    return cat


def get_attributes(string, xr_obj):
    """
    Fetch attributes or dims corresponding to keys from Xarray objects. Look in
    Dataset attributes first, then in the first variable (DataArray) of the Dataset.

    Parameters
    _________
    string: str
        String corresponding to an attribute name.
    xr_obj: DataArray or Dataset
        The Xarray object containing the attributes.

    Returns
    _______
    str
        Xarray attribute value as string or empty string if not found
    """
    if string in xr_obj.attrs:
        return xr_obj.attrs[string]

    elif isinstance(xr_obj, xr.Dataset) and string in xr_obj[list(xr_obj.data_vars)[0]].attrs: # DataArray of first variable
        return xr_obj[list(xr_obj.data_vars)[0]].attrs[string]

    else:
        warnings.warn('Attribute "{}" not found.'.format(string))
        return ''


def set_plot_attrs(attr_dict, xr_obj, ax):
    """
    Set plot elements according to Dataset or DataArray attributes.  Uses get_attributes()
    to check for and return the string.

    Parameters
    __________
    attr_dict: dict
        Dictionary containing specified attribute keys.
    xr_obj: Dataset or DataArray
        The Xarray object containing the attributes.
    ax: matplotlib axis
        The matplotlib axis of the plot.
    Returns
    ______
    matplotlib axis

    """
    #  check
    for key in attr_dict:
        if key not in ['title', 'ylabel', 'yunits']:
            warnings.warn('Use_attrs element "{}" not supported'.format(key))

    ax.set_xlabel('time') #  check_timeindex() already checks for 'time'

    if 'title' in attr_dict:
        ax.set_title(get_attributes(attr_dict['title'], xr_obj), wrap=True)

    if 'ylabel' in attr_dict:
        if 'yunits' in attr_dict and len(get_attributes(attr_dict['yunits'], xr_obj)) >= 1: # second condition avoids '[]' as label
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj) + ' (' +
                      get_attributes(attr_dict['yunits'], xr_obj) + ')')
        else:
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj))
    return ax


def get_suffix(string):
    """ Get suffix of typical Xclim variable names. """
    if re.search("[0-9]{1,2}$|_[Mm]ax$|_[Mm]in$|_[Mm]ean$", string):
        suffix = re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", string).group()
        return suffix
    else:
        raise Exception('No suffix found in {}'.format(string))


def sort_lines(array_dict):
    """
    Label arrays as 'middle', 'upper' and 'lower' for ensemble plotting.

    Parameters
    _______
    array_dict: dict
        Dictionary of format {'name': array...}.

    Returns
    _______
    dict
        Dictionary of {'middle': 'name', 'upper': 'name', 'lower': 'name'}.
    """
    if len(array_dict) != 3:
        raise ValueError('Ensembles must contain exactly three arrays')

    sorted_lines = {}

    for name in array_dict.keys():
        suffix = get_suffix(name)

        if suffix.isalpha():
            if suffix in ['max', 'Max']:
                sorted_lines['upper'] = name
            elif suffix in ['min', 'Min']:
                sorted_lines['lower'] = name
            elif suffix in ['mean', 'Mean']:
                sorted_lines['middle'] = name
        elif suffix.isdigit():
            if int(suffix) >= 51:
                sorted_lines['upper'] = name
            elif int(suffix) <= 49:
                sorted_lines['lower'] = name
            elif int(suffix) == 50:
                sorted_lines['middle'] = name
        else:
            raise Exception('Arrays names must end in format "_mean" or "_p50" ')
    return sorted_lines


def plot_lat_lon(ax, xr_obj):
    """ Place lat, lon coordinates on bottom right of plot area."""
    if 'lat' in xr_obj.coords and 'lon' in xr_obj.coords:
        text = 'lat={:.2f}, lon={:.2f}'.format(float(xr_obj['lat']),
                                               float(xr_obj['lon']))
        ax.text(0.99, 0.01, text, transform=ax.transAxes, ha = 'right', va = 'bottom')
    else:
        warnings.warn('show_lat_lon set to True, but "lat" and/or "lon" not found in coords')
    return ax


def split_legend(ax, in_plot = False, axis_factor=0.15, label_gap=0.02):
    #  TODO: check for and fix overlapping labels
    """
    Drawline labels at the end of each line, or outside the plot.

    Parameters
    _______
    ax: matplotlib axis
        The axis containing the legend.
    in_plot: bool (default False)
        If True, prolong plot area to fit labels. If False, print labels outside of plot area.
    axis_factor: float (default 0.15)
        If in_plot is True, fraction of the x-axis length to add at the far right of the plot.
    label_gap: float (default 0.02)
        If in_plot is True, fraction of the x-axis length to add as a gap between line and label.

    Returns
    ______
        matplotlib axis
    """

    #create extra space
    init_xbound = ax.get_xbound()

    ax_bump = (init_xbound[1] - init_xbound[0]) * axis_factor
    label_bump = (init_xbound[1] - init_xbound[0]) * label_gap

    if in_plot is True:
        ax.set_xbound(lower=init_xbound[0], upper=init_xbound[1] + ax_bump)

    #get legend and plot

    handles, labels = ax.get_legend_handles_labels()
    for handle, label in zip(handles, labels):

        last_x = handle.get_xdata()[-1]
        last_y = handle.get_ydata()[-1]

        if isinstance(last_x, np.datetime64):
            last_x = mpl.dates.date2num(last_x)

        color = handle.get_color()
        ls = handle.get_linestyle()

        if in_plot is True:
            ax.text(last_x + label_bump, last_y, label,
                    ha='left', va='center', color=color)
        else:
            trans = mpl.transforms.blended_transform_factory(ax.transAxes, ax.transData)
            ax.text(1.01, last_y, label, ha='left', va='center', color=color, transform=trans)

    return ax

def fill_between_label(sorted_lines, name, array_categ, legend):
    """ Create label for shading in line plots."""
    if legend != 'full':
        label = None
    elif array_categ[name] in ['ENS_PCT_VAR_DS','ENS_PCT_DIM_DS','ENS_PCT_DIM_DA']:
        label = "{}th-{}th percentiles".format(get_suffix(sorted_lines['lower']),
                                               get_suffix(sorted_lines['upper']))
    elif array_categ[name] == 'ENS_STATS_VAR_DS':
        label = 'min-max range'
    else:
        label = None

    return label
