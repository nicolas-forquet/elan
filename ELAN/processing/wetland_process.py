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

# pylint: disable=invalid-name

import json
import multiprocessing
import site
import sys
from importlib import util as importutil
from pathlib import Path
from typing import Optional

from qgis.core import (
    NULL,
    Qgis,
    QgsConditionalStyle,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsDistanceArea,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QColor

from ELAN.__about__ import DIR_PLUGIN_ROOT
from ELAN.processing.utils import getLocalizedStylesDirectory
from ELAN.utils.tr import Translatable

# Hard-coded concentrations values arriving at the WWTP in g/m3
TSS_IN = 288
BOD5_IN = 265
TKN_IN = 67
COD_IN = 646
NO3_IN = 3


class WetlandProcessAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    Algorithm using wetlandoptimizer
    """

    TSS_OBJ = "TSS_OBJ"
    BOD5_OBJ = "BOD5_OBJ"
    TKN_OBJ = "TKN_OBJ"
    COD_OBJ = "COD_OBJ"
    NO3_OBJ = "NO3_OBJ"
    TN_OBJ = "TN_OBJ"
    SINKS = "SINKS"
    TREATMENT = "TREATMENT"
    Q_FIELD = "Q_FIELD"
    SINK_COORDS = "SINK_COORDS"
    STAGES_MAX = "STAGES_MAX"
    AVAILABLE_SURFACE = "AVAILABLE_SURFACE"
    CLIMATE = "CLIMATE"

    def __init__(self):
        super().__init__()
        self.post_processor = WetlandProcessPostProcessor()
        self.climates = [
            (self.tr("Temperate"), "Temperate"),
            (self.tr("Tropical"), "Tropical"),
        ]

    def createInstance(self):
        return WetlandProcessAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanwetlandprocess"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Processes")

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
            "Sizing of treatment systems according to user defined discharge levels."
            "\n"
            """
            <u>Glossary :</u>
            [TSS] : TSS outflow concentration target [g/m3]
            [BOD5] : BOD5 outflow concentration target [g/m3]
            [TKN] :TKN outflow concentration target [g/m3]
            [COD] : COD outflow concentration target [g/m3]
            """
            "\n"
            "The input concentrations used are:"
            "<ul>"
            "<li>TSS: {} g/m3</li>"
            "<li>BOD5: {} g/m3</li>"
            "<li>TKN: {} g/m3</li>"
            "<li>COD: {} g/m3</li>"
            "<li>NO3: {} g/m3</li>"
            "</ul>"
            "\n"
            "The available surface layer is optional. If present, each input WWTP feature "
            "will be matched only once with a corresponding surface.\n"
            "One surface will be affected to only one WWTP (if 2 WWTP are "
            "within the same surface, only one station will be matched with the surface).\n"
            "The surface layer will be reprojected to the WWTP CRS.\n"
            "The available area influences the formatting of the attribute table, compared "
            "with the treatment system total needed surface. "
        ).format(TSS_IN, BOD5_IN, TKN_IN, COD_IN, NO3_IN)

    def initAlgorithm(self, configuration=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterEnum(
                self.CLIMATE,
                self.tr("Climate"),
                [climate[0] for climate in self.climates],
                defaultValue=self.climates[0][0],
                allowMultiple=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.TREATMENT, self.tr("Treatment trains layer"), Qgis.ProcessingSourceType.VectorPoint
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SINKS, self.tr("WWTP layer"), [Qgis.ProcessingSourceType.VectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.AVAILABLE_SURFACE,
                self.tr("Available area"),
                [Qgis.ProcessingSourceType.VectorPolygon],
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.SINK_COORDS,
                self.tr("Sink coordinates"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.String,
                defaultValue="sink_coords",
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.STAGES_MAX,
                self.tr("Maximum stages number"),
                Qgis.ProcessingNumberParameterType.Integer,
                defaultValue=3,
                optional=False,
                minValue=0,
                maxValue=4,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.TSS_OBJ,
                self.tr("TSS outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="TSS_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.BOD5_OBJ,
                self.tr("BOD5 outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="BOD5_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TKN_OBJ,
                self.tr("TKN outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="TKN_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.COD_OBJ,
                self.tr("COD outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="COD_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.NO3_OBJ,
                self.tr("NO3 outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="NO3_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TN_OBJ,
                self.tr("TN outflow concentration target [g/m3]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="TN_obj",
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.Q_FIELD,
                self.tr("Daily inflow [m3/d]"),
                parentLayerParameterName=self.SINKS,
                type=Qgis.ProcessingFieldParameterDataType.Numeric,
                defaultValue="average_daily_flow",
            )
        )

    def pushInfo(self, feedback: Optional[QgsProcessingFeedback], *args):
        if feedback is not None:
            feedback.pushInfo(" ".join([str(msg) for msg in args]))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Add external_dependencies directory if not already in site directory
        external_dependencies_dir = DIR_PLUGIN_ROOT / "external_dependencies"
        if str(external_dependencies_dir) not in sys.path:
            site.addsitedir(str(external_dependencies_dir))

        if (wetlandoptimizer_spec := importutil.find_spec("wetlandoptimizer")) is None:
            raise QgsProcessingException(
                self.tr("The wetlandoptimizer library is not installed.\nGo to ELAN settings to install it.")
            )
        from wetlandoptimizer.main import COD_Fractionation

        if wetlandoptimizer_spec.origin is None:
            raise QgsProcessingException("Error with wetlandoptimizer installation")

        sinks_source = self.parameterAsSource(parameters, self.SINKS, context)
        if sinks_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.SINKS))
        sinks_source_crs = sinks_source.sourceCrs()

        surface_source = self.parameterAsSource(parameters, self.AVAILABLE_SURFACE, context)
        crs_transform = None
        area_measurement = None
        if surface_source is not None:
            crs_transform = QgsCoordinateTransform(
                surface_source.sourceCrs(), sinks_source_crs, QgsCoordinateTransformContext()
            )
            area_measurement = QgsDistanceArea()
            area_measurement.setSourceCrs(sinks_source_crs, QgsCoordinateTransformContext())
            area_measurement.setEllipsoid(sinks_source_crs.ellipsoidAcronym())

        treatment_sink, treatment_dest = self.parameterAsSink(
            parameters, self.TREATMENT, context, outputFields(), Qgis.WkbType.Point, sinks_source_crs
        )
        if treatment_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.TREATMENT))

        TSS_obj_field_name = self.parameterAsString(parameters, self.TSS_OBJ, context)
        BOD5_obj_field_name = self.parameterAsString(parameters, self.BOD5_OBJ, context)
        TKN_obj_field_name = self.parameterAsString(parameters, self.TKN_OBJ, context)
        COD_obj_field_name = self.parameterAsString(parameters, self.COD_OBJ, context)
        NO3_obj_field_name = self.parameterAsString(parameters, self.NO3_OBJ, context)
        TN_obj_field_name = self.parameterAsString(parameters, self.TN_OBJ, context)
        Q_obj_field_name = self.parameterAsString(parameters, self.Q_FIELD, context)
        sink_coords_field_name = self.parameterAsString(parameters, self.SINK_COORDS, context)
        stages_max = self.parameterAsInt(parameters, self.STAGES_MAX, context)
        climate = self.climates[self.parameterAsInt(parameters, self.CLIMATE, context)][1]

        # Hard coded (see the constants at the top of the module)
        Cin = COD_Fractionation([TSS_IN, BOD5_IN, TKN_IN, COD_IN, NO3_IN])

        # Loop on WWTP and run wetlandoptimizer on each one
        assigned_surfaces_ids = []
        optimizations_parameters = []
        wwtp_features = list(sinks_source.getFeatures())
        for wwtp_feature in wwtp_features:

            # Find corresponding available surface
            available_surface = 0
            if surface_source is not None and crs_transform is not None and area_measurement is not None:
                for surface_feature in surface_source.getFeatures():
                    if surface_feature.id() in assigned_surfaces_ids:
                        continue
                    surface_geom = surface_feature.geometry()
                    # Reproject surface geometry to the sink CRS
                    surface_geom.transform(crs_transform)
                    if wwtp_feature.geometry().within(surface_geom):
                        available_surface = round(area_measurement.measureArea(surface_geom))
                        assigned_surfaces_ids.append(surface_feature.id())
                        break

            # Get objectives
            obj_none = []
            TSS_obj = wwtp_feature[TSS_obj_field_name]
            if TSS_obj == NULL:
                obj_none.append(self.tr("TSS"))
            BOD5_obj = wwtp_feature[BOD5_obj_field_name]
            if BOD5_obj == NULL:
                obj_none.append(self.tr("BOD5"))
            COD_obj = wwtp_feature[COD_obj_field_name]
            if COD_obj == NULL:
                obj_none.append(self.tr("COD"))
            if len(obj_none) > 0:
                raise QgsProcessingException(self.tr("These values can't be NULL:") + " " + ", ".join(obj_none))
            TKN_obj = wwtp_feature[TKN_obj_field_name]
            NO3_obj = wwtp_feature[NO3_obj_field_name]
            TN_obj = wwtp_feature[TN_obj_field_name]
            Q = wwtp_feature[Q_obj_field_name]
            Cobj = [TSS_obj, BOD5_obj, TKN_obj, COD_obj, NO3_obj, TN_obj]
            Cobj = [None if param == NULL else param for param in Cobj]

            optimizations_parameters.append(
                OptimizationParameters(Cin, Cobj, Q, stages_max, climate, available_surface)
            )

        # Set multiprocess path on Windows
        python_path = None
        if sys.platform.startswith("win"):
            try:
                python_path = Path(sys.exec_prefix).absolute() / "pythonw.exe"
                if python_path.is_file():
                    multiprocessing.set_executable(str(python_path))
                else:
                    python_path = Path(sys.exec_prefix).absolute().parent.parent / "bin" / "pythonw.exe"
                    if python_path.is_file():
                        multiprocessing.set_executable(str(python_path))
                    else:
                        raise QgsProcessingException(self.tr("Python not found for multiprocessing"))
            except Exception as err:
                raise QgsProcessingException(
                    self.tr("Unexpected error to set python path for multiprocessing:") + "\n" + str(err)
                )

        # Launch optimizations on every WWTP in parallel
        with multiprocessing.Pool() as pool:
            optimizations_results = pool.map(run_optimization, optimizations_parameters)

        # Loop each result and add features
        for optimization_result, wwtp_feature in zip(optimizations_results, wwtp_features):
            for pathway_result in optimization_result.pathway_results:
                output_feature = QgsFeature()
                output_feature.setFields(outputFields())
                output_feature.setGeometry(wwtp_feature.geometry())
                output_feature["name_stages"] = "-".join(pathway_result.name_stages)
                output_feature["pathway_id"] = pathway_result.id
                output_feature["available_surface"] = optimization_result.available_surface
                output_feature["sink_coords"] = wwtp_feature[sink_coords_field_name]
                output_feature["total_volume"] = pathway_result.total_volume
                output_feature["total_surface"] = pathway_result.total_surface
                output_feature["depth_stages_unsat"] = json.dumps(pathway_result.unsaturated_depth_stages)
                output_feature["depth_stages_sat"] = json.dumps(pathway_result.saturated_depth_stages)
                output_feature["surface_stages"] = json.dumps(pathway_result.surface_stages)
                output_feature["TSS_loading_stages"] = json.dumps(pathway_result.TSS_loading_stages)
                output_feature["BOD5_loading_stages"] = json.dumps(pathway_result.BOD5_loading_stages)
                output_feature["TKN_loading_stages"] = json.dumps(pathway_result.TKN_loading_stages)
                output_feature["COD_loading_stages"] = json.dumps(pathway_result.COD_loading_stages)
                output_feature["hydraulic_loading_rate_stages"] = json.dumps(
                    pathway_result.hydraulic_loading_rate_stages
                )
                output_feature["TSS_concentration"] = pathway_result.TSS_concentration
                output_feature["BOD5_concentration"] = pathway_result.BOD5_concentration
                output_feature["TKN_concentration"] = pathway_result.TKN_concentration
                output_feature["COD_concentration"] = pathway_result.COD_concentration
                output_feature["NO3_concentration"] = pathway_result.NO3_concentration
                output_feature["TN_concentration"] = pathway_result.TN_concentration
                output_feature["TSS_deviation"] = pathway_result.TSS_deviation
                output_feature["BOD5_deviation"] = pathway_result.BOD5_deviation
                output_feature["TKN_deviation"] = pathway_result.TKN_deviation
                output_feature["COD_deviation"] = pathway_result.COD_deviation
                output_feature["NO3_deviation"] = pathway_result.NO3_deviation
                output_feature["TN_deviation"] = pathway_result.TN_deviation
                treatment_sink.addFeature(output_feature)

        context.layerToLoadOnCompletionDetails(treatment_dest).setPostProcessor(self.post_processor)
        return {"OUTPUT": treatment_dest}


def outputFields() -> QgsFields:
    output_fields = QgsFields()

    # String field containing the sink coordinate
    output_fields.append(QgsField("sink_coords", QMetaType.Type.QString))

    # Pathway identifier
    output_fields.append(QgsField("pathway_id", QMetaType.Type.QString))

    # String field containing the names and materials of the stages
    output_fields.append(QgsField("name_stages", QMetaType.Type.QString))

    # String fields containing JSON list with size values for each stage
    output_fields.append(QgsField("surface_stages", QMetaType.Type.QString))
    output_fields.append(QgsField("depth_stages_sat", QMetaType.Type.QString))
    output_fields.append(QgsField("depth_stages_unsat", QMetaType.Type.QString))

    # String fields containing JSON list with loading values for each stage
    output_fields.append(QgsField("TSS_loading_stages", QMetaType.Type.QString))
    output_fields.append(QgsField("BOD5_loading_stages", QMetaType.Type.QString))
    output_fields.append(QgsField("TKN_loading_stages", QMetaType.Type.QString))
    output_fields.append(QgsField("COD_loading_stages", QMetaType.Type.QString))
    output_fields.append(QgsField("hydraulic_loading_rate_stages", QMetaType.Type.QString))

    output_fields.append(QgsField("available_surface", QMetaType.Type.Double))
    output_fields.append(QgsField("total_surface", QMetaType.Type.Double))
    output_fields.append(QgsField("total_volume", QMetaType.Type.Double))
    output_fields.append(QgsField("TSS_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("BOD5_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("TKN_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("COD_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("NO3_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("TN_concentration", QMetaType.Type.Double))
    output_fields.append(QgsField("TSS_deviation", QMetaType.Type.Double))
    output_fields.append(QgsField("BOD5_deviation", QMetaType.Type.Double))
    output_fields.append(QgsField("TKN_deviation", QMetaType.Type.Double))
    output_fields.append(QgsField("COD_deviation", QMetaType.Type.Double))
    output_fields.append(QgsField("NO3_deviation", QMetaType.Type.Double))
    output_fields.append(QgsField("TN_deviation", QMetaType.Type.Double))
    return output_fields


class WetlandProcessPostProcessor(QgsProcessingLayerPostProcessorInterface, Translatable):
    def postProcessLayer(self, layer, context, feedback):  # pylint: disable=unused-argument
        """
        Set the layer style
        """

        if not isinstance(layer, QgsVectorLayer) or (conditional_styles := layer.conditionalStyles()) is None:
            return

        # Set style from qml file
        styles_dir = getLocalizedStylesDirectory()
        if styles_dir is None:
            if feedback is not None:
                feedback.pushWarning(self.tr("No layer styles found"))
            return

        if layer is None or not layer.isValid():
            return
        layer.loadNamedStyle(str(styles_dir / "wetland_processes.qml"))

        # Conditional styling for attribute table and deviation fields

        ok_style = QgsConditionalStyle()
        ok_style.setRule("@value <= 0")
        ok_style.setName("OK")
        ok_style.setBackgroundColor(QColor(154, 216, 113, 255))

        nok_style = QgsConditionalStyle()
        nok_style.setRule("@value > 0")
        ok_style.setName("NOK")
        nok_style.setBackgroundColor(QColor(251, 50, 50, 255))
        nok_style.setTextColor(QColor(255, 255, 255, 255))

        for field_name in [f.name() for f in layer.fields() if f.name().endswith("_deviation")]:
            conditional_styles.setFieldStyles(field_name, [ok_style, nok_style])

        # Conditional styling for attribute table and surface fields

        ok_style = QgsConditionalStyle()
        ok_style.setRule('@value <= "available_surface" and "available_surface" > 0')
        ok_style.setName("OK")
        ok_style.setBackgroundColor(QColor(154, 216, 113, 255))

        nok_style = QgsConditionalStyle()
        nok_style.setRule('@value > "available_surface" and "available_surface" > 0')
        ok_style.setName("NOK")
        nok_style.setBackgroundColor(QColor(251, 50, 50, 255))
        nok_style.setTextColor(QColor(255, 255, 255, 255))

        conditional_styles.setFieldStyles("total_surface", [ok_style, nok_style])


class OptimizationParameters:
    def __init__(self, Cin, Cobj, Q, stages_max, climate, available_surface):
        self.available_surface = available_surface
        self.Cin = Cin
        self.Cobj = Cobj
        self.Q = Q
        self.climate = climate
        self.stages_max = stages_max
        self.pathway_results = []


def run_optimization(optimization_parameters: OptimizationParameters):
    """
    Independant optimization call to wetlandoptimizer library
    """
    from wetlandoptimizer.main import Results_Global_Generation

    optimization_parameters.pathway_results = Results_Global_Generation(
        optimization_parameters.Cin,
        optimization_parameters.Cobj,
        optimization_parameters.Q,
        optimization_parameters.stages_max,
        files_max=1,
        climate=optimization_parameters.climate,
    )
    return optimization_parameters
