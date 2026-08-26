"""
test_grouping
"""

# pylint: disable=import-outside-toplevel, invalid-name

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_grouping(elan_processing, tmp_path):
    """Test grouping processing"""

    from ELAN.processing.grouping import GroupingAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "grouping"
    test_grouping_alg = GroupingAlgorithm()
    assert test_grouping_alg.name() == "elangrouping"
    assert test_grouping_alg.groupId() == "elanpreprocessings"

    grouping_params = {
        "ROADS": str(test_data_dir / "grouping_inputs.gpkg.zip|layername=roads"),
        "BUILDINGS_CENTROIDS": str(test_data_dir / "grouping_inputs.gpkg.zip|layername=building_centroids"),
        "POPULATION_ATTRIBUTE_NAME": "population",
        "ADJUSTMENT_FACTOR": 28.5,
        "OUTPUT_GPKG": str(tmp_path / "grouping_generated_output.gpkg"),
    }

    res = elan_processing.run(test_grouping_alg, grouping_params)
    assert res != {}

    ref_path = str(test_data_dir / "grouping_reference_output.gpkg.zip")
    gen_path = str(tmp_path / "grouping_generated_output.gpkg")
    layers = ["grouped_buildings", "grouped_roads", "buffered_centroids"]

    for name in layers:
        assert_same_layers(load_layer(ref_path, name), load_layer(gen_path, name))
