"""
test_population
"""

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_population(elan_processing, tmp_path):
    from ELAN.processing.population import PopulationAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "population"

    test_population_alg = PopulationAlgorithm()
    assert test_population_alg.name() == "elanpopulation"
    assert test_population_alg.groupId() == "elanpreprocessings"

    population_param = {
        "INPUT_POPULATION_TOT": 1100,
        "INPUT_POLYGON_LAYER": str(test_data_dir / "population_input.gpkg.zip"),
        "OUTPUT_CENTROIDES_LAYER": str(tmp_path / "population_generated_output.gpkg"),
    }
    res = elan_processing.run(test_population_alg, population_param)
    assert list(res.keys()) == ["OUTPUT_CENTROIDES_LAYER"]

    ref_path = str(test_data_dir / "population_reference_output.gpkg.zip")
    gen_path = str(tmp_path / "population_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "population_reference_output"), load_layer(gen_path, "population_generated_output")
    )
