"""
test_wetland_process
"""

# pylint: disable=import-outside-toplevel, invalid-name

import re

import pytest
from qgis.core import QgsProcessingException

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


def test_wetland_process(elan_processing, tmp_path):
    """Test wetland process with all inputs"""

    from ELAN.processing.wetland_process import WetlandProcessAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    test_wetland_process_alg = WetlandProcessAlgorithm()
    assert test_wetland_process_alg.name() == "elanwetlandprocess"
    assert test_wetland_process_alg.groupId() == "elanprocessings"

    wetland_process_param = {
        "CLIMATE": 0,
        "TREATMENT": str(tmp_path / "wetland_process_generated_output.gpkg"),
        "SINKS": str(test_data_dir / "wetland_process_steu_input.gpkg.zip"),
        "AVAILABLE_SURFACE": str(test_data_dir / "wetland_process_surface_input.gpkg.zip"),
        "SINK_COORDS": "sink_coords",
        "STAGES_MAX": 3,
        "TSS_OBJ": "TSS_obj",
        "BOD5_OBJ": "BOD5_obj",
        "TKN_OBJ": "TKN_obj",
        "COD_OBJ": "COD_obj",
        "NO3N_OBJ": "NO3N_obj",
        "TN_OBJ": "TN_obj",
        "TP_OBJ": "TP_obj",
        "ECOLI_OBJ": "ecoli_obj",
        "Q_FIELD": "average_daily_flow",
    }

    res = elan_processing.run(test_wetland_process_alg, wetland_process_param)
    assert list(res.keys()) == ["TREATMENT"]

    ref_path = test_data_dir / "wetland_process_reference_output.gpkg.zip"
    gen_path = tmp_path / "wetland_process_generated_output.gpkg"

    assert_same_layers(
        load_layer(ref_path, "couche_de_filires"),
        load_layer(gen_path, "wetland_process_generated_output"),
        check_values_only_on_fields=["fid", "sink_coords", "pathway_id", "available_surface", "name_stages"],
    )


def test_wetland_process_without_surface(elan_processing, tmp_path):
    """Test wetland process without surface input layer"""

    from ELAN.processing.wetland_process import WetlandProcessAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    test_wetland_process_alg = WetlandProcessAlgorithm()
    assert test_wetland_process_alg.name() == "elanwetlandprocess"
    assert test_wetland_process_alg.groupId() == "elanprocessings"

    wetland_process_param = {
        "CLIMATE": 0,
        "TREATMENT": str(tmp_path / "wetland_process_generated_output.gpkg"),
        "SINKS": str(test_data_dir / "wetland_process_steu_input.gpkg.zip"),
        "AVAILABLE_SURFACE": None,
        "SINK_COORDS": "sink_coords",
        "STAGES_MAX": 3,
        "TSS_OBJ": "TSS_obj",
        "BOD5_OBJ": "BOD5_obj",
        "TKN_OBJ": "TKN_obj",
        "COD_OBJ": "COD_obj",
        "NO3N_OBJ": "NO3N_obj",
        "TN_OBJ": "TN_obj",
        "TP_OBJ": "TP_obj",
        "ECOLI_OBJ": "ecoli_obj",
        "Q_FIELD": "average_daily_flow",
    }

    res = elan_processing.run(test_wetland_process_alg, wetland_process_param)
    assert list(res.keys()) == ["TREATMENT"]

    ref_path = test_data_dir / "wetland_process_reference_output_without_surface.gpkg.zip"
    gen_path = tmp_path / "wetland_process_generated_output.gpkg"

    assert_same_layers(
        load_layer(ref_path, "couche_de_filires"),
        load_layer(gen_path, "wetland_process_generated_output"),
        check_values_only_on_fields=["fid", "sink_coords", "pathway_id", "available_surface", "name_stages"],
    )


def test_wetland_process_with_negative_objectives(elan_processing, tmp_path):
    """Test wetland process crashes when negative values are in target concentrations"""

    from ELAN.processing.wetland_process import WetlandProcessAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    test_wetland_process_alg = WetlandProcessAlgorithm()
    assert test_wetland_process_alg.name() == "elanwetlandprocess"
    assert test_wetland_process_alg.groupId() == "elanprocessings"

    wetland_process_param = {
        "CLIMATE": 0,
        "TREATMENT": str(tmp_path / "wetland_process_generated_output.gpkg"),
        "SINKS": str(test_data_dir / "wetland_process_steu_with_negative_input.gpkg.zip"),
        "AVAILABLE_SURFACE": None,
        "SINK_COORDS": "sink_coords",
        "STAGES_MAX": 3,
        "TSS_OBJ": "TSS_obj",
        "BOD5_OBJ": "BOD5_obj",
        "TKN_OBJ": "TKN_obj",
        "COD_OBJ": "COD_obj",
        "NO3N_OBJ": "NO3N_obj",
        "TN_OBJ": "TN_obj",
        "TP_OBJ": "TP_obj",
        "ECOLI_OBJ": "ecoli_obj",
        "Q_FIELD": "average_daily_flow",
    }

    with pytest.raises(QgsProcessingException, match="These target values must be strictly positive: COD, TN"):
        elan_processing.run(test_wetland_process_alg, wetland_process_param)


def test_wetland_process_with_null_objectives(elan_processing, tmp_path):
    """Test wetland process crashes when NULL values are in target concentrations"""

    from ELAN.processing.wetland_process import WetlandProcessAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    test_wetland_process_alg = WetlandProcessAlgorithm()
    assert test_wetland_process_alg.name() == "elanwetlandprocess"
    assert test_wetland_process_alg.groupId() == "elanprocessings"

    wetland_process_param = {
        "CLIMATE": 0,
        "TREATMENT": str(tmp_path / "wetland_process_generated_output.gpkg"),
        "AVAILABLE_SURFACE": None,
        "SINK_COORDS": "sink_coords",
        "STAGES_MAX": 3,
        "TSS_OBJ": "TSS_obj",
        "BOD5_OBJ": "BOD5_obj",
        "TKN_OBJ": "TKN_obj",
        "COD_OBJ": "COD_obj",
        "NO3N_OBJ": "NO3N_obj",
        "TN_OBJ": "TN_obj",
        "TP_OBJ": "TP_obj",
        "ECOLI_OBJ": "ecoli_obj",
        "Q_FIELD": "average_daily_flow",
    }

    wetland_process_param["SINKS"] = str(test_data_dir / "wetland_process_steu_with_null_input_1.gpkg.zip")
    with pytest.raises(QgsProcessingException, match="These target values can't be NULL: COD"):
        elan_processing.run(test_wetland_process_alg, wetland_process_param)

    wetland_process_param["SINKS"] = str(test_data_dir / "wetland_process_steu_with_null_input_2.gpkg.zip")
    with pytest.raises(QgsProcessingException, match="These target values can't be NULL: TSS, BOD5"):
        elan_processing.run(test_wetland_process_alg, wetland_process_param)

    wetland_process_param["SINKS"] = str(test_data_dir / "wetland_process_steu_with_null_input_3.gpkg.zip")

    # Authorized NULL values
    res = elan_processing.run(test_wetland_process_alg, wetland_process_param)
    assert list(res.keys()) == ["TREATMENT"]

    ref_path = test_data_dir / "wetland_process_reference_output_with_null_input_3.gpkg.zip"
    gen_path = tmp_path / "wetland_process_generated_output.gpkg"

    assert_same_layers(
        load_layer(ref_path, "wetland_process_generated_output"),
        load_layer(gen_path, "wetland_process_generated_output"),
        check_values_only_on_fields=["fid", "sink_coords", "pathway_id", "available_surface", "name_stages"],
    )


def test_wetland_process_with_bad_inflow_concentrations(elan_processing, tmp_path):
    """
    Test wetland process crashes when there is bad values in inflow concentrations
    that trigger an error in wetlandoptimizer
    """

    from ELAN.processing.wetland_process import WetlandProcessAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "wetland_process"
    test_wetland_process_alg = WetlandProcessAlgorithm()
    assert test_wetland_process_alg.name() == "elanwetlandprocess"
    assert test_wetland_process_alg.groupId() == "elanprocessings"

    wetland_process_param = {
        "CLIMATE": 0,
        "TREATMENT": str(tmp_path / "wetland_process_generated_output.gpkg"),
        "SINKS": str(test_data_dir / "wetland_process_steu_with_bad_inflow_concentrations.gpkg.zip"),
        "AVAILABLE_SURFACE": None,
        "SINK_COORDS": "sink_coords",
        "STAGES_MAX": 3,
        "TSS_OBJ": "TSS_obj",
        "BOD5_OBJ": "BOD5_obj",
        "TKN_OBJ": "TKN_obj",
        "COD_OBJ": "COD_obj",
        "NO3N_OBJ": "NO3N_obj",
        "TN_OBJ": "TN_obj",
        "TP_OBJ": "TP_obj",
        "ECOLI_OBJ": "ecoli_obj",
        "Q_FIELD": "average_daily_flow",
    }

    with pytest.raises(
        QgsProcessingException,
        match=re.escape(
            "Inflow concentrations have incorrect values: [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], "
            "causing an error during COD_Fractionation step."
        ),
    ):

        elan_processing.run(test_wetland_process_alg, wetland_process_param)
