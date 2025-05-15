"""
test_trench_profile
"""

from pathlib import Path

from qgis.core import QgsApplication, QgsVectorLayer
from qgis.gui import QgisInterface

DIR_PLUGIN_ROOT = Path(__file__).parent


def test_trench_profile(qgis_processing, mocker):
    mocker.patch("ELAN.toolbelt.log_handler.iface", spec=QgisInterface)
    import processing

    from ELAN.processing.provider import ELANProvider

    provider = ELANProvider()
    if (registry := QgsApplication.processingRegistry()) is None:
        raise RuntimeError("Processing registry not found")
    registry.addProvider(provider)

    trench_profile_param = {
        "INPUT_LAYER": f"{DIR_PLUGIN_ROOT}/data_test/trench_profile/trench_profile_input.gpkg.zip",
        "OUTPUT_LAYER": f"{DIR_PLUGIN_ROOT}/data_test/trench_profile/trench_profile_generated_output.gpkg",
    }

    processing.run("elan:elantrenchprofile", trench_profile_param)
    ref_path = f"{DIR_PLUGIN_ROOT}/data_test/trench_profile/trench_profile_reference_output.gpkg.zip"
    gen_path = f"{DIR_PLUGIN_ROOT}/data_test/trench_profile/trench_profile_generated_output.gpkg"
    layers = ["sewer_profile", "land_profile", "3D_pipes"]

    for name in layers:
        ref_layer = load_layer(ref_path, name)
        generated_layer = load_layer(gen_path, name)

        assert ref_layer.featureCount() == generated_layer.featureCount()
        assert [field.name() for field in ref_layer.fields()] == [field.name() for field in generated_layer.fields()]


def load_layer(gpkg_path, layer_name):
    uri = f"{gpkg_path}|layername={layer_name}"
    layer = QgsVectorLayer(uri, layer_name, "ogr")
    assert layer.isValid()
    return layer
