import ee
import ee.mapclient
import geetools

# To use GEE plataform you need to create an accont and
# Authenticate, which means, login on GEE
ee.Authenticate()
ee.Initialize()

# To download our time-series image collection choose a
# period to look in dataset
start = '2018-12-01'
end = '2018-12-31'

# Geometries
# To avoid downloading images for all area you should provide a desired
# boundary; Here I uploaded to GEE one shapefile
# Tutorial for it: https://thegeoict.com/blog/2019/08/05/uploading-a-shapefile-to-google-earth-engine/
geometries = ee.FeatureCollection("users/your_username/your_shapefile_name")

# Image collection
# In ImageCollection paste the GEE path for desired satellite images
# You can discover images satellite collections in GEE plataform
collection = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG")
                .filterDate(start, end)
                .filterBounds(geometries)
                .select(["avg_rad"]))

collectionList = collection.toList(100)
print('Number of images', len(collectionList.getInfo()))

# This step will export all images to your Google Drive

tasks = geetools.batch.Export.imagecollection.toDrive(
                collection=collection,
                folder='VIIRS_Nightlight',
                region=geometries,
                scale=500,
                crs='EPSG:31982')
