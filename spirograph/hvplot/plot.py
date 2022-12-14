import hvplot.xarray
import hvplot.pandas
import holoviews as hv
from datetime import date
import cartopy.crs as ccrs
import geopandas as gpd
from spirograph.hvplot.utils import convert_dict_metadata, precision, colors_style, reverse_color, perc_min_max, ts_ens_title, ts_ens_label, wrap_metdata
import json
import pandas as pd
import warnings

from bokeh.plotting import figure, output_notebook, reset_output, show
from bokeh.models import ColumnDataSource, Arrow, OpenHead, NormalHead, TeeHead, BoxAnnotation, Label

# plotly a l'option de filigrane, donc utilise avec compatibilité bokeh et template (à définir)
# hv.extension('plotly', compatibility= 'bokeh')
def add_logo_date(plot): #ToDo: doesnt work when saves directly from hvplot html
    jour = str(date.today())
    html_text = """
                    <figure>
                    <center>
                    <img src=https://conseilinnovation.quebec/wp-content/uploads/2022/05/logo-ouranos.png height='19' width='50'></center>
                    <center><figcaption style="font-size:0.8em; width: 60px">Spirograph - DATE </figcaption></center>
                  """
    logo = hv.Div(html_text.replace('DATE', jour))
    return hv.Layout(plot + logo.opts(width=60, height=50)).cols(1)



def da_ts(da, language, dict_metadata, hv_kwargs, ds_attrs=None, logo_date=False):
    """
    da: DataArray
    language: str
        english or french
    dic_metadata: dict
        plot elements associated to Xarray attributes (da.attrs if ds_attrs=None)
    hv_kwargs: dict
        hvplot options
    ds_attrs: dict
        options if DataArray attributes doesn't have all information required -> can be a merge of attributes
        ds_attrs = {**da.attrs, **ds.attrs}
    """
    #fonction pour dataarray (UNE SEULE VARIABLE)
    args = wrap_metdata(da, language, dict_metadata, hv_kwargs, ds_attrs)
    if language == 'french':
        args['xlabel'] = 'Temps'
    elif language == 'english':
        args['xlabel'] = 'Time'

    pl = da.hvplot(**args)
    if logo_date == True:
        pl = add_logo_date(pl)
    return pl

def scatter(data, language, dict_metadata, hv_kwargs, ds_attrs=None, logo_date=False):
    """
    da: DataArray
    language: str
        english or french
    dic_metadata: dict
        plot elements associated to Xarray attributes (da.attrs if ds_attrs=None)
    hv_kwargs: dict
        hvplot options - MUST HAVE x AND y IN KEYS
        exemples: {'x': 'time', 'y': 'tasmax'}
                  {'x': 'lon', 'y': 'lat'}
    ds_attrs: dict
        options if DataArray attributes doesn't have all information required -> can be a merge of attributes
        ds_attrs = {**da.attrs, **ds.attrs}
    """
    df = data.to_dataframe().reset_index()

    if 'x' not in hv_kwargs.keys() or 'y' not in hv_kwargs.keys():
        warnings.error("Missing 'x' or 'y' definition in hv_kwargs")

    args = wrap_metdata(data, language, dict_metadata, hv_kwargs, ds_attrs)

    pl = df.hvplot.scatter(**args)
    if logo_date == True:
        pl = add_logo_date(pl)
    return pl
