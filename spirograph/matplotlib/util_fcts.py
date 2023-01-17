
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






