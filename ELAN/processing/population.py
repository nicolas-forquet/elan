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

from typing import Any, Optional

from qgis.core import (
    Qgis,
    QgsCoordinateTransformContext,
    QgsDistanceArea,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsMapLayer,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeatureBasedAlgorithm,
    QgsProcessingFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QMetaType

from ELAN.utils.tr import Translatable


class PopulationAreametricAlgorithm(QgsProcessingAlgorithm, Translatable):
    """
    Take a building layer (polygons) and create an output layer (points) with a population field
    filled with a computed value according to the building area, and building centroids.
    """

    INPUT_POPULATION_TOT = "INPUT_POPULATION_TOT"
    INPUT_POLYGON_LAYER = "INPUT_POLYGON_LAYER"
    OUTPUT_CENTROIDES_LAYER = "OUTPUT_CENTROIDES_LAYER"

    def createInstance(self):
        """Return an instance of this class"""
        return PopulationAreametricAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanpopulationareametric"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Population (areametric distribution)")

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
            "Compute the number of inhabitants per building based on a total number of inhabitants.\n"
            "The distribution is made according to each building surface area.\n\n"
            "The output layer has a population field and is a point layer representing the buildings centroids."
        )

    def initAlgorithm(self, config=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_POPULATION_TOT, self.tr("Total inhabitants (estimation)"), minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POLYGON_LAYER, self.tr("Buildings"), [Qgis.ProcessingSourceType.VectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_CENTROIDES_LAYER,
                self.tr("Buildings with areametric population"),
                Qgis.ProcessingSourceType.VectorPoint,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # pylint: disable=too-many-locals
        """
        Here is where the processing itself takes place.
        """

        polygon = self.parameterAsSource(parameters, self.INPUT_POLYGON_LAYER, context)
        if polygon is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POLYGON_LAYER))

        nb_hab_tot = self.parameterAsInt(parameters, self.INPUT_POPULATION_TOT, context)
        input_crs = polygon.sourceCrs()
        output_fields = QgsFields()
        for field in polygon.fields():
            output_fields.append(field)

        population_per_building = QgsField("population", QMetaType.Type.Double)
        output_fields.append(population_per_building)

        output_sink, centroid_population_dest = self.parameterAsSink(
            parameters,
            self.OUTPUT_CENTROIDES_LAYER,
            context,
            output_fields,
            Qgis.WkbType.Point,
            input_crs,
        )
        if output_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_CENTROIDES_LAYER))

        total_area = 0
        area_measurement = QgsDistanceArea()
        area_measurement.setSourceCrs(input_crs, QgsCoordinateTransformContext())
        area_measurement.setEllipsoid(input_crs.ellipsoidAcronym())

        for input_feature in polygon.getFeatures():
            total_area += area_measurement.measureArea(input_feature.geometry())

        nb_zero_hab = 0
        for input_feature in polygon.getFeatures():
            output_feature = QgsFeature(input_feature)
            output_feature.setFields(output_fields)
            for attribute_name, attribute_value in input_feature.attributeMap().items():
                output_feature.setAttribute(attribute_name, attribute_value)

            area = area_measurement.measureArea(input_feature.geometry())
            nb_hab = round((nb_hab_tot * area / total_area), 2)
            if nb_hab == 0:
                nb_zero_hab += 1
            output_feature.setAttribute(population_per_building.name(), nb_hab)
            output_feature.setGeometry(input_feature.geometry().centroid())
            output_sink.addFeature(output_feature, QgsFeatureSink.Flag.FastInsert)

        if feedback is not None and nb_zero_hab > 0:
            feedback.pushWarning(self.tr("Warning! {} building(s) with 0 inhabitants").format(nb_zero_hab))

        return {self.OUTPUT_CENTROIDES_LAYER: centroid_population_dest}


class PopulationUniformAlgorithm(QgsProcessingFeatureBasedAlgorithm, Translatable):
    """
    Take a building layer (polygons) and create an output layer (points) with a population field
    filled with an input numeric value, and building centroids.
    """

    INPUT_POPULATION = "INPUT_POPULATION"

    def __init__(self):
        super().__init__()
        self.population_nb = -1
        self.population_field = QgsField("population", QMetaType.Type.Double)

    def inputLayerTypes(self) -> list[int]:
        """The input layer type"""

        return [Qgis.ProcessingSourceType.VectorPolygon]

    def inputParameterDescription(self) -> str:
        """The input parameter description"""

        return self.tr("Buildings")

    def outputWkbType(self, inputWkbType: Qgis.WkbType) -> Qgis.WkbType:  # pylint: disable=invalid-name,unused-argument
        """The output geometry type"""

        return Qgis.WkbType.Point

    def outputName(self) -> str:
        """The output layer name"""
        return self.tr("Buildings with uniform population")

    def outputFields(self, inputFields: QgsFields) -> QgsFields:  # pylint: disable=invalid-name
        """Define the output fields"""

        output_fields = inputFields
        output_fields.append(self.population_field)
        return output_fields

    def initParameters(
        self, configuration: Optional[dict[Optional[str], Any]] = None  # pylint: disable=unused-argument
    ):
        """Initialize parameters"""

        population_parameter = QgsProcessingParameterNumber(
            self.INPUT_POPULATION,
            self.tr("Number of inhabitants per building"),
            type=Qgis.ProcessingNumberParameterType.Double,
        )
        population_parameter.setMetadata({"widget_wrapper": {"decimals": 2}})
        self.addParameter(population_parameter)

    def prepareAlgorithm(  # pylint: disable=unused-argument
        self,
        parameters: dict[Optional[str], Any],
        context: QgsProcessingContext,
        feedback: Optional[QgsProcessingFeedback],
    ) -> bool:
        """Prepare other algorithm inputs"""

        self.population_nb = self.parameterAsDouble(parameters, self.INPUT_POPULATION, context)
        return self.population_nb >= 0

    def processFeature(  # pylint: disable=unused-argument
        self,
        feature: QgsFeature,
        context: QgsProcessingContext,
        feedback: Optional[QgsProcessingFeedback],
    ) -> list[QgsFeature]:
        """
        Process the input feature. This method is called for every feature in the input layer.
        """

        # Create output feature
        output_feature = QgsFeature()
        output_feature.setFields(self.outputFields(feature.fields()))

        # Copy input attributes
        for attribute_name, attribute_value in feature.attributeMap().items():
            output_feature.setAttribute(attribute_name, attribute_value)

        # Add population attribute
        output_feature.setAttribute(self.population_field.name(), self.population_nb)

        # Compute centroid
        output_feature.setGeometry(feature.geometry().centroid())

        return [output_feature]

    def supportInPlaceEdit(self, layer: Optional[QgsMapLayer]) -> bool:  # pylint: disable=unused-argument
        """Our processing does not support in-place edit"""

        return False

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it.
        """
        return self.tr(
            "For each building, the number of inhabitants is set to the number given as input.\n\n"
            "The output layer has a population field and is a point layer representing the buildings centroids."
        )

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanpopulationuniform"

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Population (uniform distribution)")

    def group(self) -> str:
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Data pre-processing")

    def groupId(self) -> str:
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanpreprocessings"

    def createInstance(self):
        """Return an instance of this class"""
        return PopulationUniformAlgorithm()
