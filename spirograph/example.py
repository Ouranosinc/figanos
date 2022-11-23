
import hvplot.xarray  # noqa
import holoviews as hv
import matplotlib.pyplot as plt
from bokeh.models import NumeralTickFormatter, Title
from bokeh.models import ColumnDataSource, Label, LabelSet, Range1d
import bokeh
import glob
import numpy as np
from spirograph.plot import da_ts
import xarray as xr
ds = xr.open_dataset('/home/sarah/spir/dlyfrzthw_tx0_tn-1_ann_BCCAQ2v2+ANUSPLIN300_historical+ssp585_1950-2100_percentiles.nc', decode_timedelta= False)
pt = ds['dlyfrzthw_tx0_tn-1_p10'].isel(lat=150, lon=250)
pl = pt.hvplot()
hvplot.show(pl)
da_ts_kwargs = {'metadata': {'title': 'description', 'ylabel': 'long_name'},
                             'hv_kwargs': {'xlabel': 'time', 'grid': True}}
pl = da_ts(pt, "english", da_ts_kwargs['metadata'], da_ts_kwargs['hv_kwargs'], ds_attrs=None, logo_date=True)

def bokeh_title_hook(plot, element):
    plot.add_layout(Title(text='mon nom est', align='center', ), 'above')
    plot.add_layout(Title(text="Created on: 2022-08-24", align='left', level='annotation'), 'below')

    #plot.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")

#pl1 = da_ts.hvplot().opts(hooks=[bokeh_title_hook])
#hvplot.show(pl1)

    #hvplot
    inter = hvplot.render(pl1, backend='plotly')
    ppl1 = Figure(inter)
    ppl1.update_layout(yaxis={'tickformat': ".3f"})

    #bokeh
    bpl1 = hvplot.render(pl1, backend='bokeh')


source = list(v.split('_')[0].split('/')[-1] for v in glob.glob("/scen3/scenario/netcdf/ouranos/portraits-clim-1.1/*rcp45_dlyfrzthw_annual.nc"))
ens_rcp45 = ensembles.create_ensemble(glob.glob("/scen3/scenario/netcdf/ouranos/portraits-clim-1.1/*rcp45_dlyfrzthw_annual.nc"))
ens_rcp45 = ens_rcp45.rename({'realization': 'source'})
ens_rcp45['source'] = np.array(source)
ens_rcp45['experiement'] = np.array(['rcp45'])
ens_rcp45 = ens_rcp45.sel(lat=45.5, lon=-75.5, method='nearest')

ens_rcp85 = ensembles.create_ensemble(glob.glob("/scen3/scenario/netcdf/ouranos/portraits-clim-1.1/*rcp85_dlyfrzthw_annual.nc"))
ens_rcp85 = ens_rcp85.rename({'realization': 'source'})
ens_rcp85['source'] = np.array(source)
ens_rcp85['experiement'] = np.array(['rcp85'])
ens_rcp85 = ens_rcp85.sel(lat=45.5, lon=-75.5, method='nearest')

ens_obs = ensembles.create_ensemble(glob.glob("/scen3/scenario/netcdf/ouranos/portraits-clim-1.1/*obs_dlyfrzthw_annual.nc"))
ens_obs = ens_obs.rename({'realization': 'source'})
ens_obs['source'] = np.array(['Nrcan_obs'])
ens_obs['experiement'] = np.array(['obs'])
ens_obs = ens_obs.sel(lat=45.5, lon=-75.5, method='nearest')

ens = xr.combine_by_coords([ens_obs, ens_rcp45, ens_rcp85])

ds = xr.open_dataset('/scen3/scenario/netcdf/ouranos/portraits-clim-1.1/NRCAN_obs_dlyfrzthw_annual.nc', decode_timedelta=False)
da = ds['dlyfrzthw']
da_ts = da.isel(lat=250, lon=500)
