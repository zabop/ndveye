# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ndveye
                                 A QGIS plugin
 Plant counting.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-03-25
        copyright            : (C) 2024 by Bator Menyhert Koncz & Pal Szabo
        email                : ndveye@protonmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = "Bator Menyhert Koncz & Pal Szabo"
__date__ = "2024-03-25"
__copyright__ = "(C) 2024 by Bator Menyhert Koncz & Pal Szabo"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsPointXY,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsSimpleLineSymbolLayer,
)
import os
import rasterio
import shapely
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
import astropy.convolution
import photutils.segmentation


class ndveyeAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT = "INPUT"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                "inputRasters",
                # accept any raster layers:
                self.tr("Input raster(s)"),
                QgsProcessing.TypeRaster,
            )
        )

        # Add float input parameter field called offset:
        self.addParameter(
            QgsProcessingParameterNumber(
                "Background offset",
                self.tr("Background offset"),
                QgsProcessingParameterNumber.Double,
                0.2,
            )
        )

        # Add float input parameter field called offset:
        self.addParameter(
            QgsProcessingParameterNumber(
                "Kernel FWHM",
                self.tr("Kernel FWHM"),
                QgsProcessingParameterNumber.Double,
                1.4,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                "Kernel size",
                self.tr("Kernel size"),
                QgsProcessingParameterNumber.Integer,
                7,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                "Detection threshold",
                self.tr("Detection threshold"),
                QgsProcessingParameterNumber.Double,
                0.08,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                "Minimum pixel count",
                self.tr("Minimum pixel count"),
                QgsProcessingParameterNumber.Integer,
                8,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                "Connectivity: use 8 instead of 4",
                self.tr("Connectivity: use 8 instead of 4"),
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                "Number of deblending thresholds",
                self.tr("Number of deblending thresholds"),
                QgsProcessingParameterNumber.Integer,
                500,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                "Minimum contrast for object separation",
                self.tr("Minimum contrast for object separation"),
                QgsProcessingParameterNumber.Double,
                0.0001,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                "Output: polygons",
                self.tr("Output: polygons"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                "Output: points",
                self.tr("Output: points"),
                defaultValue=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        polygondfs = []
        pointdfs = []
        for index, inputId in enumerate(parameters["inputRasters"]):
            counter = 0
            for _, v in QgsProject.instance().mapLayers().items():
                if v.id() == inputId:
                    inputFile = v.source()
                    counter += 1
            assert counter < 2, "Multiple layers with the same id found"

            with rasterio.open(inputFile, "r") as src:
                data = src.read(1)
                profile = src.profile
                bounds = src.bounds

            rowNum, colNum = data.shape

            totalWidth = bounds.right - bounds.left
            totalHeight = bounds.top - bounds.bottom

            pixelWidth = totalWidth / colNum
            pixelHeight = totalHeight / rowNum

            def pixelcoord_to_epsg3857(row, col):
                x = bounds.left + (col + 1 / 2) * pixelWidth
                y = bounds.top - (row + 1 / 2) * pixelHeight
                return x, y

            def point_to_square(
                centerx, centery, pixelWidth=pixelWidth, pixelHeight=pixelHeight
            ):
                return shapely.geometry.Polygon(
                    [
                        [centerx - pixelWidth / 2, centery - pixelHeight / 2],
                        [centerx + pixelWidth / 2, centery - pixelHeight / 2],
                        [centerx + pixelWidth / 2, centery + pixelHeight / 2],
                        [centerx - pixelWidth / 2, centery + pixelHeight / 2],
                        [centerx - pixelWidth / 2, centery - pixelHeight / 2],
                    ]
                )

            data -= np.ones(shape=data.shape) * parameters["Background offset"]

            kernel = photutils.segmentation.make_2dgaussian_kernel(
                parameters["Kernel FWHM"], size=parameters["Kernel size"]
            )
            convolved_data = astropy.convolution.convolve(data, kernel)

            segment_map = photutils.segmentation.detect_sources(
                convolved_data,
                np.ones(shape=data.shape) * parameters["Detection threshold"],
                npixels=parameters["Minimum pixel count"],
                connectivity=8 if parameters["Connectivity: use 8 instead of 4"] else 4,
            )

            segm_deblend = photutils.segmentation.deblend_sources(
                convolved_data,
                segment_map,
                npixels=parameters["Minimum pixel count"],
                nlevels=parameters["Number of deblending thresholds"],
                contrast=parameters["Minimum contrast for object separation"],
                progress_bar=True,
            )

            shapes = []
            for label in segm_deblend.labels:
                xs, ys = np.where(np.array(segm_deblend) == label)
                targetPixels = [[x, y] for (x, y) in zip(xs, ys)]

                shapes.append(
                    shapely.unary_union(
                        [
                            point_to_square(*pixelcoord_to_epsg3857(*each)).buffer(
                                0.001
                            )
                            for each in targetPixels
                        ]
                    )
                )
            group = os.path.basename(inputFile).replace(".tif", "")

            geom = gpd.GeoSeries(shapes).set_crs(3857)
            gdf = gpd.GeoDataFrame(geometry=geom)
            gdf["group"] = group
            polygondfs.append(gdf)

            geom = [each.centroid for each in shapes]
            gdf = gpd.GeoDataFrame(geometry=geom)
            gdf["group"] = group
            pointdfs.append(gdf)

        if parameters["Output: polygons"]:
            gpd.GeoDataFrame(pd.concat(polygondfs)).set_crs(3857).to_file(
                "/Users/palszabo/ndveye/polygons.gpkg",
                driver="GPKG",
                layer="polygons",
                engine="pyogrio",
            )
            polygonLayer = QgsProject.instance().addMapLayer(
                QgsVectorLayer(
                    "/Users/palszabo/ndveye/polygons.gpkg", "resultPolygons", "ogr"
                )
            )
            polygonLayer.renderer().symbol().changeSymbolLayer(
                0, QgsSimpleLineSymbolLayer(QColor("orange"), width=1)
            )

        if parameters["Output: points"]:
            gpd.GeoDataFrame(pd.concat(pointdfs)).set_crs(3857).to_file(
                "/Users/palszabo/ndveye/points.gpkg",
                driver="GPKG",
                layer="points",
                engine="pyogrio",
            )
            QgsProject.instance().addMapLayer(
                QgsVectorLayer(
                    "/Users/palszabo/ndveye/points.gpkg", "resultPoints", "ogr"
                )
            )

        return {
            "Found this many": len(shapes),
            "Background offset": parameters["Background offset"],
            "parameters": parameters,
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "ndveye"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ""

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return ndveyeAlgorithm()
