# NDVeye Plugin

## I. Algorithm details

## II. Example workflows

### II.1 Corn counting

### II.2 Reef mapping

#### Motivation

We can use NDVeye to improve OpenStreetMap, [an open spatial database](https://www.openstreetmap.org/about), *"built by a community of mappers that contribute and maintain data about roads, trails, cafés, railway stations, and much more, all over the world"*.

There are some yet unmapped reefs within lagoons of the [Tuamotus islands](https://en.wikipedia.org/wiki/Tuamotus):
![image](https://i.imgur.com/yu6lU5k.png)
![image](https://i.imgur.com/IFjXCix_d.webp?maxwidth=1520&fidelity=grand)

We can polygonize these reefs using NDVeye.

#### Get data

Let's use Sentinel-2 imagery as raster input. [EO Browser](https://apps.sentinel-hub.com/eo-browser) can help us acquire suitable imagery. There, we can search for *Toau atoll*, edit cloud coverage settings, copy the s3 path of the image & visualize it straight away:
![gif](https://github.com/zabop/ndveye/blob/master/docs/sentinel2download.gif?raw=true)

You can inspect the different bands in EO, and list available files using AWS s3 CLI:

```
aws s3 ls --request-payer requester sentinel-s2-l2a/tiles/6/L/XH/2024/3/26/0/ --recursive
```

I chose to work with the B04 band. Download imagery:

```
aws s3 cp --request-payer requester s3://sentinel-s2-l2a/tiles/6/L/XH/2024/3/26/0/R10m/B04.jp2 .
```

Drag and drop B04.jp2 to QGIS. Add *Bing Aerial* basemap (I like using [QuickMapServices](https://plugins.qgis.org/plugins/quick_map_services/) for this). Zoom to `-15.918, -145.932` (I can recommend the [Lat Lon Tools plugin](https://plugins.qgis.org/plugins/latlontools/)). 

These few steps in a gif:
![image](https://github.com/zabop/ndveye/blob/master/docs/dataImport.gif?raw=true)

#### Prepare input

We need a polygon to clip B04.tif by. Let's draw a polygon on the area of interest, and extract a raster from B04.tif. Save result to a tif file.  Make sure *Target CRS* is set to *EPSG:3857* and *Output data type* is set to *float32*.

![image](https://github.com/zabop/ndveye/blob/master/docs/cropRaster.gif?raw=true)

### Bush density estimation

## Contribute

