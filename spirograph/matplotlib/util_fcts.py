
import pandas as pd
import xarray as xr


def empty_dict(kwargs):
    """Returns empty dictionaries
    """
    for k, v in kwargs.items():
        if not v:
            kwargs[k] = {}
    return kwargs

def get_attributes(xr_obj, str):
    """
    Fetches attributes corresponding to keys from Xarray objects
    Args:
        xr_obj: Xarray DataArray or Dataset
        str: string corresponding to an attribute key
    Returns:
         Xarray attribute value as string
    """
    if str in xr_obj.attrs:
            return xr_obj.attrs[str]
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
    """
    if 'title' in attr_dict:
        ax.set_title(get_attributes(xr_obj, attr_dict['title']), wrap=True)
    if 'xlabel' in attr_dict:
        ax.set_xlabel(get_attributes(xr_obj, attr_dict['xlabel'])) #rotation?
    if 'ylabel' in attr_dict:
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
        ref_values[name] = int(arr[int(len(arr)/2)])
    sorted_series = pd.Series(ref_values).sort_values()
    sorted_lines['lower'] = sorted_series.idxmin()
    sorted_lines['upper'] = sorted_series.idxmax()
    sorted_lines['middle'] = sorted_series.index[int(len(sorted_series)/2 - 0.5)] # -0.5 is + 0.5 - 1, to account for 0-indexing

    return sorted_lines










# lnx = np.arange(1,10,1)
# ln1 = lnx + 3 + 1*np.random.rand()
# ln2 = lnx + 10 + 3*np.random.rand()
# ln3 = lnx + 6 + 2*np.random.rand()
#
# fig, ax = plt.subplots(figsize = (4,3))
# ax.plot(lnx, ln1)
# ax.plot(lnx, ln2)
# ax.plot(lnx, ln3)
#
# ax.fill_between(lnx, ln1,ln2, alpha = 0.2, color = 'red')
# ax.fill_between(lnx, ln1,ln3, alpha = 0.2, color = 'blue')
# plt.show()




