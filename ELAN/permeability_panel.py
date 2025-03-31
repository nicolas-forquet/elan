import time
from tempfile import NamedTemporaryFile

import processing
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.core import (
    QgsCoordinateTransformContext,
    QgsExpressionContextUtils,
    QgsFillSymbol,
    QgsMapLayerProxyModel,
    QgsProcessingFeatureSourceDefinition,
    QgsProject,
    QgsRuleBasedRenderer,
    QgsVectorLayerFeatureCounter,
)
from qgis.gui import QgsFeaturePickerWidget, QgsMapLayerComboBox
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.utils import OverrideCursor


class PermeabilityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.final_polys = None
        self.layer_nir_widget = QgsMapLayerComboBox()
        self.layer_nir_widget.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.layer_red_widget = QgsMapLayerComboBox()
        self.layer_red_widget.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.layer_zones_influence_widget = QgsMapLayerComboBox()
        self.layer_zones_influence_widget.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.zone_influence_widget = QgsFeaturePickerWidget()
        self.seuil_widget = QDoubleSpinBox()
        self.seuil_widget.setMinimum(-1)
        self.seuil_widget.setMaximum(1)
        self.seuil_widget.setSingleStep(0.01)
        self.pourcentage_widget = QLabel()
        self.set_permeabilite_button = QPushButton("Appliquer ce pourcentage\nà la zone")
        self.create_button = QPushButton("Créer la couche de perméabilité")

        layout = QFormLayout()
        raster_group_widget = QGroupBox()
        raster_group_widget.setTitle("Bandes raster")
        layout.addRow("Rouge", self.layer_red_widget)
        layout.addRow("Proche infra-rouge", self.layer_nir_widget)
        raster_group_widget.setLayout(layout)

        layout = QFormLayout()
        bv_group_widget = QGroupBox()
        bv_group_widget.setTitle("Zone d'influence")
        layout.addRow("Couche zone d'influence", self.layer_zones_influence_widget)
        layout.addRow("Zone sélectionné", self.zone_influence_widget)
        bv_group_widget.setLayout(layout)

        layout = QVBoxLayout()
        seuil_group_widget = QGroupBox()
        seuil_group_widget.setTitle("Seuil de perméabilité")
        layout.addWidget(self.seuil_widget)
        layout.addWidget(self.pourcentage_widget)
        layout.addWidget(self.set_permeabilite_button)
        seuil_group_widget.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(raster_group_widget)
        layout.addWidget(bv_group_widget)
        layout.addWidget(self.create_button)
        layout.addWidget(seuil_group_widget)
        layout.addStretch()
        self.setLayout(layout)

        self.layer_zones_influence_widget.layerChanged.connect(self.setZoneLayer)
        self.create_button.clicked.connect(self.launchComputePermeability)
        self.seuil_widget.valueChanged.connect(self.updateThreshold)
        self.set_permeabilite_button.clicked.connect(self.setPermeability)

        self.setZoneLayer(self.layer_zones_influence_widget.currentLayer())

        self.impermeable_rule = QgsRuleBasedRenderer.Rule(
            QgsFillSymbol.createSimple({"color": "#330000FF", "style_border": "no"}),
            filterExp="value <= @seuil_imper",
            label="Imperméable",
        )
        self.permeable_rule = QgsRuleBasedRenderer.Rule(
            QgsFillSymbol.createSimple({"color": "#3300FF00", "style_border": "no"}),
            filterExp="value > @seuil_imper",
            label="Perméable",
        )
        self.total_pixels = -1
        self.current_pourcentage = -1

    def setPermeability(self):
        layer_zones_influence = self.zone_influence_widget.layer()
        layer_zones_influence.startEditing()
        res = layer_zones_influence.changeAttributeValue(
            self.zone_influence_widget.feature().id(),
            layer_zones_influence.fields().indexFromName("pourcentage_impermeable"),
            self.current_pourcentage,
        )
        self.zone_influence_widget.layer().commitChanges()
        if not res:
            QMessageBox.critical(None, "Erreur", "Impossible d'assigner le pourcentage à la zone")

    def setZoneLayer(self, layer):
        self.zone_influence_widget.setLayer(layer)
        self.zone_influence_widget.setDisplayExpression(''' 'Zone ' || "id" || ' - point ' || "avaloir_id"''')

    def launchComputePermeability(self):
        with OverrideCursor(Qt.WaitCursor):
            self.computePermeability()

    def computePermeability(self):
        layer_nir = self.layer_nir_widget.currentLayer()
        layer_red = self.layer_red_widget.currentLayer()
        layer_zones_influence = self.layer_zones_influence_widget.currentLayer()
        zone_influence = self.zone_influence_widget.feature()
        layer_zones_influence.removeSelection()
        layer_zones_influence.select(zone_influence.id())

        file_ndvi = NamedTemporaryFile(suffix=".tif")
        bounding_box = zone_influence.geometry().boundingBox()
        raster_calc = QgsRasterCalculator(
            f"({layer_nir.name()}@1 - {layer_red.name()}@1) / ({layer_nir.name()}@1 + {layer_red.name()}@1)",
            file_ndvi.name,
            "GTiff",
            bounding_box,
            layer_zones_influence.crs(),
            int(bounding_box.width() / layer_nir.rasterUnitsPerPixelX()),
            int(bounding_box.height() / layer_nir.rasterUnitsPerPixelY()),
            QgsRasterCalculatorEntry.rasterEntries(),
            QgsCoordinateTransformContext(),
        )
        if raster_calc.processCalculation() != QgsRasterCalculator.Success:
            raise ValueError(raster_calc.lastError())

        # Calcul du NDVI
        polys = processing.run(
            "native:pixelstopolygons",
            {
                "INPUT_RASTER": file_ndvi.name,
                "RASTER_BAND": 1,
                "FIELD_NAME": "VALUE",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]

        # Découpage
        self.final_polys = processing.run(
            "native:extractbylocation",
            {
                "INPUT": polys,
                "INTERSECT": QgsProcessingFeatureSourceDefinition(
                    layer_zones_influence.source(), selectedFeaturesOnly=True
                ),
                "PREDICATE": [0],
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]

        # Index spatial
        processing.run(
            "native:createspatialindex",
            {"INPUT": self.final_polys},
        )

        # Style de la couche
        root = QgsRuleBasedRenderer.Rule(None)
        root.appendChild(self.impermeable_rule)
        root.appendChild(self.permeable_rule)
        self.seuil_widget.setValue(0)
        self.final_polys.setRenderer(QgsRuleBasedRenderer(root))
        self.final_polys.setName("Seuil de perméabilité")
        layer_zones_influence.removeSelection()

        # Nb d'entités
        self.total_pixels = self.final_polys.featureCount()
        QgsProject.instance().addMapLayer(self.final_polys)

    def updateThreshold(self, value):
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "seuil_imper", value)
        if self.final_polys is None:
            try:
                self.final_polys = QgsProject.instance().mapLayersByName("Seuil de perméabilité")[0]
            except IndexError:
                return

        counter = QgsVectorLayerFeatureCounter(self.final_polys)
        counter.run()
        while counter.isActive():
            time.sleep(0.01)
        nb_impermeable = counter.featureCount(self.impermeable_rule.ruleKey())
        self.current_pourcentage = round(nb_impermeable / self.total_pixels * 100, 2)
        self.pourcentage_widget.setText(f"{self.current_pourcentage}% de surface imperméable")
        self.final_polys.repaintRequested.emit()
