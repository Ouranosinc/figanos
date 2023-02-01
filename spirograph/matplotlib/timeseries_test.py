
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use("Qt5Agg")



# test

## 1 . Basic plot functionality

## simple DataArray, unlabeled
line_ts(da_pct_1, line_kw={'color': 'red'})

## simple DataArray, labeled
line_ts({'My data': da_pct_1}, line_kw={'My data': {'color': 'red'}})

## idem, with no attributes
line_ts({'Random data': da_pct_rand})

## simple Dataset ensemble (variables)
line_ts({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_stats']}, legend = 'full', show_coords = True)

line_ts({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_stats']},
        line_kw={'rcp45_2015_1': {'color': 'purple'}})

## simple Dataset ensemble (dims), title override
my_ax = line_ts({'rcp45_2015_1': datasets['tasmax_rcp45_2015_1_perc']},
        line_kw={'rcp45_2015_1': {'color': '#daa520'}}, legend = 'full')
my_ax.set_title('The percentiles are in dimensions')

## one DataArray, one pct Dataset, one stats Dataset
line_ts({'DataArray': datasets['tasmax_rcp45_2015_1_stats']['tasmax_mean'],
         'Dataset_vars': datasets['tasmax_rcp45_2015_2_stats'],
         'Dataset_dims': datasets['tasmax_rcp85_2015_1_perc']},
        line_kw={'DataArray': {'color': '#000080'},
                 'Dataset_vars': {'color': '#ffa500'},
                 'Dataset_dims': {'color': '#468499'}
                 }, legend = 'full')

# test with non-ensemble DS
# test with pct_dim_ens_ds


