# NDVeye Plugin

## Algorithm details

## Example workflows

### Corn counting

### Reef mapping

We can use NDVeye to improve OpenStreetMap, [an open spatial database](https://www.openstreetmap.org/about), *"built by a community of mappers that contribute and maintain data about roads, trails, cafés, railway stations, and much more, all over the world"*.

There are some yet unmapped reefs within lagoons of the Tuamotus islands:

![image](https://i.imgur.com/yu6lU5k.png)
![image](https://i.imgur.com/IFjXCix_d.webp?maxwidth=1520&fidelity=grand)

We can polygonize these reefs using NDVeye. Let's use Sentinel-2 imagery as raster input. [EO Browser](https://apps.sentinel-hub.com/eo-browser) can help us acquire suitable imagery. There, we can search for *Toau atoll*, edit cloud coverage settings, copy the s3 path of the image & visualize it straight away:

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
![image](https://github.com/zabop/ndveye/blob/master/docs/dataImport.gif?raw=true)

### Bush density estimation

## Contribute

