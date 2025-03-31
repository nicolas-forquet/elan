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

import json

import processing
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFields,
    QgsProject,
    QgsGeometry,
    QgsPoint,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsProviderRegistry,
)

from ELAN.processing.utils import GpkgVectorDestination, LoadGpkgStylesPostProcessor, getLocalizedStylesDirectory
from ELAN.utils.tr import Translatable


class TrenchProfileAlgorithm(QgsProcessingAlgorithm, Translatable):

    INPUT_LAYER = "INPUT_LAYER"
    OUTPUT_LAYER = "OUTPUT_LAYER"

    def __init__(self):
        super().__init__()

        # Post processor for the output layers
        # (one post processor per layer)
        self.post_processors = [
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
        ]

    def createInstance(self):
        return TrenchProfileAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elantrenchprofile"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Longitudinal sewer profile")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Results exploration")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "results_exploration"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(
            "This module creates layer of Z points from a sewer pipes layer "
            "created by the sewer network module, to be explored with the QGIS elevation profile tool."
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                self.tr("Sewer layer from Sewer module"),
                [Qgis.ProcessingSourceType.VectorLine],
            )
        )

        self.addParameter(GpkgVectorDestination(self.OUTPUT_LAYER, self.tr("Result layers (.gpkg)")))

    def processAlgorithm(self, parameters, context, feedback):

        input_source = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        if input_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LAYER))

        # Create a field list without comments and aliases to avoid having the warnings
        # about comments and aliases not compatible with memory layers
        input_fields = QgsFields()
        for input_field in input_source.fields():
            input_field.setAlias("")
            input_field.setComment("")
            input_fields.append(input_field)

        # Create sinks
        output_trench_line_sink, output_trench_line_dest = QgsProcessingUtils.createFeatureSink(
            "memory:3d_pipes", context, input_fields, Qgis.WkbType.LineStringZ, input_source.sourceCrs()
        )
        if output_trench_line_sink is None:
            raise QgsProcessingException(self.tr("Unable to create temporary output layer"))

        output_trench_sink, output_trench_dest = QgsProcessingUtils.createFeatureSink(
            "memory:sewer_profile", context, QgsFields(), Qgis.WkbType.PointZ, input_source.sourceCrs()
        )
        if output_trench_sink is None:
            raise QgsProcessingException(self.tr("Unable to create temporary output layer"))

        output_dem_sink, output_dem_dest = QgsProcessingUtils.createFeatureSink(
            "memory:land_profile", context, QgsFields(), Qgis.WkbType.PointZ, input_source.sourceCrs()
        )
        if output_dem_sink is None:
            raise QgsProcessingException(self.tr("Unable to create temporary output layer"))

        # Get output geopackage path
        output_layer_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_LAYER, context)

        multistep_feedback = QgsProcessingMultiStepFeedback(2, feedback)
        multistep_feedback.setCurrentStep(0)

        feature_count = input_source.featureCount()
        for i, feature in enumerate(input_source.getFeatures()):
            multistep_feedback.setProgress(i / feature_count * 100)
            feature: QgsFeature  # type hint because getFeatures() iterator has an incomplete python type
            try:
                trench_profile = json.loads(feature.attribute("trench_depth_profile"))
                profile = json.loads(feature.attribute("profile"))
            except KeyError:
                raise QgsProcessingException(
                    self.tr(
                        "Necessary attributes not found, "
                        "the sewer pipes layer needs to be issued from the sewer network module."
                    )
                )

            # If pressurized then reconstruct the path of the trench from the profile
            if feature["pressurized"]:
                tmin = profile[0][1] - trench_profile[0][1]
                trench_profile = [[dist, z - tmin] for dist, z in profile]

            # The idea here is to create a LineStringZ composed of every point from the original line
            # and every new point created with the "trench_depth_profile" list.
            feature_geometry = feature.geometry()

            # List of pairs [dist, QgsPoint] where dist = distance from the begining of the line, but
            # with QgsPoint a XYZ point where XY are computed with geometry interpolation and Z is from "trench_depth_profile".
            z_points = [
                [distance, QgsPoint(point.x(), point.y(), z)]
                for point, z, distance in [
                    [feature_geometry.interpolate(distance).asPoint(), z, distance] for distance, z in trench_profile
                ]
            ]

            # List of pairs [dist, QgsPoint] where dist = distance from the begining of the line, and QgsPoint are
            # constructed from the original feature vertices.
            # We don't need the first and last points because they are already in z_points from "trench_depth_profile".
            points = [
                [feature_geometry.lineLocatePoint(QgsGeometry.fromPointXY(point)), QgsPoint(point.x(), point.y())]
                for point in feature_geometry.asPolyline()[1:-1]
            ]

            # Set the Z of each point in the points list.
            # We go through each point, and compute its Z by interpolating from the Z values of its surrounding points from z_points.
            i, j = 0, 0
            while j < len(points):
                dist, point = points[j]
                point.convertTo(Qgis.WkbType.PointZ)
                dist_1, point_z_1 = z_points[i]
                dist_2, point_z_2 = z_points[i + 1]
                if dist_1 < dist < dist_2:
                    point.setZ(point_z_1.z() + (dist - dist_1) / (dist_2 - dist_1) * (point_z_2.z() - point_z_1.z()))
                    j += 1  # next point
                else:
                    i += 1  # next both point_z

            # We concatenate the 2 lists and sort it by distance from the begining of the line.
            all_points = sorted(z_points + points, key=lambda x: x[0])

            # We create the final 3D feature with all the attributes from the input feature.
            line_feature = QgsFeature()
            line_feature.setFields(feature.fields())
            line_feature.setAttributes(feature.attributes())
            line_feature.setGeometry(QgsGeometry.fromPolyline([p[1] for p in all_points]))
            output_trench_line_sink.addFeature(line_feature)

            # for trench profile, simply create a point feature for each element in "trench_profile" attribute.
            epsilon = 1e-9
            trench_profile[0][0] += epsilon
            trench_profile[-1][0] -= epsilon
            for interpolate_distance, z in trench_profile:
                point = feature.geometry().interpolate(interpolate_distance).asPoint()
                pointz = QgsPoint(point.x(), point.y(), z)
                output_feature = QgsFeature()
                output_feature.setGeometry(QgsGeometry.fromPoint(pointz))
                output_trench_sink.addFeature(output_feature)

            # for DEM profile, simply create a point feature for each element in "profile" attribute.
            for interpolate_distance, z in profile:
                point = feature.geometry().interpolate(interpolate_distance).asPoint()
                pointz = QgsPoint(point.x(), point.y(), z)
                output_feature = QgsFeature()
                output_feature.setGeometry(QgsGeometry.fromPoint(pointz))
                output_dem_sink.addFeature(output_feature)

        # Save all layers in the output geopackage file
        multistep_feedback.setCurrentStep(1)
        processing.run(
            "native:package",
            {
                "LAYERS": [output_trench_dest, output_dem_dest, output_trench_line_dest],
                "OUTPUT": output_layer_path,
                "OVERWRITE": False,
                "SAVE_STYLES": False,
                "SAVE_METADATA": False,
                "SELECTED_FEATURES_ONLY": False,
                "EXPORT_RELATED_LAYERS": False,
            },
            context=context,
            is_child_algorithm=True,
            feedback=multistep_feedback,
        )

        # Create details for loading layers
        # (names, ordering, post-processor for loading styles from gpkg)
        # Layers are ordered in QGIS panel exactly in the order of th elist below
        layers_to_load = {}
        project = QgsProject.instance()
        for i, (layer_name, layer_pretty_name) in enumerate(
            [
                ("land_profile", self.tr("Land profile")),
                ("sewer_profile", self.tr("Sewer profile")),
                ("3d_pipes", self.tr("3D pipes")),
            ]
        ):
            layer_details = context.LayerDetails()
            layer_details.name = layer_pretty_name
            layer_details.forceName = True
            layer_details.layerSortKey = i
            layer_details.setPostProcessor(self.post_processors[i])
            if project is not None:  # need to set the project for QGIS versions < 3.42.0
                layer_details.project = project
            layers_to_load[f"{output_layer_path}|layername={layer_name}"] = layer_details
        context.setLayersToLoadOnCompletion(layers_to_load)

        try:
            self.saveStyles(output_layer_path)
        except Exception as e:
            raise QgsProcessingException(self.tr("Unexpected error while saving styles: {}").format(str(e))) from e

        return {}

    def saveStyles(self, output_layer_path):
        """
        Save the styles in the GPKG
        """

        provider_registry = QgsProviderRegistry.instance()
        ogr_provider = None
        if provider_registry is not None:
            ogr_provider = provider_registry.providerMetadata("ogr")
        if ogr_provider is None:
            raise QgsProcessingException(self.tr("Unexpected error while saving styles"))

        styles_dir = getLocalizedStylesDirectory()
        if styles_dir is None:
            raise QgsProcessingException(self.tr("No styles directory found"))

        with (styles_dir / "3d_sewer_pipes_diameters.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=3d_pipes",
                style_file.read(),
                "",
                self.tr("Diameters"),
                self.tr("Width based on diameter"),
                "",
                False,
                "",
            ):
                raise Exception(self.tr("Error with diameters style"))

        with (styles_dir / "3d_sewer_pipes_gravity.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=3d_pipes",
                style_file.read(),
                "",
                self.tr("Gravity-driven"),
                self.tr("Color based on slope"),
                "",
                True,  # Default gravity style
                "",
            ):
                raise Exception(self.tr("Error with gravity-driven style"))

        with (styles_dir / "land_profile.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=land_profile",
                style_file.read(),
                "",
                self.tr("Land profile"),
                self.tr("Land profile"),
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with land profile style"))

        with (styles_dir / "trench_profile.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_profile",
                style_file.read(),
                "",
                self.tr("Sewer profile"),
                self.tr("Sewer profile"),
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with sewer profile style"))
