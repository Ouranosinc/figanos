import xarray as xr
import numpy as np
import pandas as pd
import glob
from xclim import ensembles
import re

# create NetCDFs

## rcp4.5, 2015, 3 models
ens2015_rcp45 = glob.glob('/scen3/scenario/netcdf/ouranos/cb-oura-1.0/tasmax_day_*_rcp45_*_2015.nc')
tasmax_rcp45_2015_1 = ensembles.create_ensemble(ens2015_rcp45[3:6])

tasmax_rcp45_2015_1_stats = ensembles.ensemble_mean_std_max_min(tasmax_rcp45_2015_1)
tasmax_rcp45_2015_1_perc = ensembles.ensemble_percentiles(tasmax_rcp45_2015_1, values=[15, 50, 85], split=False)

tasmax_rcp45_2015_1_stats.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp45_2015_1_stats.nc')
tasmax_rcp45_2015_1_perc.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp45_2015_1_perc.nc')

## rcp4.5, 2015, 3 other models
ens2015_rcp45 = glob.glob('/scen3/scenario/netcdf/ouranos/cb-oura-1.0/tasmax_day_*_rcp45_*_2015.nc')
tasmax_rcp45_2015_2 = ensembles.create_ensemble(ens2015_rcp45[0:3])

tasmax_rcp45_2015_2_stats = ensembles.ensemble_mean_std_max_min(tasmax_rcp45_2015_2)
tasmax_rcp45_2015_2_perc = ensembles.ensemble_percentiles(tasmax_rcp45_2015_2, values=[15, 50, 85], split=False)

tasmax_rcp45_2015_2_stats.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp45_2015_2_stats.nc')
tasmax_rcp45_2015_2_perc.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp45_2015_2_perc.nc')

## rcp8.5, 2015, 3 other models
ens2015_rcp85 = glob.glob('/scen3/scenario/netcdf/ouranos/cb-oura-1.0/tasmax_day_*_rcp85_*_2015.nc')
tasmax_rcp85_2015_1 = ensembles.create_ensemble(ens2015_rcp85[3:6])

tasmax_rcp85_2015_1_stats = ensembles.ensemble_mean_std_max_min(tasmax_rcp85_2015_1)
tasmax_rcp85_2015_1_perc = ensembles.ensemble_percentiles(tasmax_rcp85_2015_1, values=[15, 50, 85], split=False)

tasmax_rcp85_2015_1_stats.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2015_1_stats.nc')
tasmax_rcp85_2015_1_perc.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2015_1_perc.nc')


## rcp8.5, 2015, 3 other models
ens2015_rcp85 = glob.glob('/scen3/scenario/netcdf/ouranos/cb-oura-1.0/tasmax_day_*_rcp85_*_2015.nc')
tasmax_rcp85_2015_2 = ensembles.create_ensemble(ens2015_rcp85[0:3])

tasmax_rcp85_2015_2_stats = ensembles.ensemble_mean_std_max_min(tasmax_rcp85_2015_2)
tasmax_rcp85_2015_2_perc = ensembles.ensemble_percentiles(tasmax_rcp85_2015_2, values=[15, 50, 85], split=False)

tasmax_rcp85_2015_2_stats.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2015_2_stats.nc')
tasmax_rcp85_2015_2_perc.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2015_2_perc.nc')

## rcp4.5, 2012, 3 models
ens2012_rcp85 = glob.glob('/scen3/scenario/netcdf/ouranos/cb-oura-1.0/tasmax_day_*_rcp85_*_2012.nc')
tasmax_rcp85_2012_1 = ensembles.create_ensemble(ens2012_rcp85[5:8])

tasmax_rcp85_2012_1_stats = ensembles.ensemble_mean_std_max_min(tasmax_rcp85_2012_1)
tasmax_rcp85_2012_1_perc = ensembles.ensemble_percentiles(tasmax_rcp85_2012_1, values=[15, 50, 85], split=False)

tasmax_rcp85_2012_1_stats.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2012_1_stats.nc')
tasmax_rcp85_2012_1_perc.to_netcdf(path='/exec/abeaupre/Projects/spirograph/test_data/tasmax_rcp85_2012_1_perc.nc')


# import and process


def output_ds(paths):

    target_lat = 45.5
    target_lon = -73.6

    datasets = {}

    for path in paths:
        if re.search("_stats", path):
            open_ds = xr.open_dataset(path, decode_timedelta=False)
            var_ds = open_ds[['tasmax_mean', 'tasmax_min', 'tasmax_max']]
        elif re.search("_perc", path):
            open_ds = xr.open_dataset(path, decode_timedelta=False)
            var_ds = open_ds.drop_dims('ts')['tasmax']
        else:
            print(path, ' not _stats or _perc')
            continue

        loc_ds = var_ds.sel(lat = target_lat, lon = target_lon, method = 'nearest').\
            convert_calendar('standard')
        datasets[path.split(sep = '/')[-1]] = loc_ds
    return datasets

paths = glob.glob('/exec/abeaupre/Projects/spirograph/test_data/tasmax*.nc')

datasets = output_ds(paths)

#   Other datasets
## ensemble percentiles (pct in variables)
url_1 = 'https://pavics.ouranos.ca//twitcher/ows/proxy/thredds/dodsC/birdhouse/disk2/cccs_portal/indices/Final/BCCAQv2_CMIP6/tx_max/YS/ssp585/ensemble_percentiles/tx_max_ann_BCCAQ2v2+ANUSPLIN300_historical+ssp585_1950-2100_30ymean_percentiles.nc'
ds_pct_open = xr.open_dataset(url_1, decode_timedelta=False)

ds_pct_1 = ds_pct_open.isel(lon=500, lat=250)[['tx_max_p50', 'tx_max_p10', 'tx_max_p90']]
da_pct_1 = ds_pct_1['tx_max_p50']

##  randomly-generated ensemble percentiles (pct in dims). No attributes
data = np.random.rand(4,3)*25 + 300
time = pd.date_range(start ='1960-01-01', end = '2020-01-01', periods = 4)
pct = [15,50,95]

da_pct_rand = xr.DataArray(data, coords = [time, pct], dims = ['time', 'percentiles'])
attr_list = ['long_name','time','standard_name','units']
for a in attr_list:
    da_pct_rand.attrs[a] = 'default
