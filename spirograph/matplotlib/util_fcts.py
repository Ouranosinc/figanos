
import pandas as pd
import re

def empty_dict(param):
    if param is None:
        param = {}
    return param


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

    if str(type(array)) == "<class 'xarray.core.dataset.Dataset'>":
        if pd.notnull([re.search("_p[0-9]{1,2}", var) for var in array.data_vars]).sum() >=2:
            cat = "PCT_VAR_ENS"
        elif pd.notnull([re.search("[Mm]ax|[Mm]in", var) for var in array.data_vars]).sum() >= 2:
            cat = "STATS_VAR_ENS"
        elif pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
            cat = "PCT_DIM_ENS_DS"  ## no support for now
        else:
            cat = "NON_ENS_DS"

    elif str(type(array)) == "<class 'xarray.core.dataarray.DataArray'>":
        if pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
           cat = "PCT_DIM_ENS_DA"
        else:
            cat = "DA"
    else:
        raise TypeError('Array is not an Xarray Dataset or DataArray')
    print('cat: ', cat)
    return cat


def get_attributes(xr_obj, strg):
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
    elif str(type(xr_obj)) == "<class 'xarray.core.dataset.Dataset'>":
        if strg in xr_obj[list(xr_obj.data_vars)[0]].attrs:  # DataArray of first variable
            return xr_obj[list(xr_obj.data_vars)[0]].attrs[strg]
    elif strg in xr_obj.dims:
        return strg  # special case for 'time' because DataArray and Dataset dims are not the same types
    else:
        print('Attribute "{0}" not found in attributes'.format(strg))
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
    Todo: include lat,lon coordinates in title, add warning if input not in list (e.g. y_label)
    """
    if 'title' in attr_dict:
        ax.set_title(get_attributes(xr_obj, attr_dict['title']), wrap=True)
    if 'xlabel' in attr_dict:
        ax.set_xlabel(get_attributes(xr_obj, attr_dict['xlabel']))  # rotation?
    if 'ylabel' in attr_dict:
        if 'units' in attr_dict and len(attr_dict['units']) >= 1: # second condition avoids '[]' as label
            ax.set_ylabel(get_attributes(xr_obj, attr_dict['ylabel']) + ' [' +
                      get_attributes(xr_obj, attr_dict['yunits']) + ']')
        else:
            ax.set_ylabel(get_attributes(xr_obj, attr_dict['ylabel']))
    return ax


def sort_lines(array_dict):
    """
    Sorts and labels same-length arrays that plot as parallel lines in x,y space
    according to the highest and lowest along the y-axis
    Args:
        array_dict: dict of arrays.
    Returns:
        dict
    """
    ref_values = {}
    sorted_lines = {}
    for name, arr in array_dict.items():
        ref_values[name] = float(arr[int(len(arr)/2)]) # why the first int??
    sorted_series = pd.Series(ref_values).sort_values()
    sorted_lines['lower'] = sorted_series.idxmin()
    sorted_lines['upper'] = sorted_series.idxmax()
    sorted_lines['middle'] = sorted_series.index[int(len(sorted_series)/2 - 0.5)] # -0.5 is + 0.5 - 1, to account for 0-indexing

    return sorted_lines








