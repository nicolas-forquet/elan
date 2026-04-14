"""
Utils functions for tests
"""

from pathlib import Path
from typing import Optional

from qgis.core import Qgis, QgsProject, QgsVectorLayer


def assert_same_layers(
    layer_a: QgsVectorLayer,
    layer_b: QgsVectorLayer,
    check_values_only_on_fields: Optional[list[str]] = None,
    check_geom=True,
):
    """
    Verify that layer_a and layer_b are the same.
        - feature count
        - field names
        - field types
        - unique values for each attribute
        - CRS
        - geometries

    If check_values_only_on_fields is provided (list of field names), the assertion for
    the uniqueValues is made only on these fields.
    """

    # feature count
    assert layer_a.featureCount() == layer_b.featureCount()

    # field names
    layer_a_field_names = layer_a.fields().names()
    layer_b_field_names = layer_b.fields().names()
    assert layer_a_field_names == layer_b_field_names, (
        f"layer_a field names: {layer_a_field_names} " f"but layer_b field names: {layer_b_field_names}"
    )

    # field types
    layer_a_field_types = [field.type() for field in layer_a.fields()]
    layer_b_field_types = [field.type() for field in layer_b.fields()]
    assert (
        layer_a_field_types == layer_b_field_types
    ), f"layer_a field types: {layer_a_field_types} but layer_b field types: {layer_b_field_types}"

    # CRS
    assert layer_a.crs() == layer_b.crs(), f"{layer_a.crs().authid()} != {layer_b.crs().authid()}"

    # unique values inside each field
    for idx in range(layer_a.fields().size()):
        field_name = layer_a.fields().at(idx).name()

        if check_values_only_on_fields is not None and field_name not in check_values_only_on_fields:
            continue

        if field_name == "distance":
            assert set(map(lambda x: round(x, 3), layer_a.uniqueValues(idx))) == set(
                map(lambda x: round(x, 3), layer_b.uniqueValues(idx))
            )
        else:
            assert layer_a.uniqueValues(idx) == layer_b.uniqueValues(idx), (
                f"Field {field_name}: layer_a unique values are {layer_a.uniqueValues(idx)} "
                f"but layer_b unique values are {layer_b.uniqueValues(idx)}"
            )

    # geometry for each feature (based on fid)
    precision = 8 if layer_a.crs().type() == Qgis.CrsType.Geographic2d else 3
    if check_geom:
        fid_idx = layer_a.fields().indexFromName("fid")
        assert fid_idx != -1, "a 'fid' field is required to check the geometries"
        fids = layer_a.uniqueValues(fid_idx)
        for fid in fids:
            geom_a = next(layer_a.getFeatures(f'"fid" = {fid}')).geometry().asWkt(precision)
            geom_b = next(layer_b.getFeatures(f'"fid" = {fid}')).geometry().asWkt(precision)
            assert geom_a == geom_b, f"{geom_a=}\n{geom_b=}"


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
