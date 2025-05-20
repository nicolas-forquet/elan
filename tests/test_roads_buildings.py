"""
test_roads_buildings
"""

from pathlib import Path

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
