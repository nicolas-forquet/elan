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

# pylint: disable=no-member, broad-except, consider-using-f-string

import math

import processing
import requests
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

from ELAN.utils.tr import Translatable


class RoadsBuildingsAlgorithm(QgsProcessingAlgorithm, Translatable):
    """ELAN processing to extract OSM roads and buildings from a polygon zone"""

    POLYGON = "POLYGON"
    BUILDINGS_OUTPUT = "BUILDINGS_OUTPUT"
    MERGED_BUILDINGS_OUTPUT = "MERGED_BUILDINGS_OUTPUT"
    ROADS_OUTPUT = "ROADS_OUTPUT"
    PROJ = "PROJ"

    def createInstance(self):
        """Return an instance of this class"""
        return RoadsBuildingsAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanroadsbuildings"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Roads and buildings")

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
            """
            This algorithm queries the Overpass API to extract OSM (OpenStreetMap) data for buildings
            and roads within an area defined by a rectangle.

            - The user specifies a polygon layer to define the query area.

            - An Overpass query is formulated to extract entities of type "building" and "highway"
            within the specified area(s).

            - Three output layers are created:
            - A polygon layer for buildings.
            - A polygon layer for merged buildings (touching polygons).
            - A line layer for roads.
            - The building and road entities are added to the output layers.
            """
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGON, self.tr("Extraction area"), [Qgis.ProcessingSourceType.VectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.BUILDINGS_OUTPUT,
                self.tr("Buildings - Output layer"),
                Qgis.ProcessingSourceType.VectorPolygon,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.MERGED_BUILDINGS_OUTPUT,
                self.tr("Merged buildings - Output layer"),
                Qgis.ProcessingSourceType.VectorPolygon,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ROADS_OUTPUT, self.tr("Roads - Output layer"), Qgis.ProcessingSourceType.VectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(self.PROJ, self.tr("Reproject layers to the project's CRS"), False)
        )

    def processAlgorithm(
        self, parameters, context, feedback
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Here is where the processing itself takes place.
        """

        multistep_feedback = QgsProcessingMultiStepFeedback(4, feedback)
        multistep_feedback.setCurrentStep(1)
        multistep_feedback.setProgressText(self.tr("Downloading data..."))

        polygon = self.parameterAsSource(parameters, self.POLYGON, context)
        if polygon is None:
            raise QgsProcessingException(self.tr("Unable to get input polygon layer"))

        building_fields = QgsFields()
        road_fields = QgsFields()
        crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")

        # Get the extent of extraction polygon in 4326
        rect = polygon.sourceExtent()
        rect = QgsCoordinateTransform(polygon.sourceCrs(), crs_4326, QgsCoordinateTransformContext()).transform(rect)
        if math.isnan(rect.area()):
            raise QgsProcessingException(self.tr("The extent of the extraction area is null"))
        if rect.area() > 0.1:  # in degree squared it corresponds to an entire French department
            raise QgsProcessingException(self.tr("The extent of the extraction area is too big"))

        bbox = f"{rect.yMinimum()},{rect.xMinimum()},{rect.yMaximum()},{rect.xMaximum()}"
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json]
        [timeout:90];
        (
          way["building"]({bbox});
          way["highway"]({bbox});
        );
        out body;
        >;
        out skel qt;
        """
        response = requests.get(overpass_url, params={"data": overpass_query}, timeout=100)
        data = response.json()
        all_tags = set()
        osm_elements = data["elements"]
        for element in osm_elements:
            if "tags" in element:
                all_tags.update(element["tags"].keys())

        all_building_tags = sorted(tag for tag in all_tags if tag == "building:levels")
        all_road_tags = sorted(tag for tag in all_tags if tag == "highway")

        for tag in all_building_tags:
            building_fields.append(QgsField(tag, QMetaType.Type.QString))
        for tag in all_road_tags:
            road_fields.append(QgsField(tag, QMetaType.Type.QString))

        if (project := QgsProject.instance()) is not None and self.parameterAsBool(parameters, self.PROJ, context):
            dest_crs = project.crs()
        else:
            dest_crs = crs_4326

        # Temporary layers while processing
        temp_buildings_sink, temp_buildings_dest = QgsProcessingUtils.createFeatureSink(
            destination="", context=context, fields=building_fields, geometryType=Qgis.WkbType.Polygon, crs=dest_crs
        )
        if temp_buildings_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, "temp_buildings"))
        temp_roads_sink, temp_roads_dest = QgsProcessingUtils.createFeatureSink(
            destination="", context=context, fields=road_fields, geometryType=Qgis.WkbType.LineString, crs=dest_crs
        )
        if temp_roads_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, "temp_roads"))

        node_dict = {elem["id"]: (elem["lon"], elem["lat"]) for elem in osm_elements if elem["type"] == "node"}
        crs_transform = QgsCoordinateTransform(crs_4326, dest_crs, QgsCoordinateTransformContext())
        for element in osm_elements:
            if element["type"] not in ["way", "building"]:
                continue

            points = [QgsPointXY(*node_dict[node_id]) for node_id in element.get("nodes", []) if node_id in node_dict]

            if len(points) > 0 and "tags" in element:
                if "building" in element["tags"]:
                    feature = QgsFeature(building_fields)
                    geom = QgsGeometry.fromPolygonXY([points])
                    if dest_crs != crs_4326:
                        geom.transform(crs_transform)
                    feature.setGeometry(geom)

                    for tag in all_building_tags:
                        feature.setAttribute(tag, element["tags"].get(tag, None))
                    temp_buildings_sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert)

                if "highway" in element["tags"]:
                    feature = QgsFeature(road_fields)
                    geom = QgsGeometry.fromPolylineXY(points)
                    if dest_crs != crs_4326:
                        geom.transform(crs_transform)
                    feature.setGeometry(geom)

                    for tag in all_road_tags:
                        feature.setAttribute(tag, element["tags"].get(tag, None))
                    temp_roads_sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert)

        # Create QgsVectorLayer objects
        overlay = polygon.materialize(QgsFeatureRequest())
        temp_buildings = QgsProcessingUtils.mapLayerFromString(temp_buildings_dest, context)
        temp_roads = QgsProcessingUtils.mapLayerFromString(temp_roads_dest, context)
        if not isinstance(temp_buildings, QgsVectorLayer) or not isinstance(temp_roads, QgsVectorLayer):
            raise QgsProcessingException(self.tr("Error while retrieving layer"))

        # Create spatial indexes
        if (buildings_provider := temp_buildings.dataProvider()) is not None:
            buildings_provider.createSpatialIndex()
        if (roads_provider := temp_roads.dataProvider()) is not None:
            roads_provider.createSpatialIndex()

        # Clip the buildings inside the input polygons
        multistep_feedback.setCurrentStep(2)
        multistep_feedback.setProgressText(self.tr("Clipping buildings..."))
        buildings_clipped_dest = processing.run(
            "native:clip",
            {"INPUT": temp_buildings, "OVERLAY": overlay, "OUTPUT": parameters[self.BUILDINGS_OUTPUT]},
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        if context.willLoadLayerOnCompletion(buildings_clipped_dest):
            ld = context.layerToLoadOnCompletionDetails(buildings_clipped_dest)
            ld.name = self.tr("Buildings")
            ld.layerSortKey = 0

        # Merge buildings
        multistep_feedback.setCurrentStep(3)
        multistep_feedback.setProgressText(self.tr("Merging buildings..."))
        merged_buildings_dest = processing.run(
            "native:dissolve",
            {
                "INPUT": buildings_clipped_dest,
                "SEPARATE_DISJOINT": True,
                "OUTPUT": parameters[self.MERGED_BUILDINGS_OUTPUT],
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        if context.willLoadLayerOnCompletion(merged_buildings_dest):
            ld = context.layerToLoadOnCompletionDetails(merged_buildings_dest)
            ld.name = self.tr("Merged buidings")
            ld.layerSortKey = 1

        # Clip the roads inside the input polygons
        multistep_feedback.setCurrentStep(4)
        multistep_feedback.setProgressText(self.tr("Clipping roads..."))
        roads_clipped_dest = processing.run(
            "native:clip",
            {"INPUT": temp_roads, "OVERLAY": overlay, "OUTPUT": parameters[self.ROADS_OUTPUT]},
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        if context.willLoadLayerOnCompletion(roads_clipped_dest):
            ld = context.layerToLoadOnCompletionDetails(roads_clipped_dest)
            ld.name = self.tr("Roads")
            ld.layerSortKey = 2

        return {
            self.BUILDINGS_OUTPUT: buildings_clipped_dest,
            self.MERGED_BUILDINGS_OUTPUT: merged_buildings_dest,
            self.ROADS_OUTPUT: roads_clipped_dest,
        }
