import hvplot.xarray
import holoviews as hv
from datetime import date
import cartopy.crs as ccrs
import geopandas as gpd
from spirograph.utils import convert_dict_metadata, precision, colors_style, reverse_color
import json
import warnings

# plotly a l'option de filigrane, donc utilise avec compatibilité bokeh et template (à définir)
# hv.extension('plotly', compatibility= 'bokeh')
def add_logo_date(plot):
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
    #fonction pour dataarray (UNE SEULE VARIABLE)
    if ds_attrs != None:
        full_attr = {**da.attrs, **ds_attrs}
        args = {**hv_kwargs, **convert_dict_metadata(full_attr, dict_metadata, language),
            **precision(da)}
    else:
        args = {**hv_kwargs, **convert_dict_metadata(da, dict_metadata, language),
                **precision(da)}

    if language == 'french':
        args['xlabel'] = 'Temps'
    elif language == 'english':
        args['xlabel'] = 'Time'

    pl = da.hvplot(**args)
    if logo_date == True:
        pl = add_logo_date(pl)
    return pl

def dict_ds_ts(data, language, dict_labels=None, logo_date=False):
    # fonction pour un dict ou un dataset;
    # si plusieurs variables va overlay automatiquement
    # si un dict besoin de keys_vars (key + variables du dataset) -> key peut être n'importe quoi freq, experiment, lieu,
    # data est dict ou ds
    # choisi la couleur ici
    # legend_label --> POUR OVERLAY, permet de savoir quelle info du catalogue veut donner aux plots pour les overlay
    # est aussi un dict {'ds.attrs': 'cat/domain'} ou {'ds': keys} ou {'da.attrs': 'long_name'}  ou {'ds': 'keys'}
    #                      ou {'da.coords': 'percentiles'} ou {'keys_vars': keys} ...
    # (exemple: experiment, domain, source, etc) or DataArray metadata ('long_name', 'short_name'
    # values de key_var doit etre une liste de string
    # si donne min/max ou p10/9x
    # est-ce que devrait mettre ensemble à part?

    if type(data) == dict or len(list(data.keys()))>1 and legend_labels == None:
        return print('More than one DataArray in dict or Dataset and legend_labels is not defined')
    #if type(data) == :
     #   return print('Data is dicitonary but keys_vars is not defined')

    plots_over = {}
    if type(data)==dict:
        for k, v in keys_vars:

            if sum(['_min' in v or '_max' in v for v in list(data[k].keys())]) == 2 or 'percentiles' in data[k].coords:
                #ici mettre une fonction style pour spot si mean/ max/ min p10 ou p qqc
                #plot direct en area (doit faire une autre fonction que da_ts
                #ajouter label dans dict plots - genre min_max nom data.name or ensemble percentile x1-x2

            for var in v:
                if '_min' or '_max' not in var and 'percentiles' not in data[k][var].coords:
                    if 'experiment' in list(legend_labels.values()):



def dict_subplots(list, language, logo_date, common_infos):
    #fonction qui prend une liste de subplots pour les mettre en subplots
    # est ce que prend une liste de plots ou da/ds
    # pas besoin d'être associé à un type de plots


def ds_dict_ts(dict_dataset, language, keys_vars, subplots=None, overlay=None, add_infos=None,
               logo_date=False, experiment=True, label=None, saving_path=None,
               da_ts_kwargs={'metadata': {'title': 'description', 'ylabel': 'long_name'},
                             'hv_kwargs': {'xlabel': 'time', 'grid': True}},
               layout_kwargs = None):
    """ Creates figure from dataset_dict if the vars contains mean, min and max or mean, percentile, will fill
    dict_dataset: dict
        dictionary with dataset values to be used to create the figure
    language: str
        english or french
    keys_vars: dict
        dictionary corresponding key to dict_dataset and DataArray name to be plotted
        ex: {'D': ['tasmin']} or {'rcp2.6': ['pr', 'tas']}
    subplots: None or list of string
        Indicates keys or dataarray name to be used for subplots
    overlay: None or list of string
        Indicates keys or dataarray name to be used for subplots
    labels: list of str
        labels to be included in the legend if more than DataArray by plot
    add_infos: list of string
        Additional information to be included on figure, correpond to dataset attributes (ex: lat,lon, time,)
    logo_date: bool
        If true, add ouranos logo and creation date on figure
    experiment: bool
        If true, takes the rcp/ssp colors for each experiment
    da_ts_kwargs: dict
        arguments to be passe to function da_ts
        label legend if overlay

    """
    if subplots!= None:
        subs = []
    elif overlay != None:
        over = {}
    plots = {}
    for k, vars in keys_vars.items():
        plots[k] = {}
        for v in vars:
            da = dict_dataset[k][v]

            if experiment==True:
                with open("./colors.json") as f:
                    colors = json.load(f)
                if "rcp" in dict_dataset[k].attrs["cat:experiment"]:
                    d = 'rcp'
                elif "ssp" in dict_dataset[k].attrs["cat:experiment"]:
                    d = 'ssp'
                da_ts_kwargs["hv_kwargs"]["colors"] = colors[d][dict_dataset[k].attrs["cat:experiment"]]

            if overlay != None:
                if k in overlay or v in overlay:


            plots[k][v](da_ts(da, language, **da_ts_kwargs))
    if overlay != None:
        for lab in overlay:
            if lab in plots.keys():



def time_serie(data, var, language, layout=None,
               metadata={'title': 'description', 'ylabel': 'long_name'}, saving_path=None,
               add_infos=["source", "experiment", ""], logo_date=False, mono=False):
    """
    Parameters
    -----------
    data: Dataset
    var: list
        DataArray in Dataset used for plotting
    layout: str
        if more than one string in var, two options:
            - overlay (all plotting in same graph)
            - subplots (create subplot of graph
    language: str
        french or english
    metadata: dict
        keys = figures elements (ex:title), values= metadata keys (ex: units, long_name)
    saving_path: str
        path to save the figure, default is None, need to contains the extension format desired (.jpg, .html, .tiff, .png)
    kargs_hv: dict
        args sent to hvplot, by default : {'x': 'time', 'grid': True}
    add_infos: list
        pour avoir infos supplémentaires (lat, lon, source, experiement)
    logo_date: Bool
        to have date figure creation and logo appear
    fill: bool
        if True fills shape for data same dimensions, if trace line fo each data

    Returns
    --------
    hvplot shown

    """
    #dict creation to pass
    args = {**kargs_hv, **dict_metadata(data, metadata, language),
            **precision(data), **colors_style(data, 'temporal_serie')}

    if language == 'french':
        args['xlabel'] = 'Temps'
    elif language == 'english':
        args['xlabel'] = 'Time'

    for k,  v in vars_freq.items():
        pl = data[v][k].hvplot(**args)

    if logo_date == True:
        pl = add_logo_date(pl)

    return pl

def colormap(data, projection="PlateCarree", shapefile=None, logo_data=False, reverse_cmap=False, crs_kwargs=None,
             metadata = {'title': 'description', 'ylabel': 'long_name'},
             hv_kwargs={'ocean': True, 'land': True, 'rivers': True, 'lakes': True, 'borders': True, 'coastline': True,
                        'global_extent': False, 'xlabel': 'Longitude', 'ylabel': 'Latitude'}
             ):
    """
    Parameters
    ----------
    data: DataSet
        one time step or statistics has arealdy been chosen
    projection: str
        map projection, deault is , choose from https://scitools.org.uk/cartopy/docs/v0.15/crs/projections.html
    domain: str
        geo domain reconised by X see list at https://
    shapefile: str
        file path shapefile to be displayed on graph
    logo_data: bool
        show ouranos logo + creation date (T), default false
    reverse_cmap: bool
        if True reverse color cmap, default false
    hv_kwargs: dict
        options to be passed to hvplot
        default: {ocean: True, land: True, rivers: True, lakes: True, borders: True, coastline: True]}
        'ocean', 'land',... are geoviews features to be added in the background https://geoviews.org/index.html
    crs_kwrags: dict
        options to be passed to cartopy crs

    Returns
    --------
    plot
    """
    proj = getattr(ccrs, projection)

    args = hv_kwargs
    args['projection'] = proj(**crs_kwargs)
    args['cmap'] = colors_style(data, 'colormap')

    if reverse_cmap == True:
        args['cmap'] = reverse_color(args['cmap'])

    cplot = data.hvplot(**args)
    if shapefile!=None:
        shp = gpd.read_file(shapefile)
        ax_shp = shp.plot(edgecolor='k', color=None, projection=proj, xaxis='Longitude', yaxis='Latitude')
        cplot = ax_shp * cplot

    if logo_data == True:
        cplot = add_logo_date(cplot)

    return cplot




#faire meme fonction que color map, mais pour contour (outlines) et contourf (contour) - ajouter l'option tiles
#qui va venir avec contourf pour avoir un bakcground - apres s'inspirer de contour pour faire scatter avec soit dataaray ou shapefile!




