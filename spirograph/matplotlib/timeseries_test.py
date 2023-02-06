
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use("Qt5Agg")
#mpl.style.use('dark_background')  #  mpl.style.available



# test

## 1 . Basic plot functionality

## simple DataArray, unlabeled
timeseries(da_pct_1, line_kw={'color': 'red'})

## simple DataArray, labeled
timeseries({'My data': da_pct_1}, line_kw={'My data': {'color': 'red'}})

## idem, with no attributes
timeseries({'Random data': da_pct_rand})

## simple Dataset ensemble (variables)
timeseries({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_stats']}, legend = 'full', show_coords = True)

timeseries({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_stats']},
        line_kw={'rcp45_2015_1': {'color': 'purple'}})

## simple Dataset ensemble (dims), title override
my_ax = timeseries({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_perc']},
        line_kw={'rcp45_2015_1': {'color': '#daa520'}}, legend = 'full')
my_ax.set_title('The percentiles are in dimensions')

## one DataArray, one pct Dataset, one stats Dataset
timeseries({'DataArray': datasets['tasmax_rcp45_2015_1_stats']['tasmax_mean'],
            'Dataset_vars': datasets['tasmax_rcp45_2015_2_stats'],
            'Dataset_dims': datasets['tasmax_rcp85_2015_1_perc']},
           line_kw={'DataArray': {'color': '#8a2be2'},
                 'Dataset_vars': {'color': '#ffa500'},
                 'Dataset_dims': {'color': '#468499'}
                     }, legend='edge')

# test with non-ensemble DS
timeseries(rand_ds)

#test different length arrays
timeseries({'random': rand_ds,'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_perc']})

#
