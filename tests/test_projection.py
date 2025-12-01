"""
test_projection
"""

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_projection(elan_processing, tmp_path):
    from ELAN.processing.projection import SnapOnRoadsAlgorithm

    test_data_dir_projection = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "projection"
    test_projection_alg = SnapOnRoadsAlgorithm()
    assert test_projection_alg.name() == "elansnaponroads"
    assert test_projection_alg.groupId() == "elanpreprocessings"

    projection_param = {
        "ROADS_INPUT_DATA": str(test_data_dir_projection / "projection_roads_input.gpkg.zip"),
        "BUILDINGS_INPUT_DATA": str(test_data_dir_projection / "projection_buildings_input.gpkg.zip"),
        "POPULATION_FIELD": "population",
        "MAX_DISTANCE_TO_ROAD": 1000,
        "OUTPUT_AGGREGATED": str(tmp_path / "projection_centroids_generated_output.gpkg"),
        "OUTPUT_LINES": str(tmp_path / "projection_lines_generated_output.gpkg"),
    }

    res = elan_processing.run(test_projection_alg, projection_param)
    assert res != {}
    ref_path = str(test_data_dir_projection / "projection_reference_output.gpkg.zip")
    gen_centroids_path = str(tmp_path / "projection_centroids_generated_output.gpkg")
    gen_lines_path = str(tmp_path / "projection_lines_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "projection_centroids_reference_output"),
        load_layer(gen_centroids_path, "projection_centroids_generated_output"),
    )
    assert_same_layers(
        load_layer(ref_path, "projection_lines_reference_output"),
        load_layer(gen_lines_path, "projection_lines_generated_output"),
    )
