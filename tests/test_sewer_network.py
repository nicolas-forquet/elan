"""
test_sewer_network
"""

# pylint: disable=import-outside-toplevel, invalid-name

import re

import pytest
from qgis.core import (
    NULL,
    QgsGeometry,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_sewer_network(elan_processing, tmp_path):

    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network"
    test_sewer_network_alg = SewerNetworkAlgorithm()
    assert test_sewer_network_alg.name() == "elansewernetwork"
    assert test_sewer_network_alg.groupId() == "elanprocessings"

    sewer_network_param = {
        "SINKS": str(test_data_dir / "sewer_network_steu_input.gpkg.zip"),
        "OUTPUT_GPKG": str(tmp_path / "sewer_network_generated_output.gpkg"),
        "DEM_FILE_PATH": str(test_data_dir / "sewer_network_mnt_input.tif"),
        "ROADS_INPUT_DATA": str(test_data_dir / "sewer_network_roads_input.gpkg.zip"),
        "BUILDINGS_INPUT_DATA": str(test_data_dir / "sewer_network_buildings_population_input.gpkg.zip"),
        "POPULATION_ATTRIBUTE_NAME": "population",
        "PUMP_PENALTY": 1000,
        "MAX_CONNECTION_LENGTH": 30,
        "CLUSTERING": "None",
        "DAILY_WASTEWATER_PERSON": 0.164,
        "PEAK_FACTOR": 2.3,
        "MIN_SLOPE": -0.01,
        "TMAX": 8,
        "TMIN": 0.25,
        "ROUGHNESS": 0.13,
        "PRESSURIZED_DIAMETER": 0.2,
        "DIAMETERS": [0, 1, 2, 3, 4, 5],
    }

    res = elan_processing.run(test_sewer_network_alg, sewer_network_param)
    assert list(res.keys()) == ["OUTPUT_GPKG"]

    ref_path = test_data_dir / "sewer_network_reference_output.gpkg.zip"
    gen_path = tmp_path / "sewer_network_generated_output.gpkg"

    layers = ["pumping_stations", "lifting_stations", "sewer_pipes", "roads", "buildings", "sinks_layer"]

    for name in layers:
        assert_same_layers(load_layer(ref_path, name), load_layer(gen_path, name))


def test_sewer_network_with_empty_outputs(elan_processing, tmp_path):
    """
    We don't put any building feature in the input buildings layer
    so that no pump is created, only one sewer, and we must have
    no error but empty output layers with their structure (fields)
    """

    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network"
    test_sewer_network_alg = SewerNetworkAlgorithm()
    assert test_sewer_network_alg.name() == "elansewernetwork"
    assert test_sewer_network_alg.groupId() == "elanprocessings"

    sewer_network_param = {
        "SINKS": None,
        "OUTPUT_GPKG": str(tmp_path / "sewer_network_generated_output.gpkg"),
        "DEM_FILE_PATH": str(test_data_dir / "sewer_network_mnt_no_output.tif"),
        "ROADS_INPUT_DATA": str(test_data_dir / "sewer_network_roads_no_output.gpkg.zip"),
        "BUILDINGS_INPUT_DATA": str(test_data_dir / "sewer_network_buildings_empty.gpkg.zip"),
        "POPULATION_ATTRIBUTE_NAME": "population",
        "PUMP_PENALTY": 1000,
        "MAX_CONNECTION_LENGTH": 30,
        "CLUSTERING": "None",
        "DAILY_WASTEWATER_PERSON": 0.164,
        "PEAK_FACTOR": 2.3,
        "MIN_SLOPE": -0.01,
        "TMAX": 8,
        "TMIN": 0.25,
        "ROUGHNESS": 0.13,
        "PRESSURIZED_DIAMETER": 0.2,
        "DIAMETERS": [0, 1, 2, 3, 4, 5],
    }

    res = elan_processing.run(test_sewer_network_alg, sewer_network_param)
    assert list(res.keys()) == ["OUTPUT_GPKG"]

    ref_path = test_data_dir / "sewer_network_reference_output_with_empty_outputs.gpkg.zip"
    gen_path = tmp_path / "sewer_network_generated_output.gpkg"

    layers = ["pumping_stations", "lifting_stations", "sewer_pipes", "roads", "buildings", "sinks_layer"]

    for name in layers:
        assert_same_layers(load_layer(ref_path, name), load_layer(gen_path, name))


def test_error_null_population_fields(elan_processing):
    """
    Verify the raised error:
    - Building layer : population field with a NULL value
    """

    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    test_sewer_network_alg = SewerNetworkAlgorithm()

    # Create buildings layer
    buildings_layer = QgsVectorLayer(
        "Polygon?crs=EPSG:4326&field=population:double", "test_null_population_fields", "memory"
    )
    if (provider := buildings_layer.dataProvider()) is None:
        raise RuntimeError("Unexpected error: layer provider is None")
    # Add 2 features, one with NULL population value
    provider.addFeatures(
        [
            QgsVectorLayerUtils.createFeature(buildings_layer, QgsGeometry(), {0: NULL}),
            QgsVectorLayerUtils.createFeature(buildings_layer, QgsGeometry(), {0: 4.56}),
        ]
    )

    parameters = {
        "BUILDINGS_INPUT_DATA": buildings_layer,
        "ROADS_INPUT_DATA": QgsVectorLayer("Line?crs=EPSG:32620", "roads", "memory"),
        "DEM_FILE_PATH": str(
            DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network" / "sewer_network_mnt_input.tif"
        ),
        "POPULATION_ATTRIBUTE_NAME": "population",
        "OUTPUT_GPKG": "memory:",
    }

    with pytest.raises(
        QgsProcessingException, match=re.compile("There is one or more NULL values in the field population")
    ):
        elan_processing.run(test_sewer_network_alg, parameters)


def test_error_2bands_dem(mocker):
    """
    Verify the raised error:
    - DEM layer : File with 2 bands
    """

    from ELAN.processing.sewer_network import SewerNetworkAlgorithm

    mocker.patch("ELAN.utils.tr.PlgLogger")

    test_sewer_network_alg = SewerNetworkAlgorithm()

    mock_layer_dem = mocker.Mock(spec=QgsRasterLayer)
    mock_layer_dem.bandCount.return_value = 2

    # mock buildings_layer with crs and field "population"
    mocker.patch.object(test_sewer_network_alg, "parameterAsSource")
    mocker.patch.object(test_sewer_network_alg, "parameterAsRasterLayer", return_value=mock_layer_dem)

    with pytest.raises(
        QgsProcessingException, match=re.compile(r"The DEM must have a single band \(2 band\(s\) found\)")
    ):
        test_sewer_network_alg.processAlgorithm({}, QgsProcessingContext(), QgsProcessingFeedback())
