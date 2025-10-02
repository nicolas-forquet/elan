"""
Test treatment train plot script
"""

from unittest.mock import Mock

from qgis.core import QgsVectorLayer

from ELAN.__about__ import DIR_PLUGIN_ROOT
from ELAN.scripts.treatment_train_plot import ProcessPlots
from tests.utils import load_layer


def test_get_active_layer(mocker):
    """
    Test the get_active_layer method
    """

    # First layer is a real treatment train layer
    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    treatment_train_layer = load_layer(test_data_dir / "wetland_process_reference_output.gpkg.zip", "couche_de_filires")

    # Second layer to test is not a treatment train layer, some fields are missing
    error_layer = QgsVectorLayer(
        "Point?crs=EPSG:4326"
        "&field=ecoli_norm:string(255,0)"
        "&field=TSS_loading_stages:string(255,0)"
        "&field=TN_norm:string(255,0)"
        "&field=TKN_loading_stages:string(255,0)",
        "error_layer",
        "memory",
    )
    assert error_layer.isValid()

    # iface mock will give the first and the second layer when activeLayer() will be called
    iface_mock = mocker.patch("ELAN.scripts.treatment_train_plot.iface")
    iface_mock.activeLayer.side_effect = [treatment_train_layer, error_layer]

    # qmessagebox mock will avoid showing a popup and stuck the test
    qmessagebox_mock: Mock = mocker.patch("ELAN.scripts.treatment_train_plot.QMessageBox")

    plots = ProcessPlots()

    # Test the first layer which is ok
    assert plots.get_active_layer() == treatment_train_layer

    # Test the second layer which is not ok
    assert plots.get_active_layer() is None
    qmessagebox_mock.warning.assert_called_once_with(
        None,
        "Warning",
        "The active layer is not a treatment train layer.\n"
        "Missing fields: 'BOD5_loading_stages', 'BOD5_norm', 'COD_loading_stages', 'COD_norm', "
        "'NO3N_norm', 'TKN_norm', 'TP_norm', 'TSS_norm', 'hydraulic_loading_rate_stages', 'surface_norm'",
    )


def test_validate_and_get_metadata(mocker):
    """
    Test the validate_and_get_metadata method
    """

    # First layer is a real treatment train layer
    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    treatment_train_layer = load_layer(test_data_dir / "wetland_process_reference_output.gpkg.zip", "couche_de_filires")

    # qmessagebox mock will avoid showing a popup and stuck the test
    qmessagebox_mock: Mock = mocker.patch("ELAN.scripts.treatment_train_plot.QMessageBox")

    plots = ProcessPlots()

    # First test which is not ok because there are 2 WWTP and no feature selected
    assert not plots.validate_and_get_metadata(treatment_train_layer)[0]
    qmessagebox_mock.warning.assert_called_once_with(
        None,
        "Warning",
        "Features have different coordonnées gps.\nSelect only features with the same coordonnées gps.",
    )

    # Select 6 treatment trains having similar sink_coords field
    treatment_train_layer.selectByExpression('"fid" > 6')
    assert treatment_train_layer.selectedFeatureCount() == 6
    assert plots.validate_and_get_metadata(treatment_train_layer) == (
        True,  # layer is valid
        3,  # 3 stages max
        [
            "TSS_norm",
            "BOD5_norm",
            "TKN_norm",
            "COD_norm",
            "NO3N_norm",
            "TN_norm",
            "TP_norm",
        ],  # list of normalized fields without null value
    )
    qmessagebox_mock.warning.assert_called_once()  # no more warning generated
