"""
test_population
"""

# pylint: disable=import-outside-toplevel, invalid-name

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_population_areametric(elan_processing, tmp_path):
    """
    Test the population areametric distribution processing
    """

    from ELAN.processing.population import PopulationAreametricAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "population"

    test_population_alg = PopulationAreametricAlgorithm()
    assert test_population_alg.name() == "elanpopulationareametric"
    assert test_population_alg.groupId() == "elanpreprocessings"

    population_param = {
        "INPUT_POPULATION_TOT": 1100,
        "INPUT_POLYGON_LAYER": str(test_data_dir / "population_input.gpkg.zip"),
        "OUTPUT_CENTROIDES_LAYER": str(tmp_path / "population_generated_output.gpkg"),
    }
    res = elan_processing.run(test_population_alg, population_param)
    assert list(res.keys()) == ["OUTPUT_CENTROIDES_LAYER"]

    ref_path = str(test_data_dir / "population_reference_output_areametric.gpkg.zip")
    gen_path = str(tmp_path / "population_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "population_reference_output"), load_layer(gen_path, "population_generated_output")
    )


def test_population_uniform(elan_processing, tmp_path):
    """
    Test the population uniform distribution processing
    """

    from ELAN.processing.population import PopulationUniformAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "population"

    test_population_alg = PopulationUniformAlgorithm()
    assert test_population_alg.name() == "elanpopulationuniform"
    assert test_population_alg.groupId() == "elanpreprocessings"

    population_param = {
        "INPUT_POPULATION": 10.53,
        "INPUT": str(test_data_dir / "population_input.gpkg.zip"),
        "OUTPUT": str(tmp_path / "population_generated_output.gpkg"),
    }
    res = elan_processing.run(test_population_alg, population_param)
    assert list(res.keys()) == ["OUTPUT"]

    ref_path = str(test_data_dir / "population_reference_output_uniform.gpkg.zip")
    gen_path = str(tmp_path / "population_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "population_reference_output"), load_layer(gen_path, "population_generated_output")
    )
