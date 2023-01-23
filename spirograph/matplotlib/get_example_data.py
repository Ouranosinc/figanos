import xarray as xr
import numpy as np


# ensemble percentiles Xclim - dataset where each variable represents a percentile with lat, lon, time dims
url_1 = 'https://pavics.ouranos.ca//twitcher/ows/proxy/thredds/dodsC/birdhouse/disk2/cccs_portal/indices/Final/BCCAQv2_CMIP6/tx_max/YS/ssp585/ensemble_percentiles/tx_max_ann_BCCAQ2v2+ANUSPLIN300_historical+ssp585_1950-2100_30ymean_percentiles.nc'
ds_pct_open = xr.open_dataset(url_1, decode_timedelta=False)
ds_pct = ds_pct_open.isel(lon=500, lat=250)[['tx_max_p50', 'tx_max_p10', 'tx_max_p90']]
da_pct = ds_pct['tx_max_p50']


data = np.random.rand(4,3)
time = [1,2,3,4]
pct = [15,50,95]
datest = xr.DataArray(data, coords = [time, pct], dims = ['time', 'percentiles'])

# DataArray simple, tasmax across time at a given point in space
url_2 = 'https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/datasets/simulations/bias_adjusted/cmip6/pcic/CanDCS-U6/day_BCCAQv2+ANUSPLIN300_UKESM1-0-LL_historical+ssp585_r1i1p1f2_gn_1950-2100.ncml'
ds_var_open = xr.open_dataset(url_2, decode_timedelta= False)
ds_var = ds_var_open.isel(lon = 500, lat = 250)





