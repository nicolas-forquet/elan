"""
test_population
"""

from pathlib import Path

from qgis.core import QgsApplication, QgsVectorLayer
from qgis.gui import QgisInterface

DIR_PLUGIN_ROOT = Path(__file__).parent


def test_population(qgis_processing, mocker):
    mocker.patch("ELAN.toolbelt.log_handler.iface", spec=QgisInterface)
    import processing

    from ELAN.processing.provider import ELANProvider

    provider = ELANProvider()
    if (registry := QgsApplication.processingRegistry()) is None:
        raise RuntimeError("Processing registry not found")
    registry.addProvider(provider)

    population_param = {
        'INPUT_POPULATION_TOT':1100,
        "INPUT_POLYGON_LAYER": f"{DIR_PLUGIN_ROOT}/data_test/population/population_input.gpkg.zip",
        "OUPUT_CENTROIDES_LAYER": f"{DIR_PLUGIN_ROOT}/data_test/population/population_generated_output.gpkg",
    }
    processing.run("elan:elanpopulation", population_param)

    ref_path = f"{DIR_PLUGIN_ROOT}/data_test/population/population_reference_output.gpkg.zip"
    gen_path = f"{DIR_PLUGIN_ROOT}/data_test/population/population_generated_output.gpkg"

    uri_ref = f"{ref_path}|layername=population_reference_output"
    layer_ref = QgsVectorLayer(uri_ref, "population_reference_output", "ogr")
    uri_gen = f"{gen_path}|layername=population_generated_output"
    layer_gen = QgsVectorLayer(uri_gen, "population_generated_output", "ogr")

    assert layer_gen.isValid()
    assert layer_ref.isValid()

    assert layer_ref.featureCount() == layer_gen.featureCount()
    assert [field.name() for field in layer_ref.fields()] == [field.name() for field in layer_gen.fields()]



 