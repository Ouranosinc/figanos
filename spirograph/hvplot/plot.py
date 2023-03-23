import warnings
from datetime import date
from typing import Any, Dict

import holoviews as hv
import xarray as xr

from spirograph.hvplot.utils import wrap_metdata


# plotly a l'option de filigrane, donc utilise avec compatibilité bokeh et template (à définir)
# hv.extension('plotly', compatibility= 'bokeh')
def add_logo_date(plot):  # ToDo: doesnt work when saves directly from hvplot html
    jour = str(date.today())
    html_text = """
                    <figure>
                    <center>
                    <img src=https://conseilinnovation.quebec/wp-content/uploads/2022/05/logo-ouranos.png height='19' width='50'></center>
                    <center><figcaption style="font-size:0.8em; width: 60px">Spirograph - DATE </figcaption></center>
                  """
    logo = hv.Div(html_text.replace("DATE", jour))
    return hv.Layout(plot + logo.opts(width=60, height=50)).cols(1)


def da_ts(
    da: xr.DataArray,
    language: str,
    dict_metadata: Dict[str, Any],
    hv_kwargs: Dict[str, Any],
    ds_attrs: Dict[str, Any] = None,
    logo_date: bool = False,
):
    """Insert title here.


    Parameters
    ----------
    da : DataArray
        xarray DataArray object.
    language : str
        English or French
    dict_metadata : dict
        plot elements associated to Xarray attributes (da.attrs if ds_attrs=None)
    hv_kwargs : dict
        hvplot options
    ds_attrs : dict
        options if DataArray attributes doesn't have all information required -> can be a merge of attributes
        ds_attrs = {da.attrs, ds.attrs}
    logo_date : bool
        Add a date to the logo. Default: False.
    """
    # fonction pour dataarray (UNE SEULE VARIABLE)
    args = wrap_metdata(da, language, dict_metadata, hv_kwargs, ds_attrs)
    if language == "french":
        args["xlabel"] = "Temps"
    elif language == "english":
        args["xlabel"] = "Time"

    pl = da.hvplot(**args)
    if logo_date:
        pl = add_logo_date(pl)
    return pl


def scatter(
    data: xr.DataArray,
    language: str,
    dict_metadata: Dict[str, Any],
    hv_kwargs: Dict[str, Any],
    ds_attrs: Dict[str, Any] = None,
    logo_date: bool = False,
):
    """Make a scatter plot.

    Parameters
    ----------
    data : DataArray
        xarray DataArray object.
    language : {"english", "french"}
        Language of metadata.
    dict_metadata : dict
        plot elements associated to Xarray attributes (da.attrs if ds_attrs=None)
    hv_kwargs : dict
        hvplot options - MUST HAVE x AND y IN KEYS
        exemples: {'x': 'time', 'y': 'tasmax'} or {'x': 'lon', 'y': 'lat'}
    ds_attrs : dict
        options if DataArray attributes doesn't have all information required -> can be a merge of attributes
        ds_attrs = {da.attrs, s.attrs}
    logo_date : bool
        Add a date to the logo. Default: False.
    """
    df = data.to_dataframe().reset_index()

    if "x" not in hv_kwargs.keys() or "y" not in hv_kwargs.keys():
        # FIXME: Is this a warning or an error?
        warnings.error("Missing 'x' or 'y' definition in hv_kwargs")

    args = wrap_metdata(data, language, dict_metadata, hv_kwargs, ds_attrs)

    pl = df.hvplot.scatter(**args)
    if logo_date:
        pl = add_logo_date(pl)
    return pl
