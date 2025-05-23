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

import uuid

import processing
from qgis.core import (
    Qgis,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsMemoryProviderUtils,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString,
    QgsProviderRegistry,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)
from qgis.PyQt.QtCore import QDateTime, QMetaType

from ELAN.processing.utils import getLocalizedStylesDirectory
from ELAN.utils.tr import Translatable


class ScenarioAlgorithm(QgsProcessingAlgorithm, Translatable):

    SCENARIO_NAME = "SCENARIO_NAME"
    SEWER_NETWORK = "SEWER_NETWORK"
    WETLAND_PROCESSES = "WETLAND_PROCESSES"
    SCENARIO_GPKG = "SCENARIO_GPKG"

    def createInstance(self):
        return ScenarioAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanscenario"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Create a scenario")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Processings")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanprocessings"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(
            """
            Create a scenario GeoPackage file contining all informations
            required for further analysis and evaluation.
            """
        )

    def initAlgorithm(self, configuration=None):

        self.addParameter(QgsProcessingParameterString(self.SCENARIO_NAME, self.tr("Scenario name")))
        self.addParameter(
            QgsProcessingParameterFile(self.SEWER_NETWORK, self.tr("Sewer network geopackage"), extension="gpkg")
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.WETLAND_PROCESSES, self.tr("Processes (one per WWTP)"))
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.SCENARIO_GPKG, self.tr("Scenario geopackage"), self.tr("Geopackage files (*.gpkg)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        sewer_network_gpkg = self.parameterAsFile(parameters, self.SEWER_NETWORK, context)
        output_layer_path = self.parameterAsString(parameters, self.SCENARIO_GPKG, context)

        # Load all sewer network process layers
        layer_names = [
            "sinks_layer",
            "pumping_stations",
            "lifting_stations",
            "sewer_pipes",
            "roads",
            "buildings",
            "info_network",
        ]
        layers = [
            QgsVectorLayer(f"{sewer_network_gpkg}|layername={layer_name}", layer_name, "ogr")
            for layer_name in layer_names
        ]

        # Load wetland process layer and check that there is only one feature per WWTP
        if (processes_source := self.parameterAsSource(parameters, self.WETLAND_PROCESSES, context)) is None or (
            processes_layer := processes_source.materialize(QgsFeatureRequest())
        ) is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.WETLAND_PROCESSES))
        if (
            len(processes_layer.uniqueValues(processes_layer.fields().indexFromName("sink_coords")))
            != processes_layer.featureCount()
        ):
            raise QgsProcessingException(self.tr("There is more than one process per WWTP"))
        layers.append(processes_layer)

        # Create and fill scenario metadata temporary layer
        metadata_layer = QgsMemoryProviderUtils.createMemoryLayer(
            "metadata",
            QgsFields(
                [
                    QgsField("scenario_name", QMetaType.Type.QString),
                    QgsField("scenario_date", QMetaType.Type.QDateTime),
                    QgsField("scenario_id", QMetaType.Type.QString),
                ]
            ),
            Qgis.WkbType.NoGeometry,
        )
        if metadata_layer is None:
            raise QgsProcessingException(self.tr("Could not create metadata scenario layer"))
        if not metadata_layer.startEditing():
            raise QgsProcessingException(self.tr("Error when editing metadata for scenario"))
        if not metadata_layer.addFeature(
            QgsVectorLayerUtils.createFeature(
                metadata_layer,
                QgsGeometry(),
                {
                    0: self.parameterAsString(parameters, self.SCENARIO_NAME, context),
                    1: QDateTime.currentDateTime(),
                    2: str(uuid.uuid4()),
                },
            )
        ):
            raise QgsProcessingException(self.tr("Error when creating metadata for scernario"))
        if not metadata_layer.commitChanges():
            raise QgsProcessingException(self.tr("Error when saving metadata for scenario"))

        # Load metadata style
        if (styles_dir := getLocalizedStylesDirectory()) is None:
            raise QgsProcessingException(self.tr("No styles directory found"))
        err_msg, ok = metadata_layer.loadNamedStyle(str(styles_dir / "scenario_metadata.qml"))
        if not ok:
            raise QgsProcessingException(self.tr("Error when loading metadata style: {}").format(err_msg))
        layers.append(metadata_layer)

        # Package all layers.
        # Save styles is set to False because some layers may have more than one style, so we
        # take care of saving all styles directly in the geopackage in the next step
        processing.run(
            "native:package",
            {
                "LAYERS": layers,
                "OUTPUT": output_layer_path,
                "OVERWRITE": True,
                "SAVE_STYLES": False,
                "SAVE_METADATA": False,
                "SELECTED_FEATURES_ONLY": False,
                "EXPORT_RELATED_LAYERS": False,
            },
            context=context,
            is_child_algorithm=True,
            feedback=feedback,
        )

        # Saving styles in the new GeoPackage
        if (provider_registry := QgsProviderRegistry.instance()) is None or (
            ogr_provider := provider_registry.providerMetadata("ogr")
        ) is None:
            raise QgsProcessingException(self.tr("Unexpected error while saving styles"))
        for layer in layers:
            style_count, styles_ids, styles_names, styles_descriptions = layer.listStylesInDatabase()[:4]
            for style_name, style_id, style_description in zip(
                styles_names[:style_count], styles_ids[:style_count], styles_descriptions[:style_count]
            ):
                if not ogr_provider.saveStyle(
                    output_layer_path + f"|layername={layer.name()}",
                    layer.getStyleFromDatabase(style_id)[0],
                    "",
                    style_name,
                    style_description,
                    "",
                    False,
                    "",
                ):
                    raise QgsProcessingException(self.tr("Error while saving {} style").format(style_name))

        return {self.SCENARIO_GPKG: output_layer_path}
