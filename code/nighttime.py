#%%
import os
import re
import base64
import folium
import rasterio
import matplotlib
import rasterstats
import numpy as np
import pandas as pd
import geopandas as gpd
from folium import IFrame
from itertools import chain
# from module_func_rast import *
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches

#%%
# Looking for rasters
path = 'D:/Programming/NightLight/images/'
rasters = [os.path.join(path + rast) for rast in os.listdir(path)
           if rast.endswith('.tif')]

# Reading shapefile
path_shp = r'D:\Programming\NightLight\shape\EstadosBR_IBGE_LLWGS84.shp'
shapefile = gpd.read_file(path_shp)

# Looking for years


def filter_years(file):
    date = re.search(r"(\d{3}).", file).group(0)
    return date


rast_2018 = [rast for rast in rasters if '2018' == filter_years(rast)]
rast_2019 = [rast for rast in rasters if '2019' == filter_years(rast)]
rast_2020 = [rast for rast in rasters if '2020' == filter_years(rast)]

#%%
# Rewriting shapefile (changing CRS)
shp = shapefile
shp = shp.to_crs({'init': 'epsg:31982'})

# Create a new column to get BR outline
shp['BR'] = 0
shp_br_outline = shp.dissolve(by='BR')

# state list
states_name = shp['ESTADO'].to_list()

# Month list
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
          'Nov', 'Dec']

#%%
# Performing Raster Zonal Statistics


def variance(array):
    return np.nanvar(array)


def zonal_stats(rasters_list):
    statelst, brlst = [], []
    for raster in rasters_list:
        with rasterio.open(raster) as src:

            # rasterio.plot.show(tif, vmin=0, vmax=10, cmap='inferno')
            affine = src.transform

            # removing background values (<0)
            tif = src.read(1, masked=True)
            tif[tif < 0] = 0

            info_state = rasterstats.zonal_stats(shp, tif, affine=affine,
                                                 stats=['min', 'max', 'mean',
                                                        'median', 'majority',
                                                        'minority', 'std'],
                                                 add_stats={'variace': variance},
                                                 nodata=np.nan)

            info_br = rasterstats.zonal_stats(shp_br_outline, tif,
                                              affine=affine,
                                              stats=['min', 'max', 'mean',
                                                     'median', 'majority',
                                                     'minority', 'std'],
                                              add_stats={'variace': variance},
                                              nodata=np.nan)

            statelst.append(pd.DataFrame(info_state, index=states_name))
            brlst.append(info_br)

    year_df = pd.DataFrame(list(chain.from_iterable(brlst)), index=months)
    state_df = pd.concat(statelst, keys=months)

    return state_df, year_df


state2018, year2018 = zonal_stats(rast_2018)
state2019, year2019 = zonal_stats(rast_2019)
state2020, year2020 = zonal_stats(rast_2020)

# Saving into dataframes
dfs = [state2018, year2018, state2019, year2019, state2020, year2020]
dfs_names = ['state2018', 'year2018', 'state2019', 'year2019', 'state2020', 
             'year2020']

for df, name in zip(dfs, dfs_names):
    df_merge = pd.merge(df, shp, left_on='Unnamed: 1', right_on='ESTADO')
    df_merge = df_merge.drop(['object_id_', 'agreount_', 'BR'], axis=1)

    df_merge.to_csv(f'.\{name}.csv')


#%%
# Plotting years
year = '2019'

# Creating a colormap from specific colors
colors = ['#fee5d9', '#fcae91', '#fb6a4a', '#cb181d']
cmap = matplotlib.colors.LinearSegmentedColormap.from_list(name="new cmap",
                                                           colors=colors,
                                                           N=5)
# Creating a figure
fig, axes = plt.subplots(ncols=4, nrows=3, figsize=(12, 10))
axes = axes.flatten()

# Reading each raster and plotting
for raster, ax, month in zip(rast_2019, axes, months):
    with rasterio.open(raster) as src:
        tif = src.read(1)

        # Replacing negative values
        tif[np.where(tif < 0)] = 0

        # Specyfing classes to reclassify raster
        bins = [0, 0.25, 1, 10, np.round(np.nanmax(tif), 0)]

        tif_reclass = np.copy(tif)
        tif_reclass[np.where(np.isnan(tif_reclass))] = -999
        tif_reclass[np.where((tif_reclass > bins[3]))] = 4
        tif_reclass[np.where((tif_reclass > bins[2]) & (tif_reclass <= bins[3]))] = 3
        tif_reclass[np.where((tif_reclass > bins[1]) & (tif_reclass <= bins[2]))] = 2
        tif_reclass[np.where((tif_reclass > bins[0]) & (tif_reclass <= bins[1]))] = 1

        # Masking nan values
        tif_masked = np.ma.masked_where(tif_reclass == -999, tif_reclass, 
                                        copy=True)

        # Plotting
        plot = ax.imshow(tif_masked, cmap=cmap)

        # Creating patches for legend
        patches = [mpatches.Patch(color=colors[i], 
                                  label=f'{str(bins[i])} - {str(bins[i+1])}') 

                                        for i in range(len(bins)-1)]
        ax.legend(handles=patches, bbox_to_anchor=(0.8, 0.45), 
                  loc=2, frameon=False, title=f'{month}')
        ax.axis('off')

# Configuring figure
fig.tight_layout()
fig.text(0.0, 0.0, 'Extracted from VIIRS DNB dataset', ha='left', fontsize=10)
fig.suptitle(f'Nightlight {year}', fontsize=14, x=0.1, y=0.98)
fig.savefig(f'./{year}_nightlight.png', dpi=300)

#%%

# Shapefile section
df = pd.read_csv('.\state2018.csv') 

# Merging shapefile coordinates with data
df = pd.merge(df, shp, left_on='Unnamed: 1', right_on='ESTADO')
df = df.drop(['object_id_', 'agreount_', 'BR'], axis=1)

# Creating a geodataframe
gdf = gpd.GeoDataFrame(df)
gdf.crs = {'init': 'epsg:31982'}  # original coordinate system from shapefile
# Changing coordinates
gdf = gdf.to_crs('epsg:4326')  # folium only interpret EPSG 4326

# Slicing to a small part
df_acre = gdf.loc[0:11, :]
df_acre.plot()

#%%
# Plotting Stats
fig, ax = plt.subplots()
ax.plot(df_acre['std'], color='crimson', label='std')
ax.plot(df_acre['mean'], color='darkorange', label='mean')
ax.plot(df_acre['median'], color='forestgreen', label='median')
ax.set_xticklabels(months)
ax.xaxis.set_ticks(range(len(months)))
plt.legend(frameon=False, loc='upper right')
fig.savefig('./acre_stats.png', dpi=100)

#%%

#%%
# Creating an interactive map 
acre_coords = (df_acre.geometry.centroid[0].y, df_acre.geometry.centroid[0].x)
basemap = folium.Map(location=acre_coords, zoom_start=8)

# Adding Brazil and state geometry
folium.GeoJson(shp_br_outline.geometry).add_to(basemap)
folium.GeoJson(df_acre.geometry).add_to(basemap)
# how to add shapefile to folium

# Adding a figure as a marker
png = './states_stats/AC_stats.png'
encoded = base64.b64encode(open(png, 'rb').read())
html = '<img src="data:image/png;base64,{}">'.format

iframe = IFrame(html(encoded.decode('UTF-8')), width=(100*4), 
                height=(100*3.5))
popup = folium.Popup(iframe, max_width=2650)

icon = folium.Icon(color="red", icon="ok")
marker = folium.Marker(acre_coords, popup=popup, icon=icon)
marker.add_to(basemap)
basemap

basemap.save('test.html')
#%%
######################################
# Retrieving data from shapefiles
df = pd.read_csv('.\state2018.csv')

# Merging shapefile coordinates with data
df = pd.merge(df, shp, left_on='Unnamed: 1', right_on='ESTADO')
df = df.drop(['object_id_', 'agreount_', 'BR'], axis=1)

# Creating a geodataframe
gdf = gpd.GeoDataFrame(df)
gdf.crs = {'init': 'epsg:31982'}  # original coordinate system from shapefile
gdf = gdf.to_crs('epsg:4326')  # folium only interpret EPSG 4326


def states_geodataframe(geodataframe, states_list):
    ''' Create multiple state shapefiles from a geodataframe'''
    gdfs = []
    for state in states_list:
        gdf = geodataframe[geodataframe['ESTADO'] == state]
        gdfs.append(gdf)

    return gdfs


gdfs = states_geodataframe(gdf, states_name)

#%%
# Plotting basic stats graphs
for gdf, name in zip(gdfs, states_name):
    # Reseting index
    gdf = gdf.reset_index()

    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot(gdf['std'], color='rosybrown', label='std')
    ax.plot(gdf['mean'], color='firebrick', label='mean')
    ax.plot(gdf['median'], color='lightcoral', label='median')
    ax.plot(gdf['min'], color='saddlebrown', label='mean')

    ax.set_ylabel('Nighttime radiance')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_xticks(np.arange(0,12))
    ax.set_xticklabels(months)
    ax.legend(frameon=False, fontsize=10,
              bbox_to_anchor=(0.9, -0.12), ncol=4)
    plt.tight_layout()
    fig.savefig(name + '_stats.png', dpi=100)


#%%
# Creating an interactive map 
basemap = folium.Map(location=(-15, -50), zoom_start=5)
style = {'fillColor': '#00FFFFFF', 'lineColor': '#42f551'}

# Adding Brazil and state geometry
# folium.GeoJson(shp_br_outline.geometry).add_to(basemap)
for state, name in zip(gdfs, states_name):
    centroid_coords = state['geometry'].centroid
    centroid_coords_y = centroid_coords.iloc[0].y
    centroid_coords_x = centroid_coords.iloc[0].x

    # Adding Brazil and state geometry
    folium.GeoJson(state.geometry).add_to(basemap)

    # Adding a figure as a marker
    png = f'./states_stats/{name}_stats.png'
    encoded = base64.b64encode(open(png, 'rb').read())
    html = '<img src="data:image/png;base64,{}">'.format
    iframe = IFrame(html(encoded.decode('UTF-8')), width=(100*4.4), 
                    height=(70*3.5))
    popup = folium.Popup(iframe, max_width=2650)

    icon = folium.Icon(color="red", icon="ok")
    marker = folium.Marker([centroid_coords_y, centroid_coords_x],
                           popup=popup, icon=icon)
    marker.add_to(basemap)

basemap

# basemap.save('test.html')

#%%
'''
Extracted from:
https://stackoverflow.com/questions/49582831/adding-jpg-images-to-folium-popup
https://nbviewer.jupyter.org/gist/ocefpaf/20aa2e74e11db30da2ff07c45cd74816
https://stackoverflow.com/questions/59651106/add-multiple-vega-vincent-charts-to-a-folium-popup
https://stackoverflow.com/questions/58227034/png-image-not-being-displayed-on-folium-map

implement
https://stackoverflow.com/questions/57314597/folium-choropleth-map-is-there-a-way-to-add-crosshatching-for-nan-values
https://spatiality.co.ke/visualizing-geospatial-data-in-python/
'''

#%%
for row in df_acre[3:9].iterrows():
    vals = row[1]
    popup_info = f"min: {vals['min']:.2f}, max: {vals['max']:.2f}, mean: {vals['mean']:.2f}, std: {vals['std']:.2f}"
    folium.Marker(location=acre_coords,
                  clustered_marker=True,
                  popup=popup_info).add_to(basemap)

basemap
