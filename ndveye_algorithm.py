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

__author__ = 'Bator Menyhert Koncz & Pal Szabo'
__date__ = '2024-03-25'
__copyright__ = '(C) 2024 by Bator Menyhert Koncz & Pal Szabo'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsPointXY,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
    QgsFeature
)
import rasterio
import shapely
import rasterio
import numpy as np
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

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    offset = "offset"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        # Add input raster field:
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr("Input raster")
        ))
        
        # Add float input parameter field called offset:
        self.addParameter(
            QgsProcessingParameterNumber(
                self.offset,
                self.tr("meritumdegradáció"),
                QgsProcessingParameterNumber.Double,
                0.2
        ))


    def processAlgorithm(self, parameters, context, feedback):
        with rasterio.open(parameters[self.INPUT], "r") as src:
            data = src.read(1)
            profile = src.profile
            bounds = src.bounds
            
        rowNum, colNum = data.shape

        totalWidth = bounds.right - bounds.left
        totalHeight = bounds.top - bounds.bottom

        pixelWidth = totalWidth / colNum
        pixelHeight = totalHeight / rowNum

        def pixelcoord_to_epsg3857(row, col):
            x = bounds.left + (col - 1 / 2) * pixelWidth
            y = bounds.top - (row - 1 / 2) * pixelHeight
            return x, y

        def point_to_square(centerx, centery, pixelWidth=pixelWidth, pixelHeight=pixelHeight):
            return shapely.geometry.Polygon(
                [
                    [centerx - pixelWidth / 2, centery - pixelHeight / 2],
                    [centerx + pixelWidth / 2, centery - pixelHeight / 2],
                    [centerx + pixelWidth / 2, centery + pixelHeight / 2],
                    [centerx - pixelWidth / 2, centery + pixelHeight / 2],
                    [centerx - pixelWidth / 2, centery - pixelHeight / 2],
                ]
            )

        data -= np.ones(shape=data.shape) * parameters[self.offset]

        kernel = photutils.segmentation.make_2dgaussian_kernel(1.4, size=7)  # FWHM = 3.0
        convolved_data = astropy.convolution.convolve(data, kernel)

        npixels = 4
        segment_map = photutils.segmentation.detect_sources(convolved_data, np.ones(shape=data.shape) * 0.08,
                                                            npixels=npixels, connectivity=4)

        segm_deblend = photutils.segmentation.deblend_sources(convolved_data, segment_map,
                                                              npixels=npixels, nlevels=500, contrast=0.0001,
                                                              progress_bar=True)

        shapes = []

        for label in segm_deblend.labels:
            xs, ys = np.where(np.array(segm_deblend) == label)
            targetPixels = [[x, y] for (x, y) in zip(xs, ys)]

            shapes.append(
                shapely.unary_union(
                    [
                        point_to_square(*pixelcoord_to_epsg3857(*each)).buffer(0.001)
                        for each in targetPixels
                    ]
                )
            )

        gpd.GeoSeries(shapes).set_crs(3857).to_file("/Users/palszabo/pal/ndveye/pixels.gpkg", driver="GPKG", layer="polygons", engine="pyogrio")
        
        shapes = [each.centroid for each in shapes]
        gpd.GeoSeries(shapes).set_crs(3857).to_file("/Users/palszabo/pal/ndveye/pixels.gpkg", driver="GPKG", layer="points", engine="pyogrio")
        
        return {"Found this many": len(shapes),"offset": parameters[self.offset]}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'ndveye'

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
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ndveyeAlgorithm()