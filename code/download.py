#%%
import ee
import ee.mapclient
import geetools

ee.Authenticate()
ee.Initialize()

start = '2018-12-01'
end = '2018-12-31'

'''
Pelo o que eu entendi ate agora pra trabalhar com shapefiles eu preciso
fazer o upload deles no proprio google earth engine e adiciona-los aqui
como FeatureCollection (levei 2h pra entender isso)
'''

# Geometries
geometries = ee.FeatureCollection("users/laizacalbuquerque/UF_Brasil_4326")

# Image collection
collection = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG")
                .filterDate(start, end)
                .filterBounds(geometries)
                .select(["avg_rad"]))

collectionList = collection.toList(100)
print('Number of images', len(collectionList.getInfo()))

tasks = geetools.batch.Export.imagecollection.toDrive(
                collection, 'VIIRS_Nightlight', region=geometries,
                scale=500, crs='EPSG:31982')


#%%
#https://github.com/renelikestacos/Google-Earth-Engine-Python-Examples/blob/master/001_EE_Classification_Landsat_8_TOA.ipynb
#https://colab.research.google.com/github/google/earthengine-api/blob/master/python/examples/ipynb/ee-api-colab-setup.ipynb
