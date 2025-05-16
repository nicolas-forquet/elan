"""
Utils functions for tests
"""

from pathlib import Path

from qgis.core import QgsVectorLayer


def assert_same_layers(layer_a: QgsVectorLayer, layer_b: QgsVectorLayer):
    """
    Verify that layer_a and layer_b are the same.
    - feature count
    - field names
    - field types
    - unique values for each attribute
    """

    assert layer_a.featureCount() == layer_b.featureCount()
    assert [field.name() for field in layer_a.fields()] == [field.name() for field in layer_b.fields()]
    assert [field.type() for field in layer_a.fields()] == [field.type() for field in layer_b.fields()]

    for idx in range(layer_a.fields().size()):
        assert layer_a.uniqueValues(idx) == layer_b.uniqueValues(idx)


def load_layer(gpkg_path: str | Path, layer_name: str) -> QgsVectorLayer:
    """
    Return layer from a geopackage
    """

    uri = str(gpkg_path) + f"|layername={layer_name}"
    layer = QgsVectorLayer(uri, layer_name, "ogr")
    assert layer.isValid()
    return layer
