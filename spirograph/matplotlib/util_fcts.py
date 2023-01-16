
def empty_dict(kwargs):
    """Returns empty dictionaries
    """
    for k, v in kwargs.items():
        if not v:
            kwargs[k] = {}
    return kwargs

def get_metadata(xr_obj, str):
    """
    Fetches attributes corresponding to their key from Xarray objects

    Args:
        xr: Xarray DataArray or Dataset
        str: string corresponding to an attribute key

    Returns:
         Xarray attribute value as string
    """
    if str in xr_obj.attrs:
        return xr_obj.attrs[str]
    else:
        raise Exception('Metadata "{0}" not found in "{1}"'.format(str, xr_obj.name))
    #if str in xr.coords: pas sur si peut vraiment faire de quoi si dans coords .... plutôt loop a l'extérieur

def ax_dict_metadata(ax, use_attrs, xr_obj):
    if 'title' in use_attrs:
        ax.set_title(get_metadata(xr_obj, use_attrs['title']), wrap=True)
    if 'xlabel' in use_attrs:
        ax.set_xlabel(get_metadata(xr_obj, use_attrs['xlabel'])) #rotation?
    if 'ylabel' in use_attrs:
        ax.set_ylabel(get_metadata(xr_obj, use_attrs['ylabel']))
    return ax

#transform ds into df
def xr_pd(xr):
    if "Dataset" in str(type(xr)):
        return xr.to_dataframe().reset_index()
    else:
        return xr.to_dataframe(name='values').reset_index()


def da_time_serie_line(da, ax=None, dict_metadata=None, sub_kw=None, line_kw=None, logo=False):
    """
    plot unique time serie from dataset
    da: dataset xarray
    ax: matplotlib axis
    dict_metadata: join figure element to xarray dataset element
    sub_kw: matplotlib subplot kwargs
    line_kw : maplotlib line kwargs
    """
    kwargs = empty_dic({'sub_kw': sub_kw, 'line_kw': line_kw})
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])
    da.plot.line(ax=ax, **kwargs['line_kw'])
    if dict_metadata:
        ax_dict_metadata(ax, dict_metadata, da, 'lines')
    if 'label' in dict_metadata:
        ax.legend()
    return ax



def ens_time_serie(dict_xr, ax=None, dict_metadata=None, sub_kw=None, line_kwargs=None):
    """
    dict of xr object: only one no legend, more than one legend
    if dictionnary, the keys will be used to name the ensembles

    if to be created over coord (ex: horizon.... fait quoi?)

    """
    kwargs = empty_dic({'sub_kw': sub_kw, 'line_kwargs': line_kwargs})
    if not ax:
        fig, ax = plt.subplots(**kwargs['sub_kw'])

    if type(dict_xr) != dict:
        dict_xr = {'one': dict_xr}

    if len(dict_xr) == 1:
        df = xr_pd(list(dict_xr.values())[0]).drop(columns=['lat', 'lon'])
        if "Dataset" in str(type(list(dict_xr.values())[0])):
            df = pd.melt(df, ['time'])
        sns.lineplot(data=df, x='time', y='value', ax=ax,  **kwargs['line_kwargs'])
    else:
        n = 0
        for k, v in dict_xr.items():
            df = xr_pd(v).drop(columns=['lat', 'lon'])
            if "Dataset" in str(type(v)):
                df = pd.melt(df, ['time'], value_name=k)
            else:
                df = df.rename(columns={'values': k})
            if n == 0:
                dfa = df
            else:
                dfa[k] = df[k]
            n = n+1
        dfa = pd.melt(dfa, ['time'], list(dict_xr.keys()))
        sns.lineplot(data=dfa, x='time', y='value', hue='variable', ax=ax, **kwargs['line_kwargs'])  #ajouter palette horizon si possible - option rcp/ssp ou détecter automatique?
    if dict_metadata:
        ax_dict_metadata(ax, dict_metadata, list(dict_xr.values())[0], 'line')
    return ax
##### Fin code Sarah-Claude #####
