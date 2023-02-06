import pandas as pd
import re
import warnings
import xarray as xr
import matplotlib as mpl


def empty_dict(param):
    """ returns empty dict if input is None"""
    if param is None:
        param = {}
    return param


def check_timeindex(xr_dict):
    """ checks if the time index of Xarray objects in a dict is CFtime
    and converts to pd.DatetimeIndex if true

    Parameters
    _________
    xr_dict: dict
        dictionary containing Xarray DataArrays or Datasets
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
    """Returns an array category, which determines how to plot

    Parameters
    __________
    array: Dataset or DataArray

    Returns
    _________
    str
        PCT_VAR_ENS: ensemble of percentiles stored as variables
        PCT_DIM_ENS_DA: ensemble of percentiles stored as dimension coordinates, DataArray
        STATS_VAR_ENS: ensemble of statistics (min, mean, max) stored as variables
        DS: any Dataset that is not  recognized as an ensemble
        DA: DataArray
    """
    if isinstance(array, xr.Dataset):
        if pd.notnull([re.search("_p[0-9]{1,2}", var) for var in array.data_vars]).sum() >=2:
            cat = "PCT_VAR_ENS"
        elif pd.notnull([re.search("[Mm]ax|[Mm]in", var) for var in array.data_vars]).sum() >= 2:
            cat = "STATS_VAR_ENS"
        elif pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
            cat = "PCT_DIM_ENS_DS"  # placeholder, no support for now
        else:
            cat = "DS"

    elif isinstance(array, xr.DataArray):
        if pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
           cat = "PCT_DIM_ENS_DA"
        else:
            cat = "DA"
    else:
        raise TypeError('Array is not an Xarray Dataset or DataArray')

    return cat


def get_attributes(string, xr_obj):
    """
    Fetches attributes or dims corresponding to keys from Xarray objects. Looks in
    Dataset attributes first, then looks in DataArray.

    Parameters
    _________
    string: str
        string corresponding to an attribute name
    xr_obj: DataArray or Dataset
        the Xarray object containing the attributes

    Returns
    _______
    str
        Xarray attribute value as string or empty string if not found
    """
    if string in xr_obj.attrs:
        return xr_obj.attrs[string]

    elif string in xr_obj.dims:
        return string  # special case for 'time' because DataArray and Dataset dims are not the same types

    elif isinstance(xr_obj, xr.Dataset):
        if string in xr_obj[list(xr_obj.data_vars)[0]].attrs:  # DataArray of first variable
            return xr_obj[list(xr_obj.data_vars)[0]].attrs[string]

        else:
            warnings.warn('Attribute "{0}" not found in attributes'.format(string))
            return '' ## would it be better to return None? if so, need to fix ylabel in set_plot_attrs()


def set_plot_attrs(attr_dict, xr_obj, ax):
    """
    Sets plot elements according to Dataset or DataArray attributes.  Uses get_attributes()
    to check for and return the string.

    Parameters
    __________
    use_attrs: dict
        dictionary containing specified attribute keys
    xr_obj: Dataset or DataArray
        The Xarray object containing the attributes
    ax: matplotlib axis
        the matplotlib axis
    Returns
    ______
    matplotlib axis

    """
    #  check
    for key in attr_dict:
        if key not in ['title','xlabel', 'ylabel', 'yunits']:
            warnings.warn('Use_attrs element "{}" not supported'.format(key))

    if 'title' in attr_dict:
        ax.set_title(get_attributes(attr_dict['title'], xr_obj), wrap=True)

    if 'xlabel' in attr_dict:
        ax.set_xlabel(get_attributes(attr_dict['xlabel'], xr_obj))

    if 'ylabel' in attr_dict:
        if 'yunits' in attr_dict and len(get_attributes(attr_dict['yunits'], xr_obj)) >= 1: # second condition avoids '[]' as label
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj) + ' (' +
                      get_attributes(attr_dict['yunits'], xr_obj) + ')')
        else:
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj))
    return ax


def get_suffix(string):
    """ get suffix of typical Xclim variable names"""
    if re.search("[0-9]{1,2}$|_[Mm]ax$|_[Mm]in$|_[Mm]ean$", string):
        suffix = re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", string).group()
        return suffix
    else:
        raise Exception('No suffix found in {}'.format(string))


def sort_lines(array_dict):
    """
    Labels arrays as 'middle', 'upper' and 'lower' for ensemble plotting

    Parameters
    _______
    array_dict: dict of {'name': array}.

    Returns
    _______
    dict
        dictionary of {'middle': 'name', 'upper': 'name', 'lower': 'name'}
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


def plot_coords(ax, xr_obj):
    """ place lat, lon coordinates on bottom right of plot area"""
    if 'lat' in xr_obj.coords and 'lon' in xr_obj.coords:
        text = 'lat={:.2f}, lon={:.2f}'.format(float(xr_obj['lat']),
                                                 float(xr_obj['lon']))
        ax.text(0.99, 0.01, text, transform=ax.transAxes, ha = 'right', va = 'bottom')
    else:
        warnings.warn('show_coords set to True, but no coordinates found in {}.coords'.format(xr_obj))

    return ax


def split_legend(ax, out = True, axis_factor=0.15, label_gap=0.02):
    """
    Draws line labels at the end of each line, or outside the plot

    Parameters
    _______
    ax: matplotlib axis
        the axis containing the legend
    out: bool (default True)
        if True, print the labels outside of plot area. if False, prolongs plot area to fit labels
    axis_factor: float
        if out is True, percentage of the x-axis length to add at the far right of the plot
    label_gap: float
        if out is True,percentage of the x-axis length to add as a gap between line and label

    Returns
    ______
        matplotlib axis
    """

    #create extra space
    init_xbound = ax.get_xbound()

    ax_bump = (init_xbound[1] - init_xbound[0]) * axis_factor
    label_bump = (init_xbound[1] - init_xbound[0]) * label_gap

    if out is False:
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

        if out is False:
            ax.text(last_x + label_bump, last_y, label,
                    ha='left', va='center', color=color)
        else:
            trans = mpl.transforms.blended_transform_factory(ax.transAxes, ax.transData)
            ax.text(1.01, last_y, label, ha='left', va='center', color=color, transform=trans)

    return ax
