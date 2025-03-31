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

from dataclasses import dataclass
from pathlib import Path

from qgis import processing
from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsErrorMessage,
    QgsExpression,
    QgsFeatureRequest,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterVectorLayer,
    QgsProcessingUtils,
    QgsProject,
    QgsRasterBlock,
    QgsRasterFileWriter,
    QgsRasterLayer,
    QgsRasterPipe,
    QgsRectangle,
    QgsUnitTypes,
    QgsVectorLayer,
)

from ELAN.mla_model.MIG_DISCRETIZATION import mla_main_run
from ELAN.utils.tr import Translatable

PYSHEDS_FOUND = True
try:
    from pysheds.grid import Grid
except ImportError:
    PYSHEDS_FOUND = False


@dataclass
class Wastewater:
    wastewater_pattern: str = ""
    ww_time_col_name: str = ""
    ww_flow_col_name: str = ""


@dataclass
class Rain:
    rain_file: str = ""
    rain_time_col_name: str = ""
    rain_intensity_col_name: str = ""


@dataclass
class Observation:
    observations_file: str = ""
    obs_time_col_name: str = ""
    obs_flow_col_name: str = ""
    obs_weir_col_name: str = ""


@dataclass
class Output:
    directory_file: str = ""
    directory_plot: str = ""


@dataclass
class Period:
    starting_date: str = ""  # "2008-06-09 00:00:00"  # Pay close attention to the format: yyyy-mm-dd hh:mm:ss
    ending_date: str = ""  # "2008-06-11 23:59:00"  # Pay close attention to the format: yyyy-mm-dd hh:mm:ss
    time_step: int = 1  # 1  # Time step. It is adviced to use the timestep from the rain record.[min]


class PipeData:
    def __init__(self):
        self.slope = []
        self.lag_surface_runoff = []
        self.decision = []
        self.length = []


class WatershedData:
    def __init__(self):
        self.catchment_surface = []
        self.p_imp_surface = []
        self.hab = []
        self.pop_eq = []
        self.pii = []
        self.frii = []
        self.krii = []
        self.fimp = []
        self.fper = []
        self.initial_losses = []
        self.hinf = []
        self.hsoil = []
        self.pipe_order = []


class HydraulicAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    This processing
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PROJECT_NUMBER = "PROJECT_NUMBER"
    RAIN = "RAIN"
    WASTEWATER = "WASTEWATER"
    OBSERVATION = "OBSERVATION"
    PATH_FILE = "PATH_FILE"
    STARTING_DATE = "STARTING_DATE"
    ENDING_DATE = "ENDING_DATE"
    TIME_STEP = "TIME_STEP"
    TIME_BETWEEN_RAINS_RUNOFF = "TIME_BETWEEN_RAINS_RUNOFF"
    Q_LIM = "Q_LIM"
    THRESHOLD_LAW = "THRESHOLD_LAW"
    WATERSHEDS = "WATERSHEDS"
    PIPES = "PIPES"

    def createInstance(self):
        return HydraulicAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanhydraulic"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Hydraulic")

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
        return self.tr("Hydraulic simulation based on MLA model (INSA)")

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterNumber(self.PROJECT_NUMBER, self.tr("Project number"), minValue=1))

        # Bounding box layer, as a source vector feature
        self.addParameter(QgsProcessingParameterFile(self.RAIN, self.tr("Rain data file [mm/min]"), extension="csv"))

        self.addParameter(
            QgsProcessingParameterFile(
                self.WASTEWATER, self.tr("Daily wastewater pattern file [m3/s]"), extension="csv"
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.OBSERVATION, self.tr("Observed rainfall spills data file [m3/s]"), extension="csv"
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.PATH_FILE, self.tr("Output folder"), Qgis.ProcessingFileParameterBehavior.Folder
            )
        )

        self.addParameter(QgsProcessingParameterDateTime(self.STARTING_DATE, self.tr("Start date")))

        self.addParameter(QgsProcessingParameterDateTime(self.ENDING_DATE, self.tr("End date")))

        self.addParameter(QgsProcessingParameterNumber(self.TIME_STEP, self.tr("Time step between measurements [mn]")))

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TIME_BETWEEN_RAINS_RUNOFF,
                self.tr("Time between two rain periods [s]"),
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.Q_LIM, self.tr("Flow limit before discharge [m3/s]"), Qgis.ProcessingNumberParameterType.Double
            )
        )

        self.addParameter(QgsProcessingParameterString(self.THRESHOLD_LAW, self.tr("Threshold law (equation)")))

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PIPES,
                self.tr("Pipes layer"),
                [Qgis.ProcessingSourceType.VectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.WATERSHEDS,
                self.tr("Urban catchment layer"),
                [Qgis.ProcessingSourceType.VectorPolygon],
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # pylint: disable=unused-argument
        """
        Lancement de la simulation
        """

        projet_id = self.parameterAsInt(parameters, self.PROJECT_NUMBER, context)

        rain = Rain()
        rain.rain_file = self.parameterAsFile(parameters, self.RAIN, context)
        rain.rain_time_col_name = "Date TU"
        rain.rain_intensity_col_name = "mm/min"

        wastewater = Wastewater()
        wastewater.wastewater_pattern = self.parameterAsFile(parameters, self.WASTEWATER, context)
        wastewater.ww_time_col_name = "Heure"
        wastewater.ww_flow_col_name = "Debit (m3/s) autosurveillance"

        observation = Observation()
        observation.observations_file = self.parameterAsFile(parameters, self.OBSERVATION, context)
        observation.obs_time_col_name = "Date"
        observation.obs_flow_col_name = "Debit [m3/s]"
        observation.obs_weir_col_name = "Debit dev [m3/s]"

        period = Period()
        period.starting_date = self.parameterAsDateTime(parameters, self.STARTING_DATE, context).toString(
            "yyyy-MM-dd hh:mm:00"
        )
        period.ending_date = self.parameterAsDateTime(parameters, self.ENDING_DATE, context).toString(
            "yyyy-MM-dd hh:mm:00"
        )
        period.time_step = self.parameterAsEnum(parameters, self.TIME_STEP, context)

        path_file = self.parameterAsFile(parameters, self.PATH_FILE, context)
        q_lilm = self.parameterAsDouble(parameters, self.Q_LIM, context)
        threshold_law = self.parameterAsString(parameters, self.THRESHOLD_LAW, context)
        time_between_rains_runoff = self.parameterAsEnum(parameters, self.TIME_BETWEEN_RAINS_RUNOFF, context)

        # Watershed features, sorted by number
        watersheds_layer = self.parameterAsVectorLayer(parameters, self.WATERSHEDS, context)
        if watersheds_layer is None:
            raise QgsProcessingException(self.tr("Error while loading watersheds layer"))
        watersheds = list(watersheds_layer.getFeatures(QgsFeatureRequest(QgsExpression(f'"projet_id" = {projet_id}'))))
        if len(watersheds) == 0:
            raise QgsProcessingException(self.tr("No watershed with a project_id = {}").format(projet_id))
        watersheds.sort(key=lambda ws: ws["numero"])

        # tool to compute area
        project = QgsProject.instance()
        if project is None:
            raise QgsProcessingException(self.tr("No QGIS project instance found"))
        measurement = QgsDistanceArea()
        measurement.setSourceCrs(project.crs(), project.transformContext())
        measurement.setEllipsoid(project.ellipsoid())
        to_hectares = QgsUnitTypes.fromUnitToUnitFactor(measurement.areaUnits(), Qgis.AreaUnit.Hectares)
        to_meters = QgsUnitTypes.fromUnitToUnitFactor(measurement.lengthUnits(), Qgis.DistanceUnit.Meters)

        # Fill data from watershed features
        ws_data = WatershedData()
        for watershed in watersheds:
            ws_data.catchment_surface.append(round(measurement.measureArea(watershed.geometry()) * to_hectares))
            ws_data.p_imp_surface.append(watershed["pourcentage_impermeable"])
            ws_data.hab.append(watershed["nb_habitant"])
            ws_data.pop_eq.append(watershed["equivalent_population"])
            ws_data.pii.append(watershed["groundwater_infiltration_baseflow"])
            ws_data.frii.append(watershed["rain_induced_infiltration_factor"])
            ws_data.krii.append(watershed["lag_soil_infiltration_reservoir"])
            ws_data.fimp.append(watershed["imper_surf_runoff_factor"])
            ws_data.fper.append(watershed["per_surf_runoff_factor"])
            ws_data.initial_losses.append(watershed["initial_losses"])
            ws_data.hinf.append(watershed["h_inf"])
            ws_data.hsoil.append(watershed["h_soil"])
            ws_data.pipe_order.append([int(nb.strip()) for nb in watershed["pipe_order"].split(",")])

        # Fill data from pipe features
        pipe_data = PipeData()
        pipes_layer = self.parameterAsVectorLayer(parameters, self.PIPES, context)
        if pipes_layer is None:
            raise QgsProcessingException(self.tr("Error while loading pipes layer"))
        pipes = list(pipes_layer.getFeatures(QgsFeatureRequest(QgsExpression(f'"projet_id" = {projet_id}'))))
        if len(pipes) == 0:
            raise QgsProcessingException(f"Il n'y a pas de canalisation avec un projet_id à {projet_id}")
        for pipe in pipes:
            pipe_data.length.append(round(measurement.measureLength(pipe.geometry()) * to_meters))
            pipe_data.slope.append(pipe["slope"])
            pipe_data.lag_surface_runoff.append(pipe["lag_surface_runoff"])
            pipe_data.decision.append("no" if pipe_data.lag_surface_runoff is None else "yes")

        produced_volumes = mla_main_run(
            rain,
            wastewater,
            observation,
            path_file,
            q_lilm,
            threshold_law,
            period,
            time_between_rains_runoff,
            ws_data,
            pipe_data,
        )

        # On enregistre les volumes produits dans le layer
        watersheds_layer.startEditing()
        for watershed in watersheds:
            try:
                watershed["volume_produit"] = int(produced_volumes[watershed["numero"]])
            except KeyError:
                raise QgsProcessingException(
                    self.tr("No produced volume number {} in produced_volumes={}").format(
                        watershed["numero"], produced_volumes
                    )
                )
            watersheds_layer.updateFeature(watershed)

        return {
            "volumes": produced_volumes,
            "saved_in_layer": "YES" if watersheds_layer.commitChanges() else "NO",
        }


class HydraulicUrbanCatchmentAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    This processing computes urban watersheds
    """

    BUFFER_DISTANCE = "BUFFER_DISTANCE"
    INPUT_LINES = "INPUT_LINES"
    INPUT_DEM = "INPUT_DEM"
    INPUT_ZONE = "INPUT_ZONE"
    OUTPUT_POINTS = "OUTPUT_POINTS"
    OUTPUT_UWS = "OUTPUT_UWS"

    def createInstance(self):
        return HydraulicUrbanCatchmentAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanhydraulicurbancatchment"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Urban catchment")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Data preparation")

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
            "The processing extracts the DEM and the sewer pipes from the calculation area and "
            "computes the sum of urban watersheds concerned by the pipes."
        )

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Inputs
        self.addParameter(QgsProcessingParameterNumber(self.BUFFER_DISTANCE, self.tr("Erosion expansion distance")))
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINES, self.tr("Pipes network"), [Qgis.ProcessingSourceType.VectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ZONE, self.tr("Calculation area"), [Qgis.ProcessingSourceType.VectorPolygon]
            )
        )
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr("DEM")))

        # Outputs
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_UWS, self.tr("Urban catchment")))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_POINTS, self.tr("Sampled points")))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Process
        """

        if not PYSHEDS_FOUND:
            raise QgsProcessingException(self.tr("pysheds is not installed"))

        buffer_distance = self.parameterAsInt(parameters, self.BUFFER_DISTANCE, context)
        input_lines = self.parameterAsVectorLayer(parameters, self.INPUT_LINES, context)
        input_dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        input_zone = self.parameterAsSource(parameters, self.INPUT_ZONE, context)
        output_points = self.parameterAsOutputLayer(parameters, self.OUTPUT_POINTS, context)
        output_uws = self.parameterAsOutputLayer(parameters, self.OUTPUT_UWS, context)

        if input_lines is None:
            raise QgsProcessingException(self.tr("Error while loading pipes network layer"))

        if input_dem is None:
            raise QgsProcessingException(self.tr("Error while loading DEM layer"))

        if input_zone is None:
            raise QgsProcessingException(self.tr("Error while loading calculation area layer"))

        # uws stands for urban watersheds
        output_raster = QgsProcessingUtils.generateTempFilename("uws." + QgsProcessingUtils.defaultRasterExtension())
        target_crs = input_dem.crs()

        # If DEM is not from file, export into a file corresponding to the input_zone bounding box
        # TODO: test with QGIS 3.32
        if input_dem.providerType() != "gdal":
            clipped_dem = QgsProcessingUtils.generateTempFilename(
                "clipped_dem." + QgsProcessingUtils.defaultRasterExtension()
            )
            writer = QgsRasterFileWriter(clipped_dem)
            pipe = QgsRasterPipe()
            provider = input_dem.dataProvider()
            if provider is None:
                raise QgsProcessingException(self.tr("Error with DEM provider"))
            pipe.set(provider.clone())
            extent = input_zone.sourceExtent()
            if (input_zone_crs := input_zone.sourceCrs()) != target_crs:
                extent = QgsCoordinateTransform(input_zone_crs, target_crs, QgsProject.instance()).transform(extent)
            x_resolution = input_dem.rasterUnitsPerPixelX()
            y_resolution = input_dem.rasterUnitsPerPixelY()
            writer.writeRaster(
                pipe,
                int(extent.width() / x_resolution),
                int(extent.height() / y_resolution),
                extent,
                input_dem.crs(),
            )
            input_dem = QgsRasterLayer(clipped_dem, "clipped_dem", "gdal")
            if not input_dem.isValid():
                raise QgsProcessingException(self.tr("DEM file export failed"))

        # Clip input lines to compute zone
        res = processing.run(
            "native:extractbylocation",
            {
                "INPUT": input_lines,
                "PREDICATE": [6],
                "INTERSECT": parameters[self.INPUT_ZONE],
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        if res is None:
            raise QgsProcessingException(self.tr("Error while processing"))
        input_lines = res["OUTPUT"]

        if target_crs != input_lines.crs():
            if feedback is not None:
                feedback.pushInfo(self.tr("Reprojecting sewer pipe layer"))
            res = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": input_lines,
                    "TARGET_CRS": target_crs,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )
            if res is None:
                raise QgsProcessingException(self.tr("Error while processing"))
            input_lines = res["OUTPUT"]

        # Sampling of lines respecting Shannon frequency
        sample_distance = round(min(input_dem.rasterUnitsPerPixelX() / 2.1, input_dem.rasterUnitsPerPixelY() / 2.1))
        if feedback is not None:
            feedback.pushInfo(self.tr("Sampling sewer pipe every {} meters").format(sample_distance))
        res = processing.run(
            "native:pointsalonglines",
            {
                "INPUT": input_lines,
                "DISTANCE": sample_distance,
                "START_OFFSET": 0,
                "END_OFFSET": 0,
                "OUTPUT": output_points,
            },
        )
        if res is None:
            raise QgsProcessingException(self.tr("Error while processing"))
        output_points_path = res["OUTPUT"]

        # Clip DEM to compute zone
        if feedback is not None:
            feedback.pushInfo(self.tr("DEM clipping on the calculation area"))
        res = processing.run(
            "gdal:cliprasterbymasklayer",
            {
                "INPUT": input_dem,
                "MASK": parameters[self.INPUT_ZONE],
                "KEEP_RESOLUTION": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        if res is None:
            raise QgsProcessingException(self.tr("Error while processing"))
        masked_dem = res["OUTPUT"]
        if not Path(masked_dem).exists():
            raise QgsProcessingException(self.tr("Error during DEM clipping"))

        # detect and resolve depressions (multi celled depressions), pits, and flats
        if feedback is not None:
            feedback.pushInfo(self.tr("DEM preprocessing"))
        grid = Grid.from_raster(masked_dem)  # instantiate a grid from a raster file
        dem = grid.read_raster(masked_dem)  # read raster gridded data
        grid.detect_pits(dem)
        pit_filled_dem = grid.fill_pits(dem)  # fill pits in DEM
        grid.detect_depressions(pit_filled_dem)
        flooded_dem = grid.fill_depressions(pit_filled_dem)  # fill depressions in DEM
        grid.detect_flats(flooded_dem)
        inflated_dem = grid.resolve_flats(flooded_dem)  # remove flats from DEM

        # North : 64, Northeast : 128, East : 1, Southeast : 2, South : 4, Southwest : 8, West : 16, Northwest : 32
        dirmap = (64, 128, 1, 2, 4, 8, 16, 32)  # specify directional mapping

        if feedback is not None:
            feedback.pushInfo(self.tr("Watershed calculation for each sampled point"))
        grid = Grid.from_raster(masked_dem)  # instantiate a grid from a raster file
        fdir = grid.flowdir(inflated_dem, dirmap=dirmap)
        points_layer = QgsVectorLayer(output_points_path, "output_points", "ogr")
        count = points_layer.featureCount()
        catch = None
        for i, feature in enumerate(points_layer.getFeatures()):
            if feedback is not None:
                if feedback.isCanceled():
                    feedback.pushWarning(self.tr("Process stopped by user"))
                    return {}
                feedback.setProgress(i / count * 90)
            geom = feature.geometry().asPoint()
            catch_for_point = grid.catchment(x=geom.x(), y=geom.y(), fdir=fdir, dirmap=dirmap, xytype="coordinate")
            catch = catch_for_point if i == 0 else catch + catch_for_point

        # build new raster extent based on number of columns and cellsize
        if catch is None:
            raise QgsProcessingException(self.tr("No catchment found"))

        grid.clip_to(catch)  # clip exactly on detected catchments
        catch = grid.view(catch)
        xmin, xmax, ymin, ymax = catch.extent
        rows, cols = catch.shape
        writer = QgsRasterFileWriter(output_raster)
        writer.setOutputProviderKey("gdal")
        writer.setOutputFormat(QgsRasterFileWriter.driverForExtension(QgsProcessingUtils.defaultRasterExtension()))
        provider = writer.createOneBandRaster(
            Qgis.DataType.Byte, cols, rows, QgsRectangle(xmin, ymin, xmax, ymax), target_crs
        )
        if not provider:
            raise QgsProcessingException(self.tr("Raster creation failed for file {}").format(output_raster))
        if not provider.isValid():
            raise QgsProcessingException(
                self.tr("Raster creation error for raster {}: {}").format(
                    output_raster, provider.error().message(QgsErrorMessage.Format.Text)
                )
            )

        block = QgsRasterBlock(Qgis.DataType.Byte, cols, rows)
        block.setData(catch.tobytes())
        provider.writeBlock(block, 1, 0, 0)
        provider.setEditable(False)

        if feedback is not None:
            feedback.pushInfo(self.tr("Converting raster to vector"))
        res = processing.run(
            "native:pixelstopolygons",
            {
                "INPUT_RASTER": output_raster,
                "RASTER_BAND": 1,
                "FIELD_NAME": "VALUE",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        if res is None:
            raise QgsProcessingException(self.tr("Error while processing"))
        res1 = res["OUTPUT"]
        res = processing.run(
            "native:extractbyattribute",
            {
                "INPUT": res1,
                "FIELD": "VALUE",
                "OPERATOR": 0,
                "VALUE": "1",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        if res is None:
            raise QgsProcessingException(self.tr("Error while processing"))
        res2 = res["OUTPUT"]
        if buffer_distance != 0:
            if feedback is not None:
                feedback.setProgress(92)
            # mini buffer to merge all pixels
            res = processing.run(
                "native:buffer",
                {
                    "INPUT": res2,
                    "DISTANCE": 0.000001,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "DISSOLVE": True,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )
            if res is None:
                raise QgsProcessingException(self.tr("Error while processing"))
            res3 = res["OUTPUT"]
            if feedback is not None:
                feedback.setProgress(94)
                feedback.pushInfo(self.tr("Erosion/expansion"))
            res = processing.run(
                "native:buffer",
                {
                    "INPUT": res3,
                    "DISTANCE": buffer_distance,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )
            if res is None:
                raise QgsProcessingException(self.tr("Error while processing"))
            res4 = res["OUTPUT"]
            if feedback is not None:
                feedback.setProgress(96)
            res = processing.run(
                "native:buffer",
                {
                    "INPUT": res4,
                    "DISTANCE": -2 * buffer_distance,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )
            if res is None:
                raise QgsProcessingException(self.tr("Error while processing"))
            res5 = res["OUTPUT"]
            if feedback is not None:
                feedback.setProgress(98)
            processing.run(
                "native:buffer",
                {
                    "INPUT": res5,
                    "DISTANCE": buffer_distance,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "OUTPUT": output_uws,
                },
            )
        else:
            if feedback is not None:
                feedback.setProgress(95)
            # mini buffer to merge all pixels
            processing.run(
                "native:buffer",
                {
                    "INPUT": res2,
                    "DISTANCE": 0.000001,
                    "SEGMENTS": 5,
                    "END_CAP_STYLE": 0,
                    "JOIN_STYLE": 0,
                    "MITER_LIMIT": 2,
                    "DISSOLVE": True,
                    "OUTPUT": output_uws,
                },
            )

        if feedback is not None:
            feedback.setProgress(100)
        return {self.OUTPUT_POINTS: output_points, self.OUTPUT_UWS: output_uws}
