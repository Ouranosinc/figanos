
import matplotlib as mpl
mpl.use("Qt5Agg")



# test

## simple DataArray, labeled or unlabeled
line_ts(da_pct_1, line_kw={'color': 'red'})
line_ts({'My data': da_pct_1}, line_kw={'My data':{'color': 'red'}})

## simple Dataset ensemble (variables)
line_ts(ds_stats_2015)
line_ts({'2015 daily rcp4.5 stats': ds_stats_2015}, line_kw = {'2015 daily rcp4.5 stats':{'color':'purple'}})

## simple Dataset ensemble (dims)
line_ts({'2012 daily rcp4.5 percentiles': ds_perc_2012})

## all together
line_ts({'DataArray': da_pct, 'Var Ensemble': ds_pct, 'other': datest},
        line_kw={'DataArray': {'color': 'blue'}, 'Var Ensemble': {'color': 'red'}})
