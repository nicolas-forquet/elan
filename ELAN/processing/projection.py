"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import geopandas as gpd
import pandas as pd
from qgis import processing
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from ELAN.snap_buildings_to_roads import snap_buildings_to_road_vertices
from ELAN.utils.tr import Translatable


class SnapOnRoadsAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    This class projects building centroids onto the nearest road vertices within a user-defined maximum distance.
    """

    USER_TOTAL_POPULATION = "USER_TOTAL_POPULATION"
    MAX_DISTANCE_TO_ROAD = "MAX_DISTANCE_TO_ROAD"
    BUILDINGS_INPUT_DATA = " BUILDINGS_INPUT_DATA"
    ROADS_INPUT_DATA = "ROADS_INPUT_DATA"
    OUTPUT_AGGREGATED = "OUTPUT_AGGREGATED"
    OUTPUT_LINES = "OUTPUT_LINES"

    def createInstance(self):
        return SnapOnRoadsAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanprojectionroads"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Projection on roads")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Data pre-processing")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanpreprocessings"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """

        return self.tr(
            "This module projects building centroids onto the nearest road vertices within a "
            "user-defined maximum distance.\n"
            "The purpose of this spatial operation is to reduce the number of pumping stations "
            "or connection points that are not relevant from a municipal perspective - "
            "specifically those representing private lateral connections between individual "
            "buildings and the public road network.\n"
            "By snapping buildings to the closest road within a specified distance, the script "
            "prevents these private connections from being counted as distinct infrastructure "
            "needs. This step helps isolate connections that actually relate to the public "
            "network and simplifies subsequent analysis."
            "<h2>Inputs:</h2>"
            "<ul>"
            "    <li>Building layer: centroid locations of buildings</li>"
            "    <li>Road layer: road geometry used for snapping</li>"
            "    <li>Total population: numeric input representing overall population count</li>"
            "    <li>Maximum distance for projection: maximum search distance for snapping "
            "        buildings to roads</li>"
            "</ul>"
            "<h2>Outputs:</h2>"
            "<ul>"
            "<h3>Building features are preserved, with a new status column:</h3>"
            "    <li>Projected → successfully snapped to a nearby road</li>"
            "    <li>Not_projected → no road found within the specified distance</li>"
            "<h3>Centroids that fall on the same road vertex are merged, with:</h3>"
            "    <li>Population values aggregated by sum</li>"
            "    <li>A new column recording how many buildings were projected to that vertex</li>"
            "</ul>"
        )

    def initAlgorithm(self, configuration=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.USER_TOTAL_POPULATION,
                self.tr("Total population"),
                Qgis.ProcessingNumberParameterType.Integer,
                defaultValue=1000,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE_TO_ROAD,
                self.tr("Maximum distance to road for projection (m)"),
                Qgis.ProcessingNumberParameterType.Integer,
                defaultValue=40,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROADS_INPUT_DATA, self.tr("Road layer"), [Qgis.ProcessingSourceType.VectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS_INPUT_DATA, self.tr("Building layer"), [Qgis.ProcessingSourceType.VectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_AGGREGATED,
                self.tr("Projected centroids - Output layer"),
                Qgis.ProcessingSourceType.VectorLine,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES, self.tr("Projection lines - Output layer"), Qgis.ProcessingSourceType.VectorLine
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        max_distance_value = self.parameterAsInt(parameters, self.MAX_DISTANCE_TO_ROAD, context)
        population_value = self.parameterAsInt(parameters, self.USER_TOTAL_POPULATION, context)
        roads_source = self.parameterAsSource(parameters, self.ROADS_INPUT_DATA, context)
        buildings_source = self.parameterAsSource(parameters, self.BUILDINGS_INPUT_DATA, context)

        # Create GeoDataFrame from roads_source and buildings_source
        roads_gdf = gpd.GeoDataFrame.from_features(roads_source.getFeatures())
        roads_gdf.set_crs(roads_source.sourceCrs().authid(), inplace=True)

        buildings_gdf = gpd.GeoDataFrame.from_features(buildings_source.getFeatures())
        buildings_gdf.set_crs(buildings_source.sourceCrs().authid(), inplace=True)

        # Call snap_buildings_to_road_vertices script
        aggregated, lines = snap_buildings_to_road_vertices(
            buildings_gdf, roads_gdf, population_value, max_distance=max_distance_value
        )

        # Create output layer

        roads_crs = roads_source.sourceCrs()
        aggregated_fields = QgsFields()
        lines_fields = QgsFields()

        # get fields
        for col, dtype in zip(aggregated.columns, aggregated.dtypes):
            if col == "geometry":
                continue
            if dtype == "int":
                qgs_type = QVariant.Int
            elif dtype == "float":
                qgs_type = QVariant.Double
            else:
                qgs_type = QVariant.String
            aggregated_fields.append(QgsField(col, qgs_type))

        for col, dtype in zip(lines.columns, lines.dtypes):
            if col == "geometry":
                continue
            if dtype == "int":
                qgs_type = QVariant.Int
            elif dtype == "float":
                qgs_type = QVariant.Double
            else:
                qgs_type = QVariant.String
            lines_fields.append(QgsField(col, qgs_type))

        # Create layer with sink

        (aggregated_sink, aggregeted_dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT_AGGREGATED, context, aggregated_fields, QgsWkbTypes.Point, roads_crs
        )
        (lines_sink, lines_dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT_LINES, context, lines_fields, QgsWkbTypes.LineString, roads_crs
        )

        # Fill the layer

        for _, row in aggregated.iterrows():
            feat = QgsFeature()
            feat.setFields(aggregated_fields)
            attrs = [None if pd.isna(row[col]) else row[col] for col in aggregated.columns if col != "geometry"]
            feat.setAttributes(attrs)
            feat.setGeometry(QgsGeometry.fromWkt(row.geometry.wkt))
            aggregated_sink.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

        for _, row in lines.iterrows():
            feat = QgsFeature()
            feat.setFields(lines_fields)
            attrs = [None if pd.isna(row[col]) else row[col] for col in lines.columns if col != "geometry"]

            feat.setAttributes(attrs)
            feat.setGeometry(QgsGeometry.fromWkt(row.geometry.wkt))
            lines_sink.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

        return {self.OUTPUT_AGGREGATED: aggregated_sink, self.OUTPUT_LINES: lines_sink}
