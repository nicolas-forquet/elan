"""
test_roads_buildings
"""

import json
import re
from zipfile import ZipFile

import pytest
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsProcessingException,
    QgsVectorLayer,
)

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_roads_buildings(elan_processing, mocker, tmp_path):

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_alg = RoadsBuildingsAlgorithm()
    assert roads_buildings_alg.name() == "elanroadsbuildings"
    assert roads_buildings_alg.groupId() == "elanpreprocessings"

    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "CENTROID_BUILDINGS_OUTPUT": str(tmp_path / "buildings_centroids_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "CENTROID_MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_centroids_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
        "PROJ": False,
    }

    osm_zip_path = test_data_dir / "osm_roads_buildings.zip"
    assert osm_zip_path.exists()
    assert tmp_path.exists()
    json_osm_text = ""
    with ZipFile(osm_zip_path) as osm_zip:
        with osm_zip.open("osm_roads_buildings.json") as osm_json:
            json_osm_text = osm_json.read().decode()

    mock_response = mocker.Mock()
    mock_response.json.return_value = json.loads(json_osm_text)
    mocker.patch("ELAN.processing.roads_buildings.requests.get", return_value=mock_response)
    res = elan_processing.run(roads_buildings_alg, roads_buildings_param)

    assert res != {}

    layers_generated = [
        "buildings_generated_output",
        "buildings_centroids_generated_output",
        "roads_generated_output",
        "buildings_merged_generated_output",
        "buildings_centroids_merged_generated_output",
    ]
    layers_reference = [
        "buildings_reference_output",
        "buildings_centroids_reference_output",
        "roads_reference_output",
        "buildings_merged_reference_output",
        "buildings_centroids_merged_reference_output",
    ]

    for layer_reference, layer_generated in zip(layers_reference, layers_generated):
        layer_ref = load_layer(test_data_dir / "roads_buildings_output.gpkg.zip", layer_reference)
        layer_gen = load_layer((tmp_path / layer_generated).with_suffix(".gpkg"), layer_generated)
        assert_same_layers(layer_ref, layer_gen)


def test_error_big_polygon(elan_processing):
    """
    Verify the error raised:
    - To big polygon input
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test_big_rect", "memory")
    if (provider := layer.dataProvider()) is None:
        raise RuntimeError("Unexpected error: layer provider is None")

    feat = QgsFeature()
    geom = QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))")
    feat.setGeometry(geom)
    provider.addFeature(feat)
    layer.updateExtents()

    with pytest.raises(QgsProcessingException, match=re.compile("The extent of the extraction area is too big")):
        elan_processing.run(roads_buildings_alg, {"POLYGON": layer})


def test_error_empty_polygon(elan_processing):
    """
    Verify the error raised:
    - empty polygon input
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()

    with pytest.raises(QgsProcessingException, match=re.compile("The extent of the extraction area is null")):
        elan_processing.run(
            roads_buildings_alg, {"POLYGON": QgsVectorLayer("Polygon?crs=EPSG:4326", "test_null", "memory")}
        )
