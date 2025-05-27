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

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import processing
import yaml
from qgis.core import (
    NULL,
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateTransformContext,
    QgsFeatureRequest,
    QgsGraduatedSymbolRenderer,
    QgsLineSymbol,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProject,
    QgsProviderRegistry,
    QgsReadWriteContext,
    QgsSymbol,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.gui import QgsCategorizedSymbolRendererWidget
from qgis.PyQt.QtXml import QDomDocument

from ELAN.__about__ import DIR_PLUGIN_ROOT
from ELAN.processing.utils import LoadGpkgStylesPostProcessor, getLocalizedStylesDirectory
from ELAN.utils.dependencies_utils import EXTERNAL_LIRBARIES_DIR
from ELAN.utils.qgis_utils import getInterpreterPath
from ELAN.utils.tr import Translatable


class SewerNetworkAlgorithm(QgsProcessingAlgorithm, Translatable):

    OUTPUT_DIR = "OUTPUT_DIR"
    DEM_FILE_PATH = "DEM_FILE_PATH"
    ROADS_INPUT_DATA = "ROADS_INPUT_DATA"
    BUILDINGS_INPUT_DATA = "BUILDINGS_INPUT_DATA"
    DX = "DX"
    PUMP_PENALTY = "PUMP_PENALTY"
    MAX_CONNECTION_LENGTH = "MAX_CONNECTION_LENGTH"
    CLUSTERING = "CLUSTERING"
    DEFAULT_INHABITANTS_DWELLING = "DEFAULT_INHABITANTS_DWELLING"
    INHABITANTS_DWELLING_ATTRIBUTE_NAME = "INHABITANTS_DWELLING_ATTRIBUTE_NAME"
    DAILY_WASTEWATER_PERSON = "DAILY_WASTEWATER_PERSON"
    PEAK_FACTOR = "PEAK_FACTOR"
    MIN_SLOPE = "MIN_SLOPE"
    TMIN = "TMIN"
    TMAX = "TMAX"
    INFLOW_TRENCH_DEPTH = "INFLOW_TRENCH_DEPTH"
    MIN_TRENCH_DEPTH = "MIN_TRENCH_DEPTH"
    ROUGHNESS = "ROUGHNESS"
    PRESSURIZED_DIAMETER = "PRESSURIZED_DIAMETER"
    DIAMETERS = "DIAMETERS"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    SINKS = "SINKS"
    DIAMETERS_VALUE = ["0.1", "0.15", "0.2", " 0.25", "0.3", "0.4", "0.6", "0.8", "1"]

    def __init__(self):
        super().__init__()

        # One post processor for each output layer to open after the processing
        self.post_processors = [
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
            LoadGpkgStylesPostProcessor(),
        ]

    def createInstance(self):
        return SewerNetworkAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elansewernetwork"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Sewer network")

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
            "This module generates a sewer pipe network based on the input building layer "
            "following the roads and the DEM input. The path is determined by the lowest "
            "altitude points or the points provided in the optional input layer: WWTP."
            "<h2>Restriction:</h2>"
            "The input layers must have the same CRS."
            "<h2>Prerequisites:</h2>"
            "This sewer pipe module uses Pysewer. "
            "It must be installed either locally or through the ELAN plugin settings."
            "<h2>Outputs:</h2>"
            "4 geographic layers are created:\n"
            "<ul>"
            "    <li>WWTP: treatment stations used in the sewer pipe way</li>"
            "    <li>Lifting stations: lifting stations</li>"
            "    <li>Pumping stations: pumping stations</li>"
            "    <li>Sewer pipes: sewer pipe</li>"
            "</ul>"
            "One additional layer without geometry is also created:"
            "<ul>"
            "<li>Network information: statistics such as the total number of buildings, date, etc.</li>"
            "</ul>"
            "The sewer pipe layer includes 6 styles."
            "<h2>Options:</h2>"
            "If the input building layer has a population number field, "
            "it is possible to select it. If no such field exists, "
            "the module uses the parameter 'mean inhabitants per household'."
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SINKS, self.tr("WWTP layer"), [Qgis.ProcessingSourceType.VectorPoint], optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_GPKG, self.tr("Result layers (.gpkg)"), self.tr("Geopackage files (*.gpkg)")
            )
        )

        self.addParameter(QgsProcessingParameterRasterLayer(self.DEM_FILE_PATH, self.tr("DEM layer")))

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
                self.INHABITANTS_DWELLING_ATTRIBUTE_NAME,
                self.tr("Number of inhabitants (field)"),
                parentLayerParameterName=self.BUILDINGS_INPUT_DATA,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(self.PUMP_PENALTY, self.tr("Penalty factor for pumping"), defaultValue=1000)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_CONNECTION_LENGTH, self.tr("Maximum connection lengh [m]"), defaultValue=30
            )
        )

        self.addParameter(
            QgsProcessingParameterString(self.CLUSTERING, self.tr("Source clustering"), defaultValue="None")
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DEFAULT_INHABITANTS_DWELLING,
                self.tr(
                    "Mean inhabitants per household\n"
                    "(used by default if no inhabitant field is selected, "
                    "or if a field error is detected)"
                ),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=3,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DAILY_WASTEWATER_PERSON,
                self.tr("Average daily production of wastewater per person [m3]"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=0.164,  # peak factor for wastewater
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PEAK_FACTOR,
                self.tr("Peak load coefficient"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=2.3,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_SLOPE,
                self.tr("Minimum slope for sewer self-cleaning [m/m]"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=-0.01,  # min slope required for gravitational flow
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TMAX,
                self.tr("Maximum sewer depth [m]"),
                defaultValue=8,  # max trench depth allowed
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TMIN,
                self.tr("Minimum sewer depth [m]"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=0.25,  # min trench depth allowed
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(self.INFLOW_TRENCH_DEPTH, self.tr("Inflow trench depth [m]"), defaultValue=-0)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_TRENCH_DEPTH, self.tr("Lowest possible trench depth [m]"), defaultValue=-0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ROUGHNESS,
                self.tr("Pipe roughness [µm]"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=0.13,  # roughness coefficient
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRESSURIZED_DIAMETER,
                self.tr("Pressurized diameter [m]"),
                Qgis.ProcessingNumberParameterType.Double,
                defaultValue=0.2,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.DIAMETERS,
                self.tr("Gravity diameters [m]"),
                self.DIAMETERS_VALUE,
                allowMultiple=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        # load custom settings from the example settings file
        sinks_source = self.parameterAsSource(parameters, self.SINKS, context)
        output_layer_path = self.parameterAsString(parameters, self.OUTPUT_GPKG, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.DEM_FILE_PATH, context)
        roads_source = self.parameterAsSource(parameters, self.ROADS_INPUT_DATA, context)
        buildings_source = self.parameterAsSource(parameters, self.BUILDINGS_INPUT_DATA, context)
        pump_penalty = self.parameterAsDouble(parameters, self.PUMP_PENALTY, context)
        max_connection_length = self.parameterAsDouble(parameters, self.MAX_CONNECTION_LENGTH, context)
        clustering = self.parameterAsDouble(parameters, self.CLUSTERING, context)
        default_inhabitants_dwelling = int(
            self.parameterAsDouble(parameters, self.DEFAULT_INHABITANTS_DWELLING, context)
        )
        inhabitants_dwelling_attribute_name = self.parameterAsString(
            parameters, self.INHABITANTS_DWELLING_ATTRIBUTE_NAME, context
        )
        daily_wastewater_person = self.parameterAsDouble(parameters, self.DAILY_WASTEWATER_PERSON, context)
        peak_factor = self.parameterAsDouble(parameters, self.PEAK_FACTOR, context)
        min_slope = self.parameterAsDouble(parameters, self.MIN_SLOPE, context)
        tmin = self.parameterAsDouble(parameters, self.TMIN, context)
        tmax = self.parameterAsDouble(parameters, self.TMAX, context)
        inflow_trench_depth = self.parameterAsDouble(parameters, self.INFLOW_TRENCH_DEPTH, context)
        min_trench_depth = self.parameterAsDouble(parameters, self.MIN_TRENCH_DEPTH, context)
        roughness = self.parameterAsDouble(parameters, self.ROUGHNESS, context)
        pressurized_diameter = self.parameterAsDouble(parameters, self.PRESSURIZED_DIAMETER, context)
        diameters_index = self.parameterAsEnums(parameters, self.DIAMETERS, context)

        # Check sources
        if buildings_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.BUILDINGS_INPUT_DATA))
        if roads_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.ROADS_INPUT_DATA))
        if dem_layer is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.DEM_FILE_PATH))
        if (band_count := dem_layer.bandCount()) != 1:
            raise QgsProcessingException(
                self.tr("The DEM must have a single band ({} band(s) found)").format(band_count)
            )

        # Check NULL values in inhabitants_dwelling_attribute_name
        if NULL in buildings_source.uniqueValues(
            buildings_source.fields().indexFromName(inhabitants_dwelling_attribute_name)
        ):
            raise QgsProcessingException(
                self.tr("There is one or more NULL values in the field ") + inhabitants_dwelling_attribute_name
            )

        # Check CRSs
        same_crs = buildings_source.sourceCrs() == roads_source.sourceCrs() == dem_layer.crs()
        if sinks_source is not None:
            same_crs = same_crs and (sinks_source.sourceCrs() == buildings_source.sourceCrs())
        if not same_crs:
            raise QgsProcessingException(self.tr("All input layers must have the same CRS."))

        # Create temporary layers with buildings and roads input features
        if (buildings_layer := buildings_source.materialize(QgsFeatureRequest())) is None:
            raise QgsProcessingException(self.tr("Error when creating buildings layer"))
        if (roads_layer := roads_source.materialize(QgsFeatureRequest())) is None:
            raise QgsProcessingException(self.tr("Error when creating roads layer"))
        roads_layer.setName("roads")
        buildings_layer.setName("buildings")

        # Save input layers to temporary shapefiles because pysewer only accepts shapefile format
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = QgsVectorFileWriter.driverForExtension("shp")

        temp_input_dir = Path(tempfile.mkdtemp())
        roads_layer_source = str(temp_input_dir / "roads.shp")
        QgsVectorFileWriter.writeAsVectorFormatV3(
            roads_layer, roads_layer_source, QgsCoordinateTransformContext(), save_options
        )

        buildings_layer_source = str(temp_input_dir / "buildings.shp")
        QgsVectorFileWriter.writeAsVectorFormatV3(
            buildings_layer, buildings_layer_source, QgsCoordinateTransformContext(), save_options
        )

        # If input DEM is not a tif file, or if it has no data values, save it to a temporary tif file
        # because pysewer only accepts DEM which are a tif file and without no data values
        dem_layer_provider = dem_layer.dataProvider()
        if dem_layer_provider is None:
            raise QgsProcessingException(self.tr("Unexpected error while processing DEM raster layer"))
        if (
            dem_layer_provider.name() != "gdal"
            or ".tif" not in dem_layer.source().lower()
            or dem_layer_provider.sourceHasNoDataValue(1)
        ):
            if feedback is not None:
                feedback.pushInfo(self.tr("DEM pre-processing..."))
            dem_layer_uri = str(temp_input_dir / "dem.tif")
            res = processing.run(
                "native:fillnodata",
                {"INPUT": dem_layer, "BAND": 1, "FILL_VALUE": 0, "OUTPUT": dem_layer_uri},
            )
            if res is None:
                raise QgsProcessingException(self.tr("Error during DEM pre-processing."))
        else:
            dem_layer_uri = dem_layer.source()

        diameters_index = parameters[self.DIAMETERS]
        diameters_value = [float(self.DIAMETERS_VALUE[i]) for i in diameters_index]
        data = {
            "# default settings": None,
            "# preprocessing": None,
            "preprocessing": {
                "dem_file_path": dem_layer_uri,
                "roads_input_data": roads_layer_source,
                "buildings_input_data": buildings_layer_source,
                "dx": dem_layer.rasterUnitsPerPixelX(),
                "pump_penalty": pump_penalty,
                "max_connection_length": max_connection_length,
                "clustering": clustering,
            },
            "optimization": {
                "default_inhabitants_dwelling": default_inhabitants_dwelling,
                "inhabitants_dwelling_attribute_name": inhabitants_dwelling_attribute_name,
                "daily_wastewater_person": daily_wastewater_person,
                "peak_factor": peak_factor,
                "min_slope": min_slope,
                "tmax": tmax,
                "tmin": tmin,
                "inflow_trench_depth": inflow_trench_depth,
                "min_trench_depth": min_trench_depth,
                "diameters": diameters_value,
                "roughness": roughness,
                "pressurized_diameter": pressurized_diameter,
            },
            "export": {
                "file_format": "gpkg",
            },
        }

        tmp_name_file = ""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write(yaml.dump(data))
            tmp_name_file = tmp_file.name

        kwargs = {
            "args": [
                getInterpreterPath(),
                "-W",
                "ignore",
                DIR_PLUGIN_ROOT / "resources" / "pysewer" / "pysewer_launcher.py",
                "--yaml",
                tmp_name_file,
                "--output-path",
                output_layer_path,
                "--external-libs",
                EXTERNAL_LIRBARIES_DIR,
            ],
            "text": True,
            "stderr": subprocess.PIPE,
            "stdout": subprocess.PIPE,
        }
        if sys.platform.startswith("win"):
            si = subprocess.STARTUPINFO()  # type: ignore
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
            kwargs["startupinfo"] = si

        if sinks_source is not None:
            sinks_layer = sinks_source.materialize(QgsFeatureRequest())
            sinks_layer_filepath = str(temp_input_dir / "sinks.shp")
            QgsVectorFileWriter.writeAsVectorFormatV3(
                sinks_layer, sinks_layer_filepath, QgsCoordinateTransformContext(), save_options
            )
            kwargs["args"] += ["--sinks-path", sinks_layer_filepath]

        if feedback is not None:
            feedback.pushInfo(self.tr("Launching pysewer..."))

        pysewer_process = subprocess.Popen(**kwargs)  # pylint:disable=subprocess-run-check
        while (return_code := pysewer_process.poll()) is None:
            time.sleep(0.1)
            if feedback is not None and feedback.isCanceled():
                pysewer_process.terminate()
                pysewer_process.wait()
                raise QgsProcessingException(self.tr("Processing stopped by user"))

        if return_code is not None and return_code != 0:
            if pysewer_process.stderr is not None:
                error_message = pysewer_process.stderr.read()
                if "ModuleNotFoundError" in error_message:
                    raise QgsProcessingException(
                        self.tr("pysewer is not installed, go to ELAN settings to check/install.")
                    )
                else:
                    raise QgsProcessingException(error_message)
            else:
                raise QgsProcessingException(self.tr("Unexpected error while running pysewer"))

        if feedback is not None:
            feedback.pushInfo(self.tr("Post-processing and layer styles creation..."))

        # Create details for loading layers
        # (names, ordering, post-processor for loading styles from gpkg)
        # Layers are ordered in QGIS panel exactly in the order of th elist below
        layers_to_load = {}
        project = QgsProject.instance()
        for i, (layer_name, layer_pretty_name) in enumerate(
            [
                ("sinks_layer", self.tr("WWTP")),
                ("pumping_stations", self.tr("Pumping stations")),
                ("buildings", self.tr("Buildings")),
                ("lifting_stations", self.tr("Lifting stations")),
                ("sewer_pipes", self.tr("Sewer pipes")),
                ("roads", self.tr("Roads")),
                ("info_network", self.tr("Network informations")),
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

        # Save input layers in the output geopackage file
        processing.run(
            "native:package",
            {
                "LAYERS": [roads_layer, buildings_layer],
                "OUTPUT": output_layer_path,
                "OVERWRITE": False,
                "SAVE_STYLES": False,
                "SAVE_METADATA": False,
                "SELECTED_FEATURES_ONLY": False,
                "EXPORT_RELATED_LAYERS": False,
            },
            context=context,
            is_child_algorithm=True,
            feedback=feedback,
        )

        return {self.OUTPUT_GPKG: output_layer_path}

    def saveStyles(self, output_layer_path):
        """
        Save the styles in the GPKG
        """

        # Saving styles in the GeoPackage (gpkg)
        provider_registry = QgsProviderRegistry.instance()
        ogr_provider = None
        if provider_registry is not None:
            ogr_provider = provider_registry.providerMetadata("ogr")
        if ogr_provider is None:
            raise QgsProcessingException(self.tr("Unexpected error while saving styles"))

        styles_dir = getLocalizedStylesDirectory()
        if styles_dir is None:
            raise QgsProcessingException(self.tr("No styles directory found"))

        # Save the following styles directly into the gpkg
        with (styles_dir / "sewer_pipes_diameters.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_pipes",
                style_file.read(),
                "",
                self.tr("Diameters"),
                self.tr("Width based on diameter"),
                "",
                False,
                "",
            ):
                raise Exception(self.tr("Error with diameters style"))

        with (styles_dir / "sewer_pipes_gravity.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_pipes",
                style_file.read(),
                "",
                self.tr("Gravity-driven"),
                self.tr("Color based on slope"),
                "",
                True,  # Default gravitaire style
                "",
            ):
                raise Exception(self.tr("Error with gravity-driven style"))

        with (styles_dir / "sewer_pipes_flow_direction.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_pipes",
                style_file.read(),
                "",
                self.tr("Flow direction"),
                self.tr("Arrow based on trench flow direction"),
                "",
                False,
                "",
            ):
                raise Exception(self.tr("Error with flow direction style"))

        with (styles_dir / "sewer_pipes_depth.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_pipes",
                style_file.read(),
                "",
                self.tr("Depth"),
                self.tr("Color based on trench depth"),
                "",
                False,
                "",
            ):
                raise Exception(self.tr("Error with depth style"))

        with (styles_dir / "pumping_stations.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=pumping_stations",
                style_file.read(),
                "",
                self.tr("Pumping stations"),
                "",
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with pumping stations style"))

        with (styles_dir / "lifting_stations.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=lifting_stations",
                style_file.read(),
                "",
                self.tr("Lifting stations"),
                "",
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with lifting stations style"))

        with (styles_dir / "info_network.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=info_network",
                style_file.read(),
                "",
                self.tr("Network informations"),
                "",
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with network information style"))

        with (styles_dir / "WWTP.qml").open() as style_file:
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sinks_layer",
                style_file.read(),
                "",
                self.tr("WWTP"),
                "",
                "",
                True,
                "",
            ):
                raise Exception(self.tr("Error with WWTP style"))

        # Adapt this style to the data.
        # We don't use QgsVectorLayer.loadNamedStyle to load the QML file because
        # with a GPKG provider, if the style is not found, the default style is loaded
        # so we get the wrong style!
        # To get around this, we load and read the XML Dom Document.
        canas_layer = QgsVectorLayer(output_layer_path + "|layername=sewer_pipes", "", "ogr")
        doc = QDomDocument()
        with (styles_dir / "sewer_pipes_peak_flow.qml").open() as style_file:
            doc.setContent(style_file.read())
        canas_layer.readSymbology(doc.firstChild(), "", QgsReadWriteContext())
        renderer = canas_layer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            raise QgsProcessingException(self.tr("Unexpected error while creating the peak flow style"))
        renderer.updateClasses(canas_layer, 5)
        canas_layer.setRenderer(renderer)
        canas_layer.exportNamedStyle(doc)
        if not ogr_provider.saveStyle(
            output_layer_path + "|layername=sewer_pipes",
            doc.toString(),
            "",
            self.tr("Peak flow"),
            self.tr("Color based on peak flow "),
            "",
            False,
            "",
        ):
            raise Exception(self.tr("Error with peak flow style"))

        try:
            # Create the sub-network styles
            renderer = QgsCategorizedSymbolRenderer("sink_coords")
            symbol = QgsSymbol.defaultSymbol(canas_layer.geometryType())
            assert isinstance(symbol, QgsLineSymbol)
            symbol.setWidth(1)
            renderer.updateSymbols(symbol)
            canas_layer.setRenderer(renderer)
            renderer_widget = QgsCategorizedSymbolRendererWidget(canas_layer, None, renderer)
            renderer_widget.addCategories()
            renderer_to_clone = renderer_widget.renderer()
            assert isinstance(renderer_to_clone, QgsCategorizedSymbolRenderer)
            new_renderer = renderer_to_clone.clone()
            assert isinstance(new_renderer, QgsCategorizedSymbolRenderer)
            nb_category = len(new_renderer.categories()) - 1
            new_renderer.deleteCategory(nb_category)
            for i in range(nb_category):
                new_renderer.updateCategoryLabel(i, str(i + 1))
            canas_layer.setRenderer(new_renderer)
            doc = QDomDocument()
            canas_layer.exportNamedStyle(doc)
            if not ogr_provider.saveStyle(
                output_layer_path + "|layername=sewer_pipes",
                doc.toString(),
                "",
                self.tr("Sub-networks"),
                self.tr("Color based on sub-network"),
                "",
                False,
                "",
            ):
                raise AssertionError()
        except AssertionError:
            raise Exception(self.tr("Error with sub-networks style"))
