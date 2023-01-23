

import pandas as pd
import re


def get_array_categ(array):
    """Returns an array category
        PCT_VAR_ENS: ensemble of percentiles stored as variables
        PCT_DIM_ENS: ensemble of percentiles stored as dimension coordinates
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
        elif pd.notnull([re.search("percentiles", dim) for dim in array.dims]).sum() == 1:
            cat = "PCT_DIM_ENS"
        elif pd.notnull([re.search("[Mm]ax|[Mm]in", var) for var in array.data_vars]).sum() >= 2:
            cat = "STATS_VAR_ENS"
        else:
            cat = "NON_ENS_DS"

    elif str(type(array)) == "<class 'xarray.core.dataarray.DataArray'>":
        cat = "DA"
    else:
        raise TypeError('Array is not an Xarray Dataset or DataArray')
    return cat


def get_attributes(xr_obj, str):
    """
    Fetches attributes or dims corresponding to keys from Xarray objects
    Args:
        xr_obj: Xarray DataArray or Dataset
        str: string corresponding to an attribute key
    Returns:
         Xarray attribute value as string
    """
    if str in xr_obj.attrs:
        return xr_obj.attrs[str]
    elif str in xr_obj.dims:
        return str #special case because DataArray and Dataset dims are not the same types
    else:
        raise Exception('Attribute "{0}" not found in "{1}"'.format(str, xr_obj.name))



def set_plot_attrs(attr_dict, xr_obj, ax):
    """
    Sets plot elements according to DataArray attributes. Uses get_attributes()
    Args:
        use_attrs (dict): dict containing specified attribute keys
        xr_obj: Xarray DataArray
        ax: matplotlib axis
    Returns:
        matplotlib axis
    Todo: include lat,lon coordinates in title, add warning if input not in list (e.g. y_label)
    """
    if 'title' in attr_dict:
        ax.set_title(get_attributes(xr_obj, attr_dict['title']), wrap=True)
    if 'xlabel' in attr_dict:
        ax.set_xlabel(get_attributes(xr_obj, attr_dict['xlabel'])) #rotation?
    if 'ylabel' in attr_dict:
        ax.set_ylabel(get_attributes(xr_obj, attr_dict['ylabel'])+ ' [' +
                      get_attributes(xr_obj, attr_dict['yunits'])+ ']')
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
        ref_values[name] = int(arr[int(len(arr)/2)])
    sorted_series = pd.Series(ref_values).sort_values()
    sorted_lines['lower'] = sorted_series.idxmin()
    sorted_lines['upper'] = sorted_series.idxmax()
    sorted_lines['middle'] = sorted_series.index[int(len(sorted_series)/2 - 0.5)] # -0.5 is + 0.5 - 1, to account for 0-indexing

    return sorted_lines










# lnx = np.arange(1,10,1)
# ln1 = lnx + 3 + 1*np.random.rand()
# ln2 = lnx + 10 + 3*np.random.rand()
# #ln3 = lnx + 6 + 2*np.random.rand()
#
# fig, ax = plt.subplots(figsize = (4,3))
# line_1 = ax.plot(lnx, ln1)
# line_2 = ax.plot(lnx, ln2)
# #line_3 = ax.plot(lnx, ln3)
#
# ax.fill_between(lnx, ln1,ln2, alpha = 0.2, color = 'red')
# #ax.fill_between(lnx, ln1,ln3, alpha = 0.2, color = 'blue')
# plt.show()



