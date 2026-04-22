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

# pylint: disable=invalid-name,too-many-arguments,too-many-positional-arguments

import json
import multiprocessing
import sys
from math import ceil
from pathlib import Path
from typing import Any, Optional

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
    QgsMapLayer,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeatureSource,
    QgsProcessingFeedback,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType, QVariant
from qgis.PyQt.QtGui import QColor

from ELAN.processing.utils import getLocalizedStylesDirectory
from ELAN.utils.dependencies_utils import wetlandoptimizerInstalled
from ELAN.utils.tr import Translatable


class WetlandProcessAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    Algorithm using wetlandoptimizer
    """

    TSS_IN = "TSS_IN"
    BOD5_IN = "BOD5_IN"
    TKN_IN = "TKN_IN"
    COD_IN = "COD_IN"
    NO3N_IN = "NO3N_IN"
    TP_IN = "TP_IN"
    ECOLI_IN = "ECOLI_IN"
    TSS_OBJ = "TSS_OBJ"
    BOD5_OBJ = "BOD5_OBJ"
    TKN_OBJ = "TKN_OBJ"
    COD_OBJ = "COD_OBJ"
    NO3N_OBJ = "NO3N_OBJ"
    TN_OBJ = "TN_OBJ"
    TP_OBJ = "TP_OBJ"
    ECOLI_OBJ = "ECOLI_OBJ"
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
        """Return an instance of this class"""
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
            "The available surface layer is optional. If present, each input WWTP feature "
            "will be matched only once with a corresponding surface.\n"
            "One surface will be affected to only one WWTP (if 2 WWTP are "
            "within the same surface, only one station will be matched with the surface).\n"
            "The surface layer will be reprojected to the WWTP CRS.\n"
            "The available area influences the formatting of the attribute table, compared "
            "with the treatment system total needed surface.\n\n"
            "<em>Warning</em>\n"
            "TP and e.coli are not completely ready for this version of ELAN."
        )

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
                self.tr("Maximum stages number (between 1 and 3)"),
                Qgis.ProcessingNumberParameterType.Integer,
                defaultValue=3,
                optional=False,
                minValue=1,
                maxValue=3,
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

        self.addConcentrationParameter(self.TSS_IN, self.tr("TSS inflow concentration [g/m3]"), "TSS_in")
        self.addConcentrationParameter(self.BOD5_IN, self.tr("BOD5 inflow concentration [g/m3]"), "BOD5_in")
        self.addConcentrationParameter(self.TKN_IN, self.tr("TKN inflow concentration [g/m3]"), "TKN_in")
        self.addConcentrationParameter(self.COD_IN, self.tr("COD inflow concentration [g/m3]"), "COD_in")
        self.addConcentrationParameter(self.NO3N_IN, self.tr("NO3-N inflow concentration [g/m3]"), "NO3N_in")
        self.addConcentrationParameter(self.TP_IN, self.tr("TP inflow concentration [g/m3]"), "TP_in")
        self.addConcentrationParameter(self.ECOLI_IN, self.tr("e.coli inflow concentration [UFC/100mL]"), "ecoli_in")

        self.addConcentrationParameter(self.TSS_OBJ, self.tr("TSS outflow concentration target [g/m3]"), "TSS_obj")
        self.addConcentrationParameter(self.BOD5_OBJ, self.tr("BOD5 outflow concentration target [g/m3]"), "BOD5_obj")
        self.addConcentrationParameter(self.TKN_OBJ, self.tr("TKN outflow concentration target [g/m3]"), "TKN_obj")
        self.addConcentrationParameter(self.COD_OBJ, self.tr("COD outflow concentration target [g/m3]"), "COD_obj")
        self.addConcentrationParameter(self.NO3N_OBJ, self.tr("NO3-N outflow concentration target [g/m3]"), "NO3N_obj")
        self.addConcentrationParameter(self.TN_OBJ, self.tr("TN outflow concentration target [g/m3]"), "TN_obj")
        self.addConcentrationParameter(self.TP_OBJ, self.tr("TP outflow concentration target [g/m3]"), "TP_obj")
        self.addConcentrationParameter(
            self.ECOLI_OBJ, self.tr("e.coli outflow concentration target [UFC/100mL]"), "ecoli_obj"
        )

    def addConcentrationParameter(self, param_id: str, param_desc: str, param_default: str) -> None:
        """
        Add a concentration obj or in field from SINKS layer to the processing advanced parameters.
        """

        param = QgsProcessingParameterField(
            param_id,
            param_desc,
            parentLayerParameterName=self.SINKS,
            type=Qgis.ProcessingFieldParameterDataType.Numeric,
            defaultValue=param_default,
        )
        param.setFlags(Qgis.ProcessingParameterFlag.Advanced)
        self.addParameter(param)

    def processAlgorithm(
        self, parameters, context, feedback
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Here is where the processing itself takes place.
        """

        # Add EXTERNAL_LIRBARIES_DIR if not already in site directory
        if not wetlandoptimizerInstalled():
            raise QgsProcessingException(
                self.tr("The wetlandoptimizer library is not installed.\nGo to ELAN settings to install it.")
            )

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

        # Get the names of every field from WWTP layer
        TSS_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TSS_IN, context)
        BOD5_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.BOD5_IN, context)
        TKN_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TKN_IN, context)
        COD_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.COD_IN, context)
        NO3N_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.NO3N_IN, context)
        TP_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TP_IN, context)
        ecoli_in_field_name = self.getWwtpFieldName(sinks_source, parameters, self.ECOLI_IN, context)
        TSS_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TSS_OBJ, context)
        BOD5_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.BOD5_OBJ, context)
        TKN_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TKN_OBJ, context)
        COD_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.COD_OBJ, context)
        NO3N_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.NO3N_OBJ, context)
        TN_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TN_OBJ, context)
        TP_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.TP_OBJ, context)
        ecoli_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.ECOLI_OBJ, context)
        Q_obj_field_name = self.getWwtpFieldName(sinks_source, parameters, self.Q_FIELD, context)
        sink_coords_field_name = self.getWwtpFieldName(sinks_source, parameters, self.SINK_COORDS, context)

        stages_max = self.parameterAsInt(parameters, self.STAGES_MAX, context)
        climate = self.climates[self.parameterAsInt(parameters, self.CLIMATE, context)][1]

        # Loop on WWTP and run wetlandoptimizer on each one
        assigned_surfaces_ids = []
        optimizations_parameters = []
        wwtp_features: list[QgsFeature] = list(sinks_source.getFeatures())
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

            # Get target concentrations
            Cobj = self.getTargetConcentrations(
                TSS_obj_field_name,
                BOD5_obj_field_name,
                TKN_obj_field_name,
                COD_obj_field_name,
                NO3N_obj_field_name,
                TN_obj_field_name,
                TP_obj_field_name,
                ecoli_obj_field_name,
                wwtp_feature,
            )

            # Get input concentrations
            Cin = self.getInputConcentrations(
                TSS_in_field_name,
                BOD5_in_field_name,
                COD_in_field_name,
                TKN_in_field_name,
                NO3N_in_field_name,
                TP_in_field_name,
                ecoli_in_field_name,
                wwtp_feature,
            )

            optimizations_parameters.append(
                OptimizationParameters(
                    Cin, Cobj, wwtp_feature[Q_obj_field_name], stages_max, climate, available_surface
                )
            )

        # Set multiprocess path on Windows
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
                ) from err

        # Launch optimizations on every WWTP in parallel
        with multiprocessing.Pool() as pool:
            optimizations_results = pool.map(run_optimization, optimizations_parameters)

        # Prepare output layer
        treatment_sink, treatment_dest = self.parameterAsSink(
            parameters, self.TREATMENT, context, outputFields(), Qgis.WkbType.Point, sinks_source_crs
        )
        if treatment_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.TREATMENT))

        # Loop each result and add features
        for optimization_result, wwtp_feature in zip(optimizations_results, wwtp_features):
            for pathway_result in optimization_result.pathway_results:
                output_feature = QgsFeature()
                output_feature.setFields(outputFields())
                output_feature.setGeometry(wwtp_feature.geometry())
                output_feature["name_stages"] = "-".join(pathway_result.name_stages)
                output_feature["pathway_id"] = pathway_result.id
                output_feature["available_surface"] = ceil(optimization_result.available_surface)
                output_feature["sink_coords"] = wwtp_feature[sink_coords_field_name]
                output_feature["total_volume"] = round(pathway_result.total_volume)
                output_feature["total_surface"] = ceil(pathway_result.total_surface)
                output_feature["depth_stages_unsat"] = json.dumps(pathway_result.unsaturated_depth_stages)
                output_feature["depth_stages_sat"] = json.dumps(pathway_result.saturated_depth_stages)
                output_feature["surface_stages"] = json.dumps([ceil(val) for val in pathway_result.surface_stages])
                output_feature["TSS_loading_stages"] = json.dumps(pathway_result.TSS_loading_stages)
                output_feature["BOD5_loading_stages"] = json.dumps(pathway_result.BOD5_loading_stages)
                output_feature["TKN_loading_stages"] = json.dumps(pathway_result.TKN_loading_stages)
                output_feature["COD_loading_stages"] = json.dumps(pathway_result.COD_loading_stages)
                output_feature["hydraulic_loading_rate_stages"] = json.dumps(
                    pathway_result.hydraulic_loading_rate_stages
                )
                output_feature["TSS_concentration"] = round(pathway_result.TSS_concentration, 2)
                output_feature["BOD5_concentration"] = round(pathway_result.BOD5_concentration, 2)
                output_feature["TKN_concentration"] = round(pathway_result.TKN_concentration, 2)
                output_feature["COD_concentration"] = round(pathway_result.COD_concentration, 2)
                output_feature["NO3N_concentration"] = round(pathway_result.NO3N_concentration, 2)
                output_feature["TN_concentration"] = round(pathway_result.TN_concentration, 2)
                output_feature["TP_concentration"] = round(pathway_result.TP_concentration, 2)
                output_feature["ecoli_concentration"] = round(pathway_result.ecoli_concentration, 2)
                output_feature["TSS_deviation"] = (
                    round(pathway_result.TSS_deviation, 2) if pathway_result.TSS_deviation is not None else None
                )
                output_feature["BOD5_deviation"] = (
                    round(pathway_result.BOD5_deviation, 2) if pathway_result.BOD5_deviation is not None else None
                )
                output_feature["TKN_deviation"] = (
                    round(pathway_result.TKN_deviation, 2) if pathway_result.TKN_deviation is not None else None
                )
                output_feature["COD_deviation"] = (
                    round(pathway_result.COD_deviation, 2) if pathway_result.COD_deviation is not None else None
                )
                output_feature["NO3N_deviation"] = (
                    round(pathway_result.NO3N_deviation, 2) if pathway_result.NO3N_deviation is not None else None
                )
                output_feature["TN_deviation"] = (
                    round(pathway_result.TN_deviation, 2) if pathway_result.TN_deviation is not None else None
                )
                output_feature["TP_deviation"] = (
                    round(pathway_result.TP_deviation, 2) if pathway_result.TP_deviation is not None else None
                )
                output_feature["ecoli_deviation"] = (
                    round(pathway_result.ecoli_deviation, 2) if pathway_result.ecoli_deviation is not None else None
                )

                # Normalized concentration values
                TSS_obj, BOD5_obj, TKN_obj, COD_obj, NO3N_obj, TN_obj, TP_obj, ecoli_obj = optimization_result.Cobj
                if TSS_obj is not None and TSS_obj > 0:
                    output_feature["TSS_norm"] = round(pathway_result.TSS_concentration / TSS_obj, 2)
                if BOD5_obj is not None and BOD5_obj > 0:
                    output_feature["BOD5_norm"] = round(pathway_result.BOD5_concentration / BOD5_obj, 2)
                if COD_obj is not None and COD_obj > 0:
                    output_feature["COD_norm"] = round(pathway_result.COD_concentration / COD_obj, 2)
                if TKN_obj is not None and TKN_obj > 0:
                    output_feature["TKN_norm"] = round(pathway_result.TKN_concentration / TKN_obj, 2)
                if NO3N_obj is not None and NO3N_obj > 0:
                    output_feature["NO3N_norm"] = round(pathway_result.NO3N_concentration / NO3N_obj, 2)
                if TN_obj is not None and TN_obj > 0:
                    output_feature["TN_norm"] = round(pathway_result.TN_concentration / TN_obj, 2)
                if TP_obj is not None and TP_obj > 0:
                    output_feature["TP_norm"] = round(pathway_result.TP_concentration / TP_obj, 2)
                if ecoli_obj is not None and ecoli_obj > 0:
                    output_feature["ecoli_norm"] = round(pathway_result.ecoli_concentration / ecoli_obj, 2)

                if optimization_result.available_surface > 0:
                    output_feature["surface_norm"] = round(
                        pathway_result.total_surface / optimization_result.available_surface, 2
                    )

                treatment_sink.addFeature(output_feature)

        if context.willLoadLayerOnCompletion(treatment_dest):
            context.layerToLoadOnCompletionDetails(treatment_dest).setPostProcessor(self.post_processor)
        return {self.TREATMENT: treatment_dest}

    def getWwtpFieldName(
        self,
        sinks_source: QgsProcessingFeatureSource,
        parameters: dict[Optional[str], Any],
        parameter_name: str,
        context: QgsProcessingContext,
    ) -> str:
        """
        Get the field name in the WWTP input layer, and check that it really exists.
        """

        obj_field_name = self.parameterAsString(parameters, parameter_name, context)
        if obj_field_name not in sinks_source.fields().names():
            raise QgsProcessingException(
                self.tr("Field '{}' does not exist in input WWTP layer").format(obj_field_name)
            )

        return obj_field_name

    def getInputConcentrations(
        self,
        TSS_in_field_name: str,
        BOD5_in_field_name: str,
        COD_in_field_name: str,
        TKN_in_field_name: str,
        NO3N_in_field_name: str,
        TP_in_field_name: str,
        ecoli_in_field_name: str,
        wwtp_feature: QgsFeature,
    ) -> list:
        """
        Get input concentration values from a WWTP feature.
        Use default values if no value is found.
        """

        from wetlandoptimizer.main import COD_Fractionation  # pylint: disable=import-outside-toplevel

        inflow_concentrations = [
            wwtp_feature[TSS_in_field_name],
            wwtp_feature[BOD5_in_field_name],
            wwtp_feature[TKN_in_field_name],
            wwtp_feature[COD_in_field_name],
            wwtp_feature[NO3N_in_field_name],
            wwtp_feature[TP_in_field_name],
            wwtp_feature[ecoli_in_field_name],
        ]
        inflow_concentrations = [
            None if isinstance(val, QVariant) or val is NULL else val for val in inflow_concentrations
        ]

        if any(val is None for val in inflow_concentrations):
            raise QgsProcessingException(
                self.tr("An inflow concentration has a NULL value: {}.").format(inflow_concentrations)
            )
        Cin = COD_Fractionation(inflow_concentrations)
        if all(val == 0 for val in Cin):
            raise QgsProcessingException(
                self.tr(
                    "Inflow concentrations have incorrect values: {}, causing an error during COD_Fractionation step."
                ).format(inflow_concentrations)
            )

        return Cin

    def getTargetConcentrations(
        self,
        TSS_obj_field_name: str,
        BOD5_obj_field_name: str,
        TKN_obj_field_name: str,
        COD_obj_field_name: str,
        NO3N_obj_field_name: str,
        TN_obj_field_name: str,
        TP_obj_field_name: str,
        ecoli_obj_field_name: str,
        wwtp_feature: QgsFeature,
    ) -> list[Optional[float]]:
        """
        Get and check objectives values from a WWTP feature
        It raises an exception if a check fails.
        """

        check_obj_not_null = [
            (TSS_obj_field_name, self.tr("TSS")),
            (BOD5_obj_field_name, self.tr("BOD5")),
            (COD_obj_field_name, self.tr("COD")),
        ]
        check_obj_positive = check_obj_not_null + [
            (TKN_obj_field_name, self.tr("TNK")),
            (NO3N_obj_field_name, self.tr("NO3-N")),
            (TN_obj_field_name, self.tr("TN")),
            (TP_obj_field_name, self.tr("TP")),
            (ecoli_obj_field_name, self.tr("e.coli")),
        ]

        # Check objectives values that should not be NULL
        errors = []
        for obj_field_name, obj_name in check_obj_not_null:
            if (obj_value := wwtp_feature[obj_field_name]) == NULL:
                errors.append(obj_name)
        if len(errors) > 0:
            raise QgsProcessingException(self.tr("These target values can't be NULL:") + " " + ", ".join(errors))

        # Check objectives values that should be positives when they are not NULL
        errors.clear()
        for obj_field_name, obj_name in check_obj_positive:
            if (obj_value := wwtp_feature[obj_field_name]) != NULL and obj_value <= 0:
                errors.append(obj_name)
        if len(errors) > 0:
            raise QgsProcessingException(
                self.tr("These target values must be strictly positive:") + " " + ", ".join(errors)
            )

        Cobj = [
            wwtp_feature[TSS_obj_field_name],
            wwtp_feature[BOD5_obj_field_name],
            wwtp_feature[TKN_obj_field_name],
            wwtp_feature[COD_obj_field_name],
            wwtp_feature[NO3N_obj_field_name],
            wwtp_feature[TN_obj_field_name],
            wwtp_feature[TP_obj_field_name],
            wwtp_feature[ecoli_obj_field_name],
        ]

        # Replace NULL values with None
        Cobj = [None if param == NULL else param for param in Cobj]
        return Cobj


def outputFields() -> QgsFields:
    """Definition of the output fields for the output layer"""

    fields = [
        # String field containing the sink coordinate
        ("sink_coords", QMetaType.Type.QString),
        # Pathway identifier
        ("pathway_id", QMetaType.Type.QString),
        # String field containing the names and materials of the stages
        ("name_stages", QMetaType.Type.QString),
        # String fields containing JSON list with size values for each stage
        ("surface_stages", QMetaType.Type.QString),
        ("depth_stages_sat", QMetaType.Type.QString),
        ("depth_stages_unsat", QMetaType.Type.QString),
        # String fields containing JSON list with loading values for each stage
        ("TSS_loading_stages", QMetaType.Type.QString),
        ("BOD5_loading_stages", QMetaType.Type.QString),
        ("TKN_loading_stages", QMetaType.Type.QString),
        ("COD_loading_stages", QMetaType.Type.QString),
        ("hydraulic_loading_rate_stages", QMetaType.Type.QString),
        # Dimensions
        ("available_surface", QMetaType.Type.Double),
        ("surface_norm", QMetaType.Type.Double),
        ("total_surface", QMetaType.Type.Double),
        ("total_volume", QMetaType.Type.Double),
        # Concentrations
        ("TSS_concentration", QMetaType.Type.Double),
        ("BOD5_concentration", QMetaType.Type.Double),
        ("TKN_concentration", QMetaType.Type.Double),
        ("COD_concentration", QMetaType.Type.Double),
        ("NO3N_concentration", QMetaType.Type.Double),
        ("TN_concentration", QMetaType.Type.Double),
        ("TP_concentration", QMetaType.Type.Double),
        ("ecoli_concentration", QMetaType.Type.Double),
        # Deviations
        ("TSS_deviation", QMetaType.Type.Double),
        ("BOD5_deviation", QMetaType.Type.Double),
        ("TKN_deviation", QMetaType.Type.Double),
        ("COD_deviation", QMetaType.Type.Double),
        ("NO3N_deviation", QMetaType.Type.Double),
        ("TN_deviation", QMetaType.Type.Double),
        ("TP_deviation", QMetaType.Type.Double),
        ("ecoli_deviation", QMetaType.Type.Double),
        # Normalized concentrations
        ("TSS_norm", QMetaType.Type.Double),
        ("BOD5_norm", QMetaType.Type.Double),
        ("TKN_norm", QMetaType.Type.Double),
        ("COD_norm", QMetaType.Type.Double),
        ("NO3N_norm", QMetaType.Type.Double),
        ("TN_norm", QMetaType.Type.Double),
        ("TP_norm", QMetaType.Type.Double),
        ("ecoli_norm", QMetaType.Type.Double),
    ]

    return QgsFields([QgsField(field_name, field_type) for field_name, field_type in fields])


class WetlandProcessPostProcessor(QgsProcessingLayerPostProcessorInterface, Translatable):
    """Post process layer to set attribute table conditionnal formatting and layer style"""

    def postProcessLayer(
        self,
        layer: Optional[QgsMapLayer],
        context: QgsProcessingContext,  # pylint: disable=unused-argument
        feedback: Optional[QgsProcessingFeedback],
    ):
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


class OptimizationParameters:  # pylint: disable=too-few-public-methods
    """Class to store parameters for parallel optimization"""

    def __init__(
        self,
        Cin: list[Optional[float]],
        Cobj: list[Optional[float]],
        Q: float,
        stages_max: int,
        climate: str,
        available_surface: float,
    ):  # pylint: disable=too-many-arguments
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
    from wetlandoptimizer.main import Results_Global_Generation_All  # pylint: disable=import-outside-toplevel

    optimization_parameters.pathway_results = Results_Global_Generation_All(
        optimization_parameters.Cin,
        optimization_parameters.Cobj,
        optimization_parameters.Q,
        optimization_parameters.stages_max,
        files_max=1,
        climate=optimization_parameters.climate,
    )
    return optimization_parameters
