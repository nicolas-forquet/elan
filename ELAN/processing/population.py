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

from qgis.core import (
    Qgis,
    QgsCoordinateTransformContext,
    QgsDistanceArea,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QVariant

from ELAN.utils.tr import Translatable


class PopulationAlgorithm(QgsProcessingAlgorithm, Translatable):

    INPUT_POPULATION_TOT = "INPUT_POPULATION_TOT"
    INPUT_POLYGON_LAYER = "INPUT_POLYGON_LAYER"
    OUTPUT_CENTROIDES_LAYER = "OUTPUT_CENTROIDES_LAYER"

    def createInstance(self):
        return PopulationAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "elanpopulation"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Population")

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
        return self.tr("Total inhabitants per buildings (estimation)")

    def initAlgorithm(self, config=None):  # pylint: disable=unused-argument
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_POPULATION_TOT,
                self.tr("Total inhabitants (estimation)"),
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
                self.tr("Buildings with population"),
                Qgis.ProcessingSourceType.VectorPoint,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        polygon = self.parameterAsSource(parameters, self.INPUT_POLYGON_LAYER, context)
        if polygon is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POLYGON_LAYER))

        nb_hab_tot = self.parameterAsInt(parameters, self.INPUT_POPULATION_TOT, context)
        input_crs = polygon.sourceCrs()
        output_fields = QgsFields()
        for field in polygon.fields():
            output_fields.append(field)

        population_per_building = QgsField("population", QVariant.Double)
        output_fields.append(population_per_building)

        output_sink, centroid_population_dest = self.parameterAsSink(
            parameters,
            self.OUTPUT_CENTROIDES_LAYER,
            context,
            output_fields,
            Qgis.WkbType.Point,
            input_crs,
        )

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
