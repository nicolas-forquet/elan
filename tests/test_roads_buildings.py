"""
test_roads_buildings
"""

from pathlib import Path

import pytest
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsVectorLayer,
)

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_roads_buildings(qgis_processing, mocker, tmp_path):
    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations
    import processing

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "roads_buildings"
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

    res = processing.run(roads_buildings_alg, roads_buildings_param)
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
        layer_ref = load_layer(f"{test_data_dir}/roads_buildings_output.gpkg.zip", layer_reference)
        layer_gen = load_layer(f"{tmp_path}/{layer_generated}.gpkg", layer_generated)
        assert_same_layers(layer_ref, layer_gen)


def test_error_roads_buildings(qgis_processing, mocker, tmp_path):
    """
    Verify the error raised :
    - To big polygon input
    - Empty polygon input
    """

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations
    import processing

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_alg = RoadsBuildingsAlgorithm()

    ##################################### test big polygon #####################################

    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test_big_rect", "memory")
    provider = layer.dataProvider()

    feat = QgsFeature()
    geom = QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))")
    feat.setGeometry(geom)
    provider.addFeatures([feat])
    layer.updateExtents()

    mocker.patch.object(roads_buildings_alg, "parameterAsSource", return_value=layer)

    parameters = {"POLYGON": "test_big_rect"}
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    with pytest.raises(QgsProcessingException, match="The extent of the extraction area is too big"):
        roads_buildings_alg.processAlgorithm(parameters, context, feedback)

    ##################################### test null polygon #####################################

    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test_null", "memory")
    provider = layer.dataProvider()

    feat = QgsFeature()
    geom = QgsGeometry.fromWkt("POLYGON(()")
    feat.setGeometry(geom)
    provider.addFeatures([feat])
    layer.updateExtents()

    mocker.patch.object(roads_buildings_alg, "parameterAsSource", return_value=layer)

    parameters = {"POLYGON": "test_null"}
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    with pytest.raises(QgsProcessingException, match="The extent of the extraction area is null"):

        roads_buildings_alg.processAlgorithm(parameters, context, feedback)


def test_osm_roads_buildings(qgis_processing, mocker, tmp_path):
    """
    Mock the osm request
    """
    mocker.patch("ELAN.utils.tr.PlgLogger")
    import processing

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()

    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test_osm", "memory")
    provider = layer.dataProvider()

    feat = QgsFeature()
    geom = QgsGeometry.fromWkt("POLYGON((0 0, 0.2 0, 0.2 0.2, 0 0.2, 0 0))")
    feat.setGeometry(geom)
    provider.addFeatures([feat])
    layer.updateExtents()
    parameters = {
        "POLYGON": "test_osm",
        "BUILDINGS_OUTPUT": "memory:",
        "CENTROID_BUILDINGS_OUTPUT": "memory:",
        "MERGED_BUILDINGS_OUTPUT": "memory:",
        "CENTROID_MERGED_BUILDINGS_OUTPUT": "memory:",
        "ROADS_OUTPUT": "memory:",
    }
    mocker.patch.object(roads_buildings_alg, "parameterAsSource", return_value=layer)
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    osm_roads_buildings = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "osm_roads_buildings.json"
    mock_response = mocker.Mock()

    mock_response.json.return_value = json.loads(osm_roads_buildings.read_text())
    mocker.patch("requests.get", return_value=mock_response)

    result = roads_buildings_alg.processAlgorithm(parameters, context, feedback)
    expected_keys = {
        "BUILDINGS_OUTPUT",
        "CENTROID_BUILDINGS_OUTPUT",
        "MERGED_BUILDINGS_OUTPUT",
        "CENTROID_MERGED_BUILDINGS_OUTPUT",
        "ROADS_OUTPUT",
    }
    for key in expected_keys:
        assert key in result
