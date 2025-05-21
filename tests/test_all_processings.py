"""
test_all_processings
"""

from pathlib import Path

from qgis.core import QgsCoordinateReferenceSystem, QgsProject

from ELAN.__about__ import DIR_PLUGIN_ROOT

DIR_PLUGIN_ROOT = Path(__file__).parent


def test_all_processings(qgis_processing, mocker, tmp_path):

    ########################## Roads and Buildings #####################################################

    import processing

    from ELAN.processing.provider import (
        PopulationAlgorithm,
        RoadsBuildingsAlgorithm,
        SewerNetworkAlgorithm,
        TrenchProfileAlgorithm,
    )

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:32620"))
    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_alg = RoadsBuildingsAlgorithm()
    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "CENTROID_BUILDINGS_OUTPUT": str(tmp_path / "buildings_centroids_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "CENTROID_MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_centroids_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
        "PROJ": True,
    }

    res = processing.run(roads_buildings_alg, roads_buildings_param)
    assert res != {}

    ########################## Population #####################################################

    test_population_alg = PopulationAlgorithm()
    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "population"

    population_param = {
        "INPUT_POPULATION_TOT": 1100,
        "INPUT_POLYGON_LAYER": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "OUPUT_CENTROIDES_LAYER": str(tmp_path / "population_generated_output.gpkg"),
    }
    res = processing.run(test_population_alg, population_param)

    ########################## Sewer Network #####################################################

    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "sewer_network"
    test_sewer_network_alg = SewerNetworkAlgorithm()

    sinks_path = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "processings" / "sewer_network_steu.gpkg"
    dem_file_path = f"{test_data_dir}/sewer_network_mnt_input.tif"
    roads_input_path = f"{tmp_path}/roads_generated_output.gpkg"
    buildings_input_path = f"{tmp_path}/population_generated_output.gpkg"

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

    ########################## Trench Profile #####################################################

    trench_profile_alg = TrenchProfileAlgorithm()
    test_data_dir = Path(DIR_PLUGIN_ROOT).parent / "tests" / "data_test" / "trench_profile"

    trench_profile_param = {
        "INPUT_LAYER": str(tmp_path / "sewer_network_generated_output.gpkg|layername=sewer_pipes"),
        "OUTPUT_GPKG": str(tmp_path / "trench_profile_generated_output.gpkg"),
    }
    res = processing.run(trench_profile_alg, trench_profile_param)
