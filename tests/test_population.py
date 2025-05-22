"""
test_population
"""

from pathlib import Path

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_population(qgis_processing, mocker, tmp_path):
    import processing

    from ELAN.processing.population import PopulationAlgorithm

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations
    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "population"

    test_population_alg = PopulationAlgorithm()
    assert test_population_alg.name() == "elanpopulation"
    assert test_population_alg.groupId() == "elanpreprocessings"

    population_param = {
        "INPUT_POPULATION_TOT": 1100,
        "INPUT_POLYGON_LAYER": str(test_data_dir / "population_input.gpkg.zip"),
        "OUPUT_CENTROIDES_LAYER": str(tmp_path / "population_generated_output.gpkg"),
    }
    res = processing.run(test_population_alg, population_param)
    assert res != {}

    ref_path = str(test_data_dir / "population_reference_output.gpkg.zip")
    gen_path = str(tmp_path / "population_generated_output.gpkg")

    assert_same_layers(
        load_layer(ref_path, "population_reference_output"), load_layer(gen_path, "population_generated_output")
    )
