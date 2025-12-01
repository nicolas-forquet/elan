"""
test_snap_on_roads
"""

# pylint: disable=import-outside-toplevel, invalid-name

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_snap_on_roads(elan_processing, tmp_path):
    """Test snap on roads processing"""

    from ELAN.processing.snap_on_roads import SnapOnRoadsAlgorithm

    test_data_dir_snap_on_roads = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "snap_on_roads"
    test_snap_on_roads_alg = SnapOnRoadsAlgorithm()
    assert test_snap_on_roads_alg.name() == "elansnaponroads"
    assert test_snap_on_roads_alg.groupId() == "elanpreprocessings"

    snap_on_roads_param = {
        "ROADS_INPUT_DATA": str(test_data_dir_snap_on_roads / "snap_on_roads_roads_input.gpkg.zip"),
        "BUILDINGS_INPUT_DATA": str(test_data_dir_snap_on_roads / "snap_on_roads_buildings_input.gpkg.zip"),
        "POPULATION_FIELD": "population",
        "MAX_DISTANCE_TO_ROAD": 1000,
        "OUTPUT_AGGREGATED": str(tmp_path / "snap_on_roads_centroids_generated_output.gpkg"),
        "OUTPUT_LINES": str(tmp_path / "snap_on_roads_lines_generated_output.gpkg"),
    }

    res = elan_processing.run(test_snap_on_roads_alg, snap_on_roads_param)
    assert res != {}
    ref_path = str(test_data_dir_snap_on_roads / "snap_on_roads_reference_output.gpkg.zip")
    gen_centroids_path = str(tmp_path / "snap_on_roads_centroids_generated_output.gpkg")
    gen_lines_path = str(tmp_path / "snap_on_roads_lines_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "snap_on_roads_centroids_reference_output"),
        load_layer(gen_centroids_path, "snap_on_roads_centroids_generated_output"),
    )
    assert_same_layers(
        load_layer(ref_path, "snap_on_roads_lines_reference_output"),
        load_layer(gen_lines_path, "snap_on_roads_lines_generated_output"),
    )
