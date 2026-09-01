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

import processing
from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateTransform,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProject,
    QgsProperty,
    QgsProviderRegistry,
    QgsReadWriteContext,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.gui import QgsCategorizedSymbolRendererWidget
from qgis.PyQt.QtXml import QDomDocument

from ELAN.processing.utils import LoadGpkgStylesPostProcessor, getLocalizedStylesDirectory
from ELAN.utils.tr import Translatable


class GroupingAlgorithm(QgsProcessingAlgorithm, Translatable):
    """Elan processing to group buildings together"""

    ROADS = "ROADS"
    BUILDINGS_CENTROIDS = "BUILDINGS_CENTROIDS"
    POPULATION_ATTRIBUTE_NAME = "POPULATION_ATTRIBUTE_NAME"
    ADJUSTMENT_FACTOR = "ADJUSTMENT_FACTOR"
    OUTPUT_GPKG = "OUTPUT_GPKG"

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
        """Return an instance of this class"""
        return GroupingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elangrouping"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Grouping")

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
            "This module helps identify buildings that would make sense to connect when "
            "considering decentralized scenarios (assistance in defining decentralized scenarios)."
            "<h2>Identification process</h2>"
            "The identification process involves three steps:"
            "<ol>"
            "    <li>"
            "    A buffer is applied around the centroids, with the buffer diameter determined by the population"
            "    <ul>"
            "        <li>function: adjustment factor * sqrt(population)</li>"
            "        <li>assumption: the more populated a centroid is, the greater the benefit of connecting it.</li>"
            "    </ul>"
            "    </li>"
            "    <li>"
            "    Identification of interconnected roads within the buffers"
            "    <ul>"
            "        <li>assumption: to be connected to one another, buildings must be linked by a common road.</li>"
            "    </ul>"
            "    </li>"
            "    <li>Grouping of buildings connected by a common road within the perimeter of their buffer.</li>"
            "</ol>"
            "<h2>Inputs:</h2>"
            "<ul>"
            "    <li>Building layer: building centroids projected onto roads</li>"
            "    <li>Road layer</li>"
            "    <li>Adjustment factor to adapt the function to your area (default: 30)</li>"
            "    <li>Population: attribute of the building layer corresponding to the population "
            "associated with each building</li>"
            "</ul>"
            "<h2>Outputs:</h2>"
            "<ul>"
            "    <li>Centroid buffers</li>"
            "    <li>Grouped roads: each road group is identified by a number visible on the output "
            "layer (symbology).</li>"
            "    <li>Grouped buildings: each centroid belongs to a group (one color per group on "
            "the output layer).</li>"
            "</ul>"
            "<br>"
            "<em>Note: The black centroids in the output correspond to buildings that could not be "
            "projected onto a road by the Project onto Roads module (distance to the road > maximum "
            "distance to the road for projection).</em>"
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Inputs
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS_CENTROIDS, self.tr("Snapped buildings"), [Qgis.ProcessingSourceType.VectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.ROADS, self.tr("Roads"), [Qgis.ProcessingSourceType.VectorLine])
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ADJUSTMENT_FACTOR,
                self.tr("Adjustment factor"),
                Qgis.ProcessingNumberParameterType.Double,
                30,
                minValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.POPULATION_ATTRIBUTE_NAME,
                self.tr("Population (field)"),
                "population",
                parentLayerParameterName=self.BUILDINGS_CENTROIDS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
            )
        )

        # Outputs
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_GPKG, self.tr("Result layers (.gpkg)"), self.tr("Geopackage files (*.gpkg)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Check inputs
        building_centroids_source = self.parameterAsSource(parameters, self.BUILDINGS_CENTROIDS, context)
        if building_centroids_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.BUILDINGS_CENTROIDS))
        roads_source = self.parameterAsSource(parameters, self.ROADS, context)
        if roads_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.ROADS))
        if building_centroids_source.sourceCrs() != roads_source.sourceCrs():
            raise QgsProcessingException(self.tr("The roads and building centroids layers must have the same CRS"))

        multistep_feedback = QgsProcessingMultiStepFeedback(7, feedback)

        # centroids buffer
        buffered_centroids = processing.run(
            "native:buffer",
            {
                "DISSOLVE": False,
                "DISTANCE": QgsProperty.fromExpression(
                    str(self.parameterAsDouble(parameters, self.ADJUSTMENT_FACTOR, context)) + " * "
                    f'sqrt("{self.parameterAsString(parameters, self.POPULATION_ATTRIBUTE_NAME, context)}")'
                ),
                "END_CAP_STYLE": 0,  # Round
                "INPUT": parameters[self.BUILDINGS_CENTROIDS],
                "JOIN_STYLE": 0,  # Round
                "MITER_LIMIT": 2,
                "SEGMENTS": 5,
                "SEPARATE_DISJOINT": False,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        multistep_feedback.setCurrentStep(1)
        if multistep_feedback.isCanceled():
            return {}

        # clip roads
        clipped_roads = processing.run(
            "native:clip",
            {
                "INPUT": parameters[self.ROADS],
                "OVERLAY": buffered_centroids,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        multistep_feedback.setCurrentStep(2)
        if multistep_feedback.isCanceled():
            return {}

        # buffer clipped roads
        buffer_clipped_roads = processing.run(
            "native:buffer",
            {
                "DISSOLVE": True,
                "DISTANCE": 2,
                "END_CAP_STYLE": 0,  # Round
                "INPUT": clipped_roads,
                "JOIN_STYLE": 0,  # Round
                "MITER_LIMIT": 2,
                "SEGMENTS": 5,
                "SEPARATE_DISJOINT": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        multistep_feedback.setCurrentStep(3)
        if multistep_feedback.isCanceled():
            return {}

        # add group id
        grouped_roads = processing.run(
            "native:addautoincrementalfield",
            {
                "INPUT": buffer_clipped_roads,
                "FIELD_NAME": "group_id",
                "START": 1,
                "MODULUS": 0,
                "GROUP_FIELDS": [],
                "SORT_EXPRESSION": "",
                "SORT_ASCENDING": True,
                "SORT_NULLS_FIRST": False,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        multistep_feedback.setCurrentStep(4)
        if multistep_feedback.isCanceled():
            return {}

        # join_by_location
        grouped_buildings = processing.run(
            "native:joinattributesbylocation",
            {
                "DISCARD_NONMATCHING": False,
                "INPUT": parameters[self.BUILDINGS_CENTROIDS],
                "JOIN": grouped_roads,
                "JOIN_FIELDS": ["group_id"],
                "METHOD": 0,  # Create separate feature for each matching feature (one-to-many)
                "PREDICATE": [5],  # are within
                "PREFIX": None,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=multistep_feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        multistep_feedback.setCurrentStep(5)
        if multistep_feedback.isCanceled():
            return {}

        # Get resulting layers
        if (
            (grouped_buildings_layer := context.getMapLayer(grouped_buildings)) is None
            or (grouped_roads_layer := context.getMapLayer(grouped_roads)) is None
            or (buffered_centroids_layer := context.getMapLayer(buffered_centroids)) is None
        ):
            raise QgsProcessingException(self.tr("Unable to retrieve layers from context"))
        layers_to_save = [grouped_buildings_layer, grouped_roads_layer, buffered_centroids_layer]

        # Set correct GPKG names to the layers to save
        grouped_buildings_layer.setName("grouped_buildings")
        grouped_roads_layer.setName("grouped_roads")
        buffered_centroids_layer.setName("buffered_centroids")

        # Write to GPKG
        output_layer_path = self.parameterAsString(parameters, self.OUTPUT_GPKG, context)
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = QgsVectorFileWriter.driverForExtension("gpkg")
        save_options.fileEncoding = context.defaultEncoding()
        save_options.feedback = multistep_feedback
        for i, layer in enumerate(layers_to_save):

            if not isinstance(layer, QgsVectorLayer):  # for type hint
                continue

            # Create the file if it is the first layer
            if i == 0:
                save_options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
            else:
                save_options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer

            # Remove fid if existing to regenerate it
            attrs = layer.fields().allAttributesList()
            if (fid_idx := layer.fields().indexFromName("fid")) >= 0:
                attrs.remove(fid_idx)
            save_options.attributes = attrs
            save_options.layerName = layer.name()

            # In QGIS < 4 we need to explicitly force the CRS
            save_options.ct = QgsCoordinateTransform(layer.crs(), layer.crs(), context.transformContext())

            # Write the layer in the GPKG
            write_error, error_message, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_layer_path, context.transformContext(), save_options
            )
            if write_error != QgsVectorFileWriter.WriterError.NoError:
                raise QgsProcessingException(self.tr("Error saving layer {}: {}").format(layer.name(), error_message))

        multistep_feedback.setCurrentStep(6)
        if multistep_feedback.isCanceled():
            return {}

        # Create details for loading layers
        # (names, ordering, post-processor for loading styles from gpkg)
        # Layers are ordered in QGIS panel exactly in the order of th elist below
        layers_to_load = {}
        project = QgsProject.instance()
        for i, (layer_name, layer_pretty_name) in enumerate(
            [
                ("buffered_centroids", self.tr("Buffered centroids")),
                ("grouped_roads", self.tr("Grouped roads")),
                ("grouped_buildings", self.tr("Grouped buildings")),
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

        return {self.OUTPUT_GPKG: output_layer_path}

    def saveStyles(self, output_layer_path):
        """
        Save the styles in the GPKG
        """

        styles_dir = getLocalizedStylesDirectory()
        if styles_dir is None:
            raise QgsProcessingException(self.tr("No styles directory found"))

        grouped_buildings_layer = QgsVectorLayer(output_layer_path + "|layername=grouped_buildings", "", "ogr")
        if not grouped_buildings_layer.isValid():
            raise QgsProcessingException(self.tr("Unable to load grouped buildings layer"))

        # We don't use QgsVectorLayer.loadNamedStyle to load the QML file because
        # with a GPKG provider, if the style is not found, the default style is loaded
        # so we get the wrong style!
        # To get around this, we load and read the XML Dom Document.
        doc = QDomDocument()
        with (styles_dir / "grouped_buildings.qml").open() as style_file:
            doc.setContent(style_file.read())
        grouped_buildings_layer.readSymbology(doc.firstChild(), "", QgsReadWriteContext())
        renderer = grouped_buildings_layer.renderer()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            raise QgsProcessingException(f"renderer does not have the right type: {renderer.__class__}")

        # Adjust categorized style to the number of categories
        renderer_widget = QgsCategorizedSymbolRendererWidget(grouped_buildings_layer, None, renderer)
        renderer_widget.addCategories()
        renderer_to_clone = renderer_widget.renderer()
        assert isinstance(renderer_to_clone, QgsCategorizedSymbolRenderer)
        new_renderer = renderer_to_clone.clone()
        assert isinstance(new_renderer, QgsCategorizedSymbolRenderer)
        nb_category = len(new_renderer.categories()) - 1
        new_renderer.deleteCategory(nb_category)
        grouped_buildings_layer.setRenderer(new_renderer)

        # Save styles in the GeoPackage (gpkg)
        provider_registry = QgsProviderRegistry.instance()
        ogr_provider = None
        if provider_registry is not None:
            ogr_provider = provider_registry.providerMetadata("ogr")
        if ogr_provider is None:
            raise QgsProcessingException("ogr provider not found")

        doc = QDomDocument()
        grouped_buildings_layer.exportNamedStyle(doc)
        if not ogr_provider.saveStyle(
            output_layer_path + "|layername=grouped_buildings",
            doc.toString(),
            "",
            self.tr("Grouped buildings"),
            self.tr("Color based on the group identifier"),
            "",
            False,
            "",
        ):
            raise QgsProcessingException("could not save buildings style")

        with (styles_dir / "grouped_roads.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=grouped_roads",
                style_file.read(),
                "",
                self.tr("Grouped roads"),
                self.tr("Grouped roads"),
                "",
                True,
                "",
            ):
                raise QgsProcessingException(self.tr("Error with grouped roads style"))
