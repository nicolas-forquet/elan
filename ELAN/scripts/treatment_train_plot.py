import json
from typing import Optional, cast

from qgis.core import NULL, QgsVectorLayer
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface, plugins

from ELAN.utils.tr import Translatable


class ProcessPlots(Translatable):

    normalized_fields = [
        "surface_norm",
        "TSS_norm",
        "BOD5_norm",
        "TKN_norm",
        "COD_norm",
        "NO3_norm",
        "TN_norm",
        "P_norm",
        "col_norm",
    ]

    loading_fields = [
        "TSS_loading_stages",
        "BOD5_loading_stages",
        "TKN_loading_stages",
        "COD_loading_stages",
    ]

    def get_dataplotly_panel(self):
        """
        Get DataPlotly main dock panel.
        Returns None if not found.
        """

        try:
            data_plotly_plugin = plugins["DataPlotly"]
        except KeyError:
            QMessageBox.warning(
                None,
                self.tr("Warning"),
                self.tr("DataPlotly plugin not found!\nIt must be installed and activated (see the plugin manager)."),
            )
            return

        if (main_dock := data_plotly_plugin.dock_manager.getDock("DataPlotly")) is None:
            QMessageBox.warning(
                None,
                self.tr("Warning"),
                self.tr("Main dock from DataPlotly can't be found. Please check your DataPlotly configuration."),
            )
            return

        if not main_dock.isUserVisible():
            main_dock.setUserVisible(True)

        return main_dock.main_panel

    @staticmethod
    def generate_gradient(base_color: str, steps: int):
        """
        Generate a gradient from a base hexadecimal color.

        :param base_color: base hexadecimal color (ie. : "#57322d")
        :param steps: number of colors in the gradient
        :return: hexadecimal color list
        """
        # Retirer le "#" de la couleur hexadécimale
        base_color = base_color.lstrip("#")

        # Convertir la couleur hex en RGB
        r, g, b = tuple(int(base_color[i : i + 2], 16) for i in (0, 2, 4))

        # Calculer la différence vers la couleur blanche (ou toute autre couleur de fin de dégradé)
        diff_r = 255 - r
        diff_g = 255 - g
        diff_b = 255 - b

        gradient = []

        # Créer les couleurs du dégradé
        for i in range(steps):
            new_r = r + (diff_r * i / (steps - 1))
            new_g = g + (diff_g * i / (steps - 1))
            new_b = b + (diff_b * i / (steps - 1))

            # Convertir en hex et ajouter à la liste
            hex_color = f"#{int(new_r):02x}{int(new_g):02x}{int(new_b):02x}"
            gradient.append(hex_color)

        return gradient

    def getActiveLayer(self) -> Optional[QgsVectorLayer]:
        """
        Get the active layer and return it if it is a treatment train layer.
        (based on the layer fields)
        """

        if (layer := cast(QgisInterface, iface).activeLayer()) is None:
            return

        missing_fields = ""
        if isinstance(layer, QgsVectorLayer):
            fields_to_check = set(self.normalized_fields).union(set(self.loading_fields))
            layer_fields = {field.name() for field in layer.fields()}
            if fields_to_check.issubset(layer_fields):
                return layer

            missing_fields = fields_to_check.difference(layer_fields)

        err_msg = self.tr("The active layer is not a treatment train layer.")
        if missing_fields != "":
            err_msg += self.tr("\nMissing fields: {}").format(
                str(missing_fields)[1:-1]  # remove starting and ending braces
            )
        QMessageBox.warning(None, self.tr("Warning"), err_msg)

    def validateAndGetMetadata(self, layer: QgsVectorLayer) -> tuple[bool, int, list[str]]:
        """
        Verify that in the layer, the features have
            - different treatment trains
            - one unique WWTP
            - more than one stage

        Because this function iterates on the features, we get some information, and we return
        metadata about the layer (maximum number of stages).

        If the layer has selected features, the verification si performed on the selected features,
        else, the verification is performed on all its features.
        """

        if layer.selectedFeatureCount() > 0:
            features = layer.getSelectedFeatures()
        else:
            features = layer.getFeatures()

        unique_name_stages = []
        unique_sink_coords = []
        fields_to_remove = []
        normalized_fields_without_null_values = self.normalized_fields.copy()
        max_stages_nb = -1
        for feature in features:
            unique_name_stages.append(feature["name_stages"])
            unique_sink_coords.append(feature["sink_coords"])
            max_stages_nb = max(max_stages_nb, len(json.loads(feature[self.loading_fields[0]])))

            for field in normalized_fields_without_null_values:
                if feature[field] == NULL and field not in fields_to_remove:
                    fields_to_remove.append(field)

        for field_to_remove in fields_to_remove:
            normalized_fields_without_null_values.remove(field_to_remove)

        if len(set(unique_sink_coords)) > 1:
            field_alias = layer.fields().at(layer.fields().indexFromName("sink_coords")).alias()
            QMessageBox.warning(
                None,
                self.tr("Warning"),
                self.tr("Features have different {}.\n" "Select only features with the same {}.").format(
                    field_alias, field_alias
                ),
            )
            return (False, max_stages_nb, normalized_fields_without_null_values)

        if len(set(unique_name_stages)) < len(unique_name_stages):
            field_alias = layer.fields().at(layer.fields().indexFromName("name_stages")).alias()
            QMessageBox.warning(
                None,
                self.tr("Warning"),
                self.tr("More than 1 feature with the same {}.\n" "Select only features with different {}.").format(
                    field_alias, field_alias
                ),
            )
            return (False, max_stages_nb, normalized_fields_without_null_values)

        if max_stages_nb <= 0:
            QMessageBox.warning(None, self.tr("Warning"), self.tr("The features don't have any stage"))
            return (False, max_stages_nb, normalized_fields_without_null_values)

        if len(normalized_fields_without_null_values) == 0:
            QMessageBox.warning(
                None, self.tr("Warning"), self.tr("The features don't have any normalized fields value.")
            )
            return (False, max_stages_nb, normalized_fields_without_null_values)

        return (True, max_stages_nb, normalized_fields_without_null_values)

    def barPlot(self):
        """
        Control DataPlotly interface to create a bar plot of all polluants in the active treatment train layer.
        """

        if (layer := self.getActiveLayer()) is None:
            return

        if (main_panel := self.get_dataplotly_panel()) is None:
            return

        layer_valid, max_stages_nb, _ = self.validateAndGetMetadata(layer)
        if not layer_valid:
            return

        nb_pollutant = len(self.loading_fields)

        bar_color_gradients = [
            g
            for g in [
                self.generate_gradient(c, max_stages_nb + 1) for c in ["#70ad47", "#5a9bd5", "#ffc000", "#43682b"]
            ]
        ]
        bar_legend_labels = [self.tr("TSS"), self.tr("BOD5"), self.tr("TKN"), self.tr("COD")]

        # Following conditions should not appear (implementation problem from above lists)
        if len(bar_legend_labels) > nb_pollutant:
            raise RuntimeError("Missing a legend label for a field!")
        if len(bar_legend_labels) > nb_pollutant:
            raise RuntimeError("Missing a color for a field!")

        main_panel.clearPlotView()
        main_panel.layer_combo.setLayer(layer)
        main_panel.plot_combo.setCurrentIndex(main_panel.plot_combo.findData("bar"))
        main_panel.selected_feature_check.setChecked(layer.selectedFeatureCount() > 0)
        main_panel.x_combo.setField('"name_stages"')
        main_panel.out_color_combo.setColor(QColor("#FFFFFF"))

        for i in range(max_stages_nb):

            # if this is not the first stage, then plot an empty bar as a separator
            if i > 0:
                main_panel.y_combo.setField("0")
                main_panel.legend_title.setText("")
                main_panel.in_color_combo.setColor(QColor("#FFFFFF"))
                main_panel.create_plot()

            # plot a bar for each pollutant
            for j in range(nb_pollutant):
                main_panel.y_combo.setField(f'from_json("{self.loading_fields[j]}")[{i}]')
                main_panel.legend_title.setText(f"{bar_legend_labels[j]} {self.tr("stage")} {i+1}")
                main_panel.in_color_combo.setColor(QColor(bar_color_gradients[j][i]))

                # Create the plot only if this is not the very last bar
                if i < max_stages_nb - 1 or j < nb_pollutant - 1:
                    main_panel.create_plot()

        # The settings below are overridden at every call of create_plot,
        # that is why we set them only at the end, before the very last call
        # to create_plot, which plots the last bar

        # Plot title and font
        main_panel.plot_title_line.setText(self.tr("Hydraulic and pollutant loading rates"))
        title_font = main_panel.font_title_style.currentFont()
        title_font.setPointSize(20)
        main_panel.font_title_style.setCurrentFont(title_font)

        # X axis title and font
        main_panel.y_axis_title.setText(self.tr("Loading rate (%)"))
        x_axis_font = main_panel.font_ylabel_style.currentFont()
        x_axis_font.setPointSize(15)
        main_panel.font_xlabel_style.setCurrentFont(x_axis_font)

        # Y axis title and font
        main_panel.x_axis_title.setText(self.tr("Treatment trains"))
        y_axis_font = main_panel.font_ylabel_style.currentFont()
        y_axis_font.setPointSize(15)
        main_panel.font_ylabel_style.setCurrentFont(y_axis_font)

        # Create last bar plot
        main_panel.create_plot()

    def radarPlot(self):
        """
        Control DataPlotly interface to create a radar plot of all normalized data.
        """

        if (layer := self.getActiveLayer()) is None:
            return

        if (main_panel := self.get_dataplotly_panel()) is None:
            return

        layer_valid, _, normalized_fields_without_null_values = self.validateAndGetMetadata(layer)
        if not layer_valid:
            return

        main_panel.clearPlotView()
        main_panel.layer_combo.setLayer(layer)
        main_panel.plot_combo.setCurrentIndex(main_panel.plot_combo.findData("radar"))
        main_panel.selected_feature_check.setChecked(layer.selectedFeatureCount() > 0)
        main_panel.y_combo_radar_label.setField('"name_stages"')
        for normalized_field in normalized_fields_without_null_values:
            main_panel.y_fields_combo.setItemCheckState(
                main_panel.y_fields_combo.findText(normalized_field), Qt.CheckState.Checked
            )
        main_panel.marker_type_combo.setCurrentIndex(main_panel.marker_type_combo.findData("lines+markers"))
        main_panel.line_combo_threshold.setCurrentText("Dash Line")
        main_panel.marker_size.setValue(5.0)

        # Color scale BlueYellowRed
        main_panel.color_scale_combo.setCurrentIndex(main_panel.color_scale_combo.findData("Portland"))

        # Plot title and font
        main_panel.plot_title_line.setText(self.tr("Treatment trains multicriteria analysis"))
        title_font = main_panel.font_title_style.currentFont()
        title_font.setPointSize(20)
        main_panel.font_title_style.setCurrentFont(title_font)

        # Create last bar plot
        main_panel.create_plot()
