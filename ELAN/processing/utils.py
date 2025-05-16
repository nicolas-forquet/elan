from processing import QgsVectorLayer
from qgis.core import (
    QgsMapLayerStyle,
    QgsProcessingLayerPostProcessorInterface,
)

from ELAN.__about__ import DIR_PLUGIN_ROOT, LOCALE
from ELAN.utils.tr import Translatable


def getLocalizedStylesDirectory():
    """
    Returns the layer styles directory according to language
    """

    styles_dir = DIR_PLUGIN_ROOT / "resources" / "layer_styles" / LOCALE
    if not styles_dir.exists():
        return None
    return styles_dir


class LoadGpkgStylesPostProcessor(QgsProcessingLayerPostProcessorInterface, Translatable):
    def postProcessLayer(self, layer, context, feedback):  # pylint: disable=unused-argument
        """
        Load the database styles in the layer style manager
        """
        if layer is None or not layer.isValid() or not isinstance(layer, QgsVectorLayer):
            return

        # Set styles
        layer.loadDefaultStyle()
        if (style_manager := layer.styleManager()) is not None:
            style_count, styles_ids, styles_names = layer.listStylesInDatabase()[:3]
            for style_name, style_id in zip(styles_names[:style_count], styles_ids[:style_count]):
                style_manager.addStyle(style_name, QgsMapLayerStyle(layer.getStyleFromDatabase(style_id)[0]))
