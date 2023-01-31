
import pandas as pd
import re
import warnings
import xarray as xr

def empty_dict(param):
    if param is None:
        param = {}
    return param

def check_timeindex(xr_dict):
    """ checks if the time index of Xarray objects in a dict is CFtime
    and converts to pd.DatetimeIndex if true"""
    for name, xr_obj in xr_dict.items():
        if 'time' in xr_obj.dims:
            if isinstance(xr_obj.get_index('time'), xr.CFTimeIndex):
                conv_obj = xr_obj.convert_calendar('standard', use_cftime=None)
                xr_dict[name] = conv_obj
        else:
            raise ValueError('"time" dimension not found in {}'.format(xr_obj))
    return xr_dict

def get_array_categ(array):
    """Returns an array category
        PCT_VAR_ENS: ensemble of percentiles stored as variables
        PCT_DIM_ENS_DA: ensemble of percentiles stored as dimension coordinates, DataArray
        STATS_VAR_ENS: ensemble of statistics (min, mean, max) stored as variables
        NON_ENS_DS: dataset of individual lines, not an ensemble
        DA: DataArray
    Args:
        data_dict:  Xarray Dataset or DataArray
    Returns
        str
        """
    if isinstance(array, xr.Dataset):
        if pd.notnull([re.search("_p[0-9]{1,2}", var) for var in array.data_vars]).sum() >=2:
            cat = "PCT_VAR_ENS"
        elif pd.notnull([re.search("[Mm]ax|[Mm]in", var) for var in array.data_vars]).sum() >= 2:
            cat = "STATS_VAR_ENS"
        elif pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
            cat = "PCT_DIM_ENS_DS"  ## no support for now
        else:
            cat = "NON_ENS_DS"

    elif isinstance(array, xr.DataArray):
        if pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
           cat = "PCT_DIM_ENS_DA"
        else:
            cat = "DA"
    else:
        raise TypeError('Array is not an Xarray Dataset or DataArray')

    return cat


def get_attributes(strg, xr_obj):
    """
    Fetches attributes or dims corresponding to keys from Xarray objects. Looks in
    Dataset attributes first, and then looks in DataArray.
    Args:
        xr_obj: Xarray DataArray or Dataset
        str: string corresponding to an attribute key
    Returns:
         Xarray attribute value as string
    """
    if strg in xr_obj.attrs:
        return xr_obj.attrs[strg]

    elif strg in xr_obj.dims:
        return strg  # special case for 'time' because DataArray and Dataset dims are not the same types

    elif isinstance(array, xr.Dataset):
        if strg in xr_obj[list(xr_obj.data_vars)[0]].attrs:  # DataArray of first variable
            return xr_obj[list(xr_obj.data_vars)[0]].attrs[strg]

    else:
        warnings.warn('Attribute "{0}" not found in attributes'.format(strg))
        return ''



def set_plot_attrs(attr_dict, xr_obj, ax):
    """
    Sets plot elements according to Dataset or DataArray attributes.  Uses get_attributes()
    to check for and return the string.
    Args:
        use_attrs (dict): dict containing specified attribute keys
        xr_obj: Xarray DataArray.
        ax: matplotlib axis
    Returns:
        matplotlib axis

    """
    #  check
    for key in attr_dict:
        if key not in ['title','xlabel', 'ylabel', 'yunits']:
            warnings.warn('Use_attrs element "{}" not supported'.format(key))

    if 'title' in attr_dict:
        if 'lat' in xr_obj.coords and 'lon' in xr_obj.coords:
            ax.set_title(get_attributes(attr_dict['title'], xr_obj) +
                         ' (lat={:.2f}, lon={:.2f})'.format(float(xr_obj['lat']),
                                                              float(xr_obj['lon'])),
                         wrap=True)
        else:
            ax.set_title(get_attributes(attr_dict['title'], xr_obj), wrap=True)

    if 'xlabel' in attr_dict:
        ax.set_xlabel(get_attributes(attr_dict['xlabel'], xr_obj))

    if 'ylabel' in attr_dict:
        if 'units' in attr_dict and len(attr_dict['units']) >= 1: # second condition avoids '[]' as label
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj) + ' [' +
                      get_attributes(attr_dict['yunits'], xr_obj) + ']')
        else:
            ax.set_ylabel(get_attributes(attr_dict['ylabel'], xr_obj))
    return ax


def sort_lines(array_dict):
    """
    Labels arrays as 'middle', 'upper' and 'lower' for ensemble plotting
    Args:
        array_dict: dict of arrays.
    Returns:
        dict
    """
    if len(array_dict) != 3:
        raise ValueError('Ensembles must contain exactly three arrays')

    sorted_lines = {}

    for name in array_dict.keys():
        if re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", name):
            suffix = re.search("[0-9]{1,2}$|[Mm]ax$|[Mm]in$|[Mm]ean$", name).group()

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








