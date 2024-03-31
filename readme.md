# NDVeye Plugin

## I. Algorithm details

## II. Example workflows

### II.1 Corn counting

#### Motivation

In agriculture, it is often useful to know how many corn plants grow in a section of land. Experiments on different types of plants & treatments are often very localised. It is therefore helpful to be able quickly count how many corn plants there are in a row.


#### Get data

Download an example NDVI raster:
```
curl -O 'https://raw.githubusercontent.com/zabop/ndveye/master/docs/NDVIsource.tif'
```

If you prefer not using the terminal, you can also download the file from [here](https://github.com/zabop/ndveye/raw/master/docs/NDVIsource.tif).

(We got the data using a DJI drone. We modified the location for privacy reasons.)

#### Prepare input

Open the downloaded TIF file in QGIS. Draw a polygon around some of the rows:
![image](https://github.com/zabop/ndveye/blob/master/docs/drawCornSections.gif?raw=true)

Create 4 raster files from these polygons:
![image](https://github.com/zabop/ndveye/blob/master/docs/extract4rasters.gif?raw=true)


We will use these rasters as input to NDVI. Explore pixel values:
- Background (ie non-corn) pixel values are around $0.15$
- Target pixel values are more than that by around $0.1$
- The smallest targets consist of around 2 pixels
- Smallest target's diameter is around 2 pixels. We found by trial and error that it is usually beneficial to undershoot this parameter, so let's just say smallest diameter is around 1.

Keeping these values in mind, we can launch NDVeye to identify corn plants:
![image](https://github.com/zabop/ndveye/blob/master/docs/ndveye_for_corn.gif?raw=true)



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

We can use the *Identify Features* functionality to explore the pixel values of the layer *in* we just created:

![image](https://i.imgur.com/gaT5ym3.png)

The background, ie non-reef water pixels have value around a 1000. The reefs have pixel values a few hundred more. The smallest reefs we can hope to identify are 1 or 2 pixels wide, consisting of ~4 pixels at a minimum.

#### Launch NDVeye

Open NDVeye from the Processing Toolbox. Specify input parameters, keeping in mind the numbers in the previous paragraph. Since we don't need deblending (ie we don't want to separate reefs which are touching), I set the *Minimum contrast for object separation* field to one.
![image](https://github.com/zabop/ndveye/blob/master/docs/ndveye_reef_detection.gif?raw=true)
In the end, two layers (one of points, one of polygons) are added to canvas.

#### Polish results

We can edit the style settings of our newly created polygon layer, and inspect the results. If we find there many reefs we haven't found, we need to change the input parameters (lowering *Detection threshold* would probably be a good first try.) Overall, this run was fairly successful, we found most reefs. There are a few false detections, but we cand delete these easily (I press the Backspace after highlighting the erroneous polygons):
![image](https://github.com/zabop/ndveye/blob/master/docs/deletePolygons.gif?raw=true)
Quite many reefs have been found!

### Bush density estimation

## Contribute

