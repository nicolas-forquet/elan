"""
test_sewer_network
"""

from pathlib import Path

from qgis.core import QgsApplication, QgsVectorLayer
from qgis.gui import QgisInterface

DIR_PLUGIN_ROOT = Path(__file__).parent


def load_layer(gpkg_path, layer_name):
    uri = f"{gpkg_path}|layername={layer_name}"
    layer = QgsVectorLayer(uri, layer_name, "ogr")
    assert layer.isValid(), f"Layer {layer_name} could not be loaded from {gpkg_path}"
    return layer


def test_sewer_network(qgis_processing, mocker):

    mocker.patch("ELAN.toolbelt.log_handler.iface", spec=QgisInterface)

    import processing

    from ELAN.processing.provider import ELANProvider

    provider = ELANProvider()
    if (registry := QgsApplication.processingRegistry()) is None:
        raise RuntimeError("Processing registry not found")
    registry.addProvider(provider)

    sinks_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_steu_input.gpkg"
    dem_file_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_mnt_input.tif"
    roads_input_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_roads_input.gpkg"
    buildings_input_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_input_buildings_pop_input.gpkg"
    sewer_network_param = {
        "SINKS": sinks_path,
        "OUTPUT_LAYER": f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_generated_output.gpkg",
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

    processing.run("elan:elansewernetwork", sewer_network_param)

    ref_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_reference_output.gpkg"
    gen_path = f"{DIR_PLUGIN_ROOT}/data_test/sewer_network/sewer_network_generated_output.gpkg"

    layers = ["pumping_stations", "lifting_stations", "sewer_pipes", "info_network"]

    for name in layers:
        ref_layer = load_layer(ref_path, name)
        generated_layer = load_layer(gen_path, name)

        assert ref_layer.featureCount() == generated_layer.featureCount()
        assert [field.name() for field in ref_layer.fields()] == [field.name() for field in generated_layer.fields()]
