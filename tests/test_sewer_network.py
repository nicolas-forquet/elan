"""
test_sewer_network
"""

import re
from pathlib import Path

import pytest
from qgis.core import (
    NULL,
    QgsField,
    QgsFields,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsRasterLayer,
)

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


def test_error_NULL_population_fields(qgis_processing, mocker, tmp_path):
    """
    Verify the raised errors:

    - Building layer : population fields NULL
    - DEM layer : File with 2 bands

    """
    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations

    test_sewer_network_alg = SewerNetworkAlgorithm()

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    # # mock DEM_layer with crs and band value
    mock_layer_dem = mocker.Mock(spec=QgsRasterLayer)
    mock_layer_dem.bandCount.return_value = 1
    mock_layer_dem.crs.return_value = "32620"

    # mock buildings_layer with crs and field "population"
    mock_layer_buildings_source = mocker.Mock()
    mock_layer_buildings_source.crs.return_value = "32620"

    fields = QgsFields()
    fields.append(QgsField("population", 0))
    mock_layer_buildings_source.fields.return_value = fields
    mock_layer_buildings_source.uniqueValues.return_value = {NULL}  # return QgsFeature.attributes() NULL

    mocker.patch.object(test_sewer_network_alg, "parameterAsSource", return_value=mock_layer_buildings_source)
    mocker.patch.object(test_sewer_network_alg, "parameterAsRasterLayer", return_value=mock_layer_dem)

    parameters = {
        "BUILDINGS_INPUT_DATA": mock_layer_buildings_source,
        "DEM_FILE_PATH": mock_layer_dem,
        "INHABITANTS_DWELLING_ATTRIBUTE_NAME": "population",
        "OUTPUT_GPKG": "memory:",
    }

    with pytest.raises(QgsProcessingException, match=re.compile("There is one or more NULL values in the field")):
        test_sewer_network_alg.processAlgorithm(parameters, context, feedback)


def test_error_2bands_dem(qgis_processing, mocker, tmp_path):
    """
    Verify the raised errors:

    - Building layer : population fields NULL
    - DEM layer : File with 2 bands

    """
    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    mocker.patch("ELAN.utils.tr.PlgLogger")

    test_sewer_network_alg = SewerNetworkAlgorithm()

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    mock_layer_dem = mocker.Mock(spec=QgsRasterLayer)
    mock_layer_dem.bandCount.return_value = 2
    mock_layer_dem.crs.return_value = "32620"

    # mock buildings_layer with crs and field "population"
    mock_layer_buildings_source = mocker.Mock()
    mock_layer_buildings_source.crs.return_value = "32620"
    mocker.patch.object(test_sewer_network_alg, "parameterAsSource", return_value=mock_layer_buildings_source)

    mocker.patch.object(test_sewer_network_alg, "parameterAsRasterLayer", return_value=mock_layer_dem)
    parameters = {
        "BUILDINGS_INPUT_DATA": mock_layer_buildings_source,
        "DEM_FILE_PATH": mock_layer_dem,
        "INHABITANTS_DWELLING_ATTRIBUTE_NAME": "population",
        "OUTPUT_GPKG": "memory:",
    }

    with pytest.raises(
        QgsProcessingException, match=re.compile(r"The DEM must have a single band \(2 band\(s\) found\)")
    ):
        test_sewer_network_alg.processAlgorithm(parameters, context, feedback)
