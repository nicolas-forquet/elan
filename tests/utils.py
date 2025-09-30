"""
Utils functions for tests
"""

from pathlib import Path

from qgis.core import QgsProject, QgsVectorLayer


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
        if layer_a.fields().at(idx).name() == "distance":
            assert set(map(lambda x: round(x, 3), layer_a.uniqueValues(idx))) == set(
                map(lambda x: round(x, 3), layer_b.uniqueValues(idx))
            )
        else:
            assert layer_a.uniqueValues(idx) == layer_b.uniqueValues(idx)


def load_layer(gpkg_path: str | Path, layer_name: str) -> QgsVectorLayer:
    """
    Returns a QgsVectorLayer from a geopackage and a layer name
    """

    assert Path(gpkg_path).exists()
    uri = str(gpkg_path) + f"|layername={layer_name}"
    layer = QgsVectorLayer(uri, layer_name, "ogr")
    assert layer.isValid()

    # Give ownership of the layer to the project.
    # The project will take care of deleting the layer to avoid segfaults.
    if (project := QgsProject.instance()) is not None:
        project.addMapLayer(layer)

    return layer
