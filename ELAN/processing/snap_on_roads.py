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

from collections import defaultdict

import geopandas as gpd
import pandas as pd
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
)
from qgis.PyQt.QtCore import QMetaType
from shapely.geometry import LineString, Point

from ELAN.utils.tr import Translatable


class SnapOnRoadsAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    This class projects building centroids onto the nearest road vertices within a user-defined maximum distance.
    """

    POPULATION_FIELD = "POPULATION_FIELD"
    MAX_DISTANCE_TO_ROAD = "MAX_DISTANCE_TO_ROAD"
    BUILDINGS_INPUT_DATA = "BUILDINGS_INPUT_DATA"
    ROADS_INPUT_DATA = "ROADS_INPUT_DATA"
    OUTPUT_AGGREGATED = "OUTPUT_AGGREGATED"
    OUTPUT_LINES = "OUTPUT_LINES"

    def createInstance(self):
        """Return an instance of this class"""
        return SnapOnRoadsAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elansnaponroads"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Snap on roads")

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
        parameters and outputs associated with it.
        """

        return self.tr(
            "This module projects building centroids onto the nearest road vertices within a"
            "user-defined maximum distance.\n"
            "The purpose of this spatial operation is to reduce the number of pumping stations"
            "or connection points that are not relevant from an urban perspective -"
            "specifically those representing private lateral connections between individual"
            "buildings and the public road network.\n"
            "By snapping buildings to the closest road vertex within a specified distance, the script"
            "prevents these private connections from being counted as distinct infrastructure "
            "needs. This step helps isolate connections that actually relate to the public"
            "network and simplifies subsequent analysis."
            "<h2>Inputs:</h2>"
            "<ul>"
            "    <li>Building layer: centroid locations of buildings</li>"
            "    <li>Road layer: road geometry used for snapping</li>"
            "    <li>Building population field: field from the buildings layer with the population attribute</li>"
            "    <li>Maximum distance to road for snapping: maximum search distance for snapping "
            "        buildings to roads</li>"
            "</ul>"
            "<h2>Outputs:</h2>"
            "<ul>"
            "<h3>Building features are preserved, with a new status column:</h3>"
            "    <li>Projected: successfully snapped to a nearby road</li>"
            "    <li>Not projected: no road found within the specified distance</li>"
            "<h3>Centroids that fall on the same road vertex are merged, with:</h3>"
            "    <li>Population values aggregated by sum</li>"
            "    <li>A new column recording how many buildings were projected to that vertex</li>"
            "</ul>"
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROADS_INPUT_DATA, self.tr("Road layer"), [Qgis.ProcessingSourceType.VectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS_INPUT_DATA, self.tr("Building layer"), [Qgis.ProcessingSourceType.VectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.POPULATION_FIELD,
                self.tr("Building population field"),
                parentLayerParameterName=self.BUILDINGS_INPUT_DATA,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.MAX_DISTANCE_TO_ROAD,
                self.tr("Maximum distance to road for snapping (m)"),
                defaultValue=40,
                parentParameterName=self.ROADS_INPUT_DATA,
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

    def getFieldsFromDataFrame(self, df) -> QgsFields:
        """
        Get fields
        """

        fields = QgsFields()
        for col, dtype in zip(df.columns, df.dtypes):
            if col == "geometry":
                continue
            if dtype == "int":
                qgs_type = QMetaType.Type.Int
            elif dtype == "float":
                qgs_type = QMetaType.Type.Double
            else:
                qgs_type = QMetaType.Type.QString
            fields.append(QgsField(col, qgs_type))
        return fields

    def fillSinkWithDataFrame(self, output_df, fields, sink) -> QgsFeatureSink:
        """
        Fill the sink
        """
        for _, row in output_df.iterrows():
            feat = QgsFeature()
            feat.setFields(fields)
            attrs = [None if pd.isna(row[col]) else row[col] for col in output_df.columns if col != "geometry"]
            feat.setAttributes(attrs)
            feat.setGeometry(QgsGeometry.fromWkt(row.geometry.wkt))
            sink.addFeature(feat, QgsFeatureSink.Flag.FastInsert)
        return sink

    def processAlgorithm(self, parameters, context, feedback):  # pylint: disable=unused-argument, too-many-locals
        """
        Here is where the processing itself takes place.
        """

        max_distance_value = self.parameterAsInt(parameters, self.MAX_DISTANCE_TO_ROAD, context)
        population_value = self.parameterAsString(parameters, self.POPULATION_FIELD, context)
        roads_source = self.parameterAsSource(parameters, self.ROADS_INPUT_DATA, context)
        buildings_source = self.parameterAsSource(parameters, self.BUILDINGS_INPUT_DATA, context)

        if roads_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.ROADS_INPUT_DATA))
        if buildings_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.BUILDINGS_INPUT_DATA))

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

        # get fields
        aggregated_fields = self.getFieldsFromDataFrame(aggregated)
        lines_fields = self.getFieldsFromDataFrame(lines)
        # Create layer with sink

        (aggregated_sink, aggregeted_dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT_AGGREGATED, context, aggregated_fields, Qgis.WkbType.Point, roads_crs
        )
        (lines_sink, lines_dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT_LINES, context, lines_fields, Qgis.WkbType.LineString, roads_crs
        )

        # Fill the layer
        aggregated_sink = self.fillSinkWithDataFrame(aggregated, aggregated_fields, aggregated_sink)
        lines_sink = self.fillSinkWithDataFrame(lines, lines_fields, lines_sink)

        if aggregated_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_AGGREGATED))
        if lines_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LINES))

        return {self.OUTPUT_AGGREGATED: aggregeted_dest_id, self.OUTPUT_LINES: lines_dest_id}


def explode_multilines(gdf):
    """
    Explodes MultiLineStrings into individual LineStrings.
    """
    gdf = gdf.explode(ignore_index=True)
    return gdf[gdf.geometry.type == "LineString"].reset_index(drop=True)


def snap_buildings_to_road_vertices(buildings_gdf, roads_gdf, value_field, max_distance=500):
    """
    Snap centroids to road vertices, aggregate population at each vertex,
    and return individual building status and projection lines.

    Returns:
        - aggregated_gdf: snapped vertex points with sum + count
        - projection_lines_gdf: LineStrings from original centroid to snapped vertex
    """

    if buildings_gdf.crs != roads_gdf.crs:
        raise ValueError("CRS mismatch between buildings and roads")

    roads_gdf = explode_multilines(roads_gdf)
    roads_gdf = roads_gdf[roads_gdf.geometry.is_valid]

    # Extract all road vertices
    vertex_index = {}
    vertices = []
    for line in roads_gdf.geometry:
        for coord in line.coords:
            pt = Point(coord)
            key = (round(pt.x, 6), round(pt.y, 6))
            if key not in vertex_index:
                vertex_index[key] = pt
                vertices.append(pt)

    vertex_gdf = gpd.GeoDataFrame(geometry=vertices, crs=roads_gdf.crs)
    vertex_sindex = vertex_gdf.sindex

    # Containers
    aggregation = defaultdict(lambda: {"geometry": None, "count": 0, f"{value_field}": 0.0})
    projection_lines = []
    building_records = []

    for _, row in buildings_gdf.iterrows():
        centroid = row.geometry.centroid
        value = row[value_field]

        # Find nearest vertex within threshold
        possible_idx = list(vertex_sindex.intersection(centroid.buffer(max_distance).bounds))
        candidates = vertex_gdf.iloc[possible_idx]

        nearest_pt = None
        min_dist = float("inf")
        for _, v_row in candidates.iterrows():
            dist = centroid.distance(v_row.geometry)
            if dist < min_dist and dist <= max_distance:
                nearest_pt = v_row.geometry
                min_dist = dist

        if nearest_pt:
            # Snap and aggregate
            key = (round(nearest_pt.x, 6), round(nearest_pt.y, 6))
            pt = vertex_index[key]
            aggregation[key]["geometry"] = pt
            aggregation[key]["count"] += 1
            aggregation[key][str(value_field)] += value

            # Record projection line
            projection_lines.append(LineString([(centroid.x, centroid.y), (pt.x, pt.y)]))

            # Record individual building
            building_records.append({**row.drop("geometry"), "geometry": pt, "status": "snapped"})

        else:
            # Not snapped
            building_records.append({**row.drop("geometry"), "geometry": centroid, "status": "not_snapped"})

    # Build outputs
    aggregated_gdf = gpd.GeoDataFrame(list(aggregation.values()), crs=buildings_gdf.crs)
    lines_gdf = gpd.GeoDataFrame(geometry=projection_lines, crs=buildings_gdf.crs)
    status_gdf = gpd.GeoDataFrame(building_records, crs=buildings_gdf.crs)

    return aggregated_gdf, lines_gdf
