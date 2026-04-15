"""
test_sewer_network
"""

# pylint: disable=import-outside-toplevel, invalid-name

from unittest.mock import patch

import pytest

from ELAN.__about__ import DIR_PLUGIN_ROOT


def test_main(tmp_path):
    """Test main pysewer launcher"""

    from ELAN.resources.pysewer import pysewer_launcher

    test_data_dir_sewer = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network"

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "pysewer_launcher"
    filename_yaml = str(test_data_dir / "config.yaml")
    output_path = str(tmp_path / "OUTPUT_PATH.gpkg")
    output_path_error = str(tmp_path / "OUTPUT_PATH.shp")
    sinks_path = str(test_data_dir_sewer / "sewer_network_steu_input.gpkg")

    # with check_install
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(filename_yaml),
            "--check-installed",
            "--output-path",
            str(output_path),
        ],
    ):
        pysewer_launcher.main()

    # test run(filename, output_path, sinks_path)

    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(filename_yaml),
            "--output-path",
            str(output_path),
        ],
    ):
        pysewer_launcher.main()

    # without outpath
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(filename_yaml),
        ],
    ):
        with pytest.raises(ValueError):
            pysewer_launcher.main()

    # wrong output_path
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(filename_yaml),
            "--output-path",
            str(output_path_error),
        ],
    ):
        with pytest.raises(ValueError):
            pysewer_launcher.main()
    # without yaml
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--output-path",
            str(output_path),
        ],
    ):
        with pytest.raises(ValueError):
            pysewer_launcher.main()

    # GPKG for sink_path
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(filename_yaml),
            "--output-path",
            str(output_path),
            "--sinks-path",
            str(sinks_path),
        ],
    ):
        with pytest.raises(ValueError):
            pysewer_launcher.main()


def test_run(tmp_path):
    """Test run pysewer launcher"""

    from ELAN.resources.pysewer import pysewer_launcher

    test_data_dir_sewer = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network"

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "pysewer_launcher"
    filename_yaml = str(test_data_dir / "config.yaml")
    output_path = str(tmp_path / "OUTPUT_PATH.gpkg")
    sinks_path = str(test_data_dir_sewer / "sewer_network_steu_input.gpkg")
    pysewer_launcher.run(filename_yaml, output_path, sinks_path)
