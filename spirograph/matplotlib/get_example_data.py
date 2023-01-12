import xarray as xr





# ensemble percentiles Xclim - dataset where each variable represents a percentile, with lat, lon, time coords
url_1 = 'https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/disk2/cccs_portal/indices/Final/BCCAQv2_CMIP6/txgt_32/YS/ssp585/ensemble_percentiles/txgt_32_ann_BCCAQ2v2+ANUSPLIN300_historical+ssp585_1950-2100_percentiles.nc'

ds_pct = xr.open_dataset(url_1, decode_cf= False)


da_pct = ds_pct.sel()

