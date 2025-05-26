"""
test_trench_profile
"""

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_trench_profile(elan_processing, tmp_path):

    from ELAN.processing.trench_profile import TrenchProfileAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "trench_profile"

    trench_profile_alg = TrenchProfileAlgorithm()
    assert trench_profile_alg.name() == "elantrenchprofile"
    assert trench_profile_alg.groupId() == "results_exploration"

    trench_profile_param = {
        "INPUT_LAYER": str(test_data_dir / "trench_profile_input.gpkg.zip"),
        "OUTPUT_GPKG": str(tmp_path / "trench_profile_generated_output.gpkg"),
    }

    res = elan_processing.run(trench_profile_alg, trench_profile_param)
    assert res == {}

    ref_path = str(test_data_dir / "trench_profile_reference_output.gpkg.zip")
    gen_path = str(tmp_path / "trench_profile_generated_output.gpkg")
    layers = ["sewer_profile", "land_profile", "3D_pipes"]

    for name in layers:
        assert_same_layers(load_layer(ref_path, name), load_layer(gen_path, name))
