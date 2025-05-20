"""
test_sewer_network
"""

from pathlib import Path

from tests.utils import assert_same_layers, load_layer

DIR_PLUGIN_ROOT = Path(__file__).parent


def test_sewer_network(qgis_processing, mocker, tmp_path):

    import processing

    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations

    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "sewer_network"
    test_sewer_network_alg = SewerNetworkAlgorithm()
    assert test_sewer_network_alg.name() == "elansewernetwork"
    assert test_sewer_network_alg.groupId() == "elanprocessings"

    sinks_path = f"{test_data_dir}/sewer_network_steu_input.gpkg.zip"
    dem_file_path = f"{test_data_dir}/sewer_network_mnt_input.tif"
    roads_input_path = f"{test_data_dir}/sewer_network_roads_input.gpkg.zip"
    buildings_input_path = f"{test_data_dir}/sewer_network_buildings_population_input.gpkg.zip"
    sewer_network_param = {
        "SINKS": sinks_path,
        "OUTPUT_GPKG": f"{tmp_path}/sewer_network_generated_output.gpkg",
        "DEM_FILE_PATH": dem_file_path,
        "ROADS_INPUT_DATA": roads_input_path,
        "BUILDINGS_INPUT_DATA": buildings_input_path,
        "INHABITANTS_DWELLING_ATTRIBUTE_NAME": "population",
        "PUMP_PENALTY": 1000,
        "MAX_CONNECTION_LENGTH": 30,
        "CLUSTERING": "None",
        "DEFAULT_INHABITANTS_DWELLING": 3,
        "DAILY_WASTEWATER_PERSON": 0.164,
        "PEAK_FACTOR": 2.3,
        "MIN_SLOPE": -0.01,
        "TMAX": 8,
        "TMIN": 0.25,
        "INFLOW_TRENCH_DEPTH": 0,
        "MIN_TRENCH_DEPTH": 0,
        "ROUGHNESS": 0.13,
        "PRESSURIZED_DIAMETER": 0.2,
        "DIAMETERS": [0, 1, 2, 3, 4, 5],
    }

    res = processing.run(test_sewer_network_alg, sewer_network_param)
    assert res != {}

    ref_path = f"{test_data_dir}/sewer_network_reference_output.gpkg.zip"
    gen_path = f"{tmp_path}/sewer_network_generated_output.gpkg"

    layers = ["pumping_stations", "lifting_stations", "sewer_pipes"]

    for name in layers:
        assert_same_layers(load_layer(ref_path, name), load_layer(gen_path, name))
