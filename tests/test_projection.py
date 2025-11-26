"""
test_projection
"""

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_projection(elan_processing, tmp_path):
    from ELAN.processing.projection import SnapOnRoadsAlgorithm

    test_data_dir_projection = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "projection"
    test_data_roads_buildings = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    test_data_population = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "population"

    test_projection_alg = SnapOnRoadsAlgorithm()
    assert test_projection_alg.name() == "elansnaponroads"
    assert test_projection_alg.groupId() == "elanpreprocessings"
    population_building = load_layer(
        str(test_data_population / "population_reference_output.gpkg"), "population_reference_output"
    )
    roads = load_layer(str(test_data_roads_buildings / "roads_buildings_output.gpkg.zip"), "roads_reference_output")

    projection_param = {
        "ROADS_INPUT_DATA": roads,
        "BUILDINGS_INPUT_DATA": population_building,
        "POPULATION_FIELD": "population",
        "MAX_DISTANCE_TO_ROAD": 1000,
        "OUTPUT_AGGREGATED": str(tmp_path / "projection_aggregated_generated_output.gpkg"),
        "OUTPUT_LINES": str(tmp_path / "projection_lines_generated_output.gpkg"),
    }

    res = elan_processing.run(test_projection_alg, projection_param)

    ref_path = str(test_data_dir_projection / "projection_reference.gpkg.zip")
    gen_centroids_path = str(tmp_path / "projection_centroids_generated_output.gpkg.gpkg")

    gen_lines_path = str(tmp_path / "projection_centroids_lines_output.gpkg.gpkg")

    assert_same_layers(
        load_layer(ref_path, "projected_centroids_output"), load_layer(gen_centroids_path, "projected_centroids_output")
    )

    assert_same_layers(
        load_layer(ref_path, "projection_lines_output"), load_layer(gen_lines_path, "projection_lines_output")
    )
