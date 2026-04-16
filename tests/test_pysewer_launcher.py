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
    filename_yaml = str(test_data_dir / "config.yaml.template")
    output_path = str(tmp_path / "OUTPUT_PATH.gpkg")
    output_path_error = str(tmp_path / "OUTPUT_PATH.shp")
    sinks_path = str(test_data_dir_sewer / "sewer_network_steu_input.gpkg")
    placeholders_yml = {
        "buildings_input_data": str(test_data_dir_sewer / "sewer_network_buildings_population_input.gpkg"),
        "dem_file_path": str(test_data_dir_sewer / "sewer_network_mnt_input.tif"),
        "roads_input_data": str(test_data_dir_sewer / "sewer_network_roads_input.gpkg"),
    }
    with open(filename_yaml) as f:
        content = f.read()
    for key, value in placeholders_yml.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    tmp_yaml = tmp_path / "config.yaml"
    tmp_yaml.write_text(content)

    # with check_install
    with patch(
        "sys.argv",
        [
            "pysewer_launcher",
            "--yaml",
            str(tmp_yaml),
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
            str(tmp_yaml),
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
            str(tmp_yaml),
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
            str(tmp_yaml),
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
            str(tmp_yaml),
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

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "pysewer_launcher"
    test_data_dir_sewer = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "sewer_network"
    output_path = tmp_path / "OUTPUT_PATH.gpkg"
    sinks_path = test_data_dir_sewer / "sewer_network_steu_input.gpkg"
    yaml_template_path = test_data_dir / "config.yaml.template"

    placeholders_yml = {
        "buildings_input_data": str(test_data_dir_sewer / "sewer_network_buildings_population_input.gpkg"),
        "dem_file_path": str(test_data_dir_sewer / "sewer_network_mnt_input.tif"),
        "roads_input_data": str(test_data_dir_sewer / "sewer_network_roads_input.gpkg"),
    }
    content = yaml_template_path.read_text()
    for key, value in placeholders_yml.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    tmp_yaml = tmp_path / "config_template.yaml"
    tmp_yaml.write_text(content)

    pysewer_launcher.run(tmp_yaml, output_path, sinks_path)
