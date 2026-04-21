"""
test_roads_buildings
"""

# pylint: disable=import-outside-toplevel, invalid-name, too-many-locals

import json
import re
import sys
from unittest import mock
from zipfile import ZipFile

import pytest
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsProject,
    QgsVectorLayer,
)

from ELAN.__about__ import DIR_PLUGIN_ROOT
from tests.utils import assert_same_layers, load_layer


@pytest.mark.xfail(sys.platform.startswith("win"), reason="Geometry differences to investigate on Windows", strict=True)
def test_roads_buildings_no_proj(elan_processing, mocker, tmp_path):
    """Test the processing roads buildings without reprojection on the project CRS"""

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_alg = RoadsBuildingsAlgorithm()
    assert roads_buildings_alg.name() == "elanroadsbuildings"
    assert roads_buildings_alg.groupId() == "elanpreprocessings"

    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
        "PROJ": False,
    }

    osm_zip_path = test_data_dir / "osm_roads_buildings.zip"
    assert osm_zip_path.exists()
    assert tmp_path.exists()
    json_osm_text = ""
    with ZipFile(osm_zip_path) as osm_zip:
        with osm_zip.open("osm_roads_buildings.json") as osm_json:
            json_osm_text = osm_json.read().decode()

    mock_response = mocker.Mock()
    mock_response.json.return_value = json.loads(json_osm_text)
    mocker.patch("ELAN.processing.roads_buildings.requests.get", return_value=mock_response)
    res = elan_processing.run(roads_buildings_alg, roads_buildings_param)

    assert list(res.keys()) == ["BUILDINGS_OUTPUT", "MERGED_BUILDINGS_OUTPUT", "ROADS_OUTPUT"]

    layers_generated = [
        "buildings_generated_output",
        "roads_generated_output",
        "buildings_merged_generated_output",
    ]
    layers_reference = [
        "buildings_reference_output",
        "roads_reference_output",
        "buildings_merged_reference_output",
    ]

    for layer_reference, layer_generated in zip(layers_reference, layers_generated):
        layer_ref = load_layer(test_data_dir / "roads_buildings_output_no_proj.gpkg.zip", layer_reference)
        layer_gen = load_layer((tmp_path / layer_generated).with_suffix(".gpkg"), layer_generated)
        assert_same_layers(layer_ref, layer_gen)


def test_roads_buildings_proj(elan_processing, mocker, tmp_path):
    """Test the processing roads buildings with reprojection on the project CRS"""

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_alg = RoadsBuildingsAlgorithm()
    assert roads_buildings_alg.name() == "elanroadsbuildings"
    assert roads_buildings_alg.groupId() == "elanpreprocessings"

    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
        "PROJ": True,
    }

    assert (project := QgsProject.instance())
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:32620"))

    osm_zip_path = test_data_dir / "osm_roads_buildings.zip"
    assert osm_zip_path.exists()
    assert tmp_path.exists()
    json_osm_text = ""
    with ZipFile(osm_zip_path) as osm_zip:
        with osm_zip.open("osm_roads_buildings.json") as osm_json:
            json_osm_text = osm_json.read().decode()

    mock_response = mocker.Mock()
    mock_response.json.return_value = json.loads(json_osm_text)
    mocker.patch("ELAN.processing.roads_buildings.requests.get", return_value=mock_response)
    res = elan_processing.run(roads_buildings_alg, roads_buildings_param)

    assert list(res.keys()) == ["BUILDINGS_OUTPUT", "MERGED_BUILDINGS_OUTPUT", "ROADS_OUTPUT"]

    layers_generated = [
        "buildings_generated_output",
        "roads_generated_output",
        "buildings_merged_generated_output",
    ]
    layers_reference = [
        "buildings_reference_output",
        "roads_reference_output",
        "buildings_merged_reference_output",
    ]

    for layer_reference, layer_generated in zip(layers_reference, layers_generated):
        layer_ref = load_layer(test_data_dir / "roads_buildings_output_proj.gpkg.zip", layer_reference)
        layer_gen = load_layer((tmp_path / layer_generated).with_suffix(".gpkg"), layer_generated)
        assert_same_layers(layer_ref, layer_gen)


def test_error_big_polygon(elan_processing):
    """
    Verify the error raised:
    - To big polygon input
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test_big_rect", "memory")
    if (provider := layer.dataProvider()) is None:
        raise RuntimeError("Unexpected error: layer provider is None")

    feat = QgsFeature()
    geom = QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))")
    feat.setGeometry(geom)
    provider.addFeature(feat)
    layer.updateExtents()

    with pytest.raises(QgsProcessingException, match=re.compile("The extent of the extraction area is too big")):
        elan_processing.run(roads_buildings_alg, {"POLYGON": layer})


def test_error_empty_polygon(elan_processing):
    """
    Verify the error raised:
    - empty polygon input
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()

    with pytest.raises(QgsProcessingException, match=re.compile("The extent of the extraction area is null")):
        elan_processing.run(
            roads_buildings_alg, {"POLYGON": QgsVectorLayer("Polygon?crs=EPSG:4326", "test_null", "memory")}
        )


def test_timeout(elan_processing, mocker, tmp_path):
    """
    Verify that OpenStreeMap server timeout is handled.
    Try 4 times: the first 3 times are timetouts, and the last try succeeds.
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()

    # 1st mock response from request: timeout
    mock_response_1 = mocker.Mock()
    mock_response_1.json.side_effect = json.JSONDecodeError("", "", 0)
    mock_response_1.text = "some text and timeout"

    # 2nd mock response from request: timeout
    mock_response_2 = mocker.Mock()
    mock_response_2.json.side_effect = json.JSONDecodeError("", "", 0)
    mock_response_2.text = "timeout"

    # 3rd mock response from request: timeout
    mock_response_3 = mocker.Mock()
    mock_response_3.json.side_effect = json.JSONDecodeError("", "", 0)
    mock_response_3.text = "timeout and some text"

    # 4th mock response from request: ok (here en empty elements dict, but valid expected json)
    mock_response_4 = mocker.Mock()
    mock_response_4.json.return_value = {"elements": []}

    mocker.patch(
        "ELAN.processing.roads_buildings.requests.get",
        side_effect=[mock_response_1, mock_response_2, mock_response_3, mock_response_4],
    )

    spy_feedback = SpyMultiStepFeedback()
    mocker.patch("ELAN.processing.roads_buildings.QgsProcessingMultiStepFeedback", return_value=spy_feedback)

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
    }

    elan_processing.run(roads_buildings_alg, roads_buildings_param)

    # Verification of the messages
    spy_feedback.spy.pushInfo.assert_has_calls(
        [
            mocker.call("OpenStreetMap server timeout, retrying (2/5)"),
            mocker.call("OpenStreetMap server timeout, retrying (3/5)"),
            mocker.call("OpenStreetMap server timeout, retrying (4/5)"),
        ]
    )
    assert len(spy_feedback.spy.mock_calls) == 6  # The 3 last calls are intermediate info from child processings


def test_error_max_timeout(elan_processing, mocker, tmp_path):
    """
    An error is raised and the processing ends if the maximum number of
    OpenStreetMap timeouts is reached.
    """

    from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm

    roads_buildings_alg = RoadsBuildingsAlgorithm()

    spy_feedback = SpyMultiStepFeedback()
    mocker.patch("ELAN.processing.roads_buildings.QgsProcessingMultiStepFeedback", return_value=spy_feedback)

    test_data_dir = DIR_PLUGIN_ROOT.parent / "tests" / "data_test" / "roads_buildings"
    roads_buildings_param = {
        "POLYGON": str(test_data_dir / "buildings_roads_input.gpkg.zip"),
        "BUILDINGS_OUTPUT": str(tmp_path / "buildings_generated_output.gpkg"),
        "MERGED_BUILDINGS_OUTPUT": str(tmp_path / "buildings_merged_generated_output.gpkg"),
        "ROADS_OUTPUT": str(tmp_path / "roads_generated_output.gpkg"),
    }

    # Every response made will be a timeout
    mock_response = mocker.Mock()
    mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
    mock_response.text = "some text and timeout"
    mocker.patch("ELAN.processing.roads_buildings.requests.get", return_value=mock_response)

    with pytest.raises(QgsProcessingException, match=re.compile("Maximum number of attempts reached, exiting.")):
        elan_processing.run(roads_buildings_alg, roads_buildings_param)

    spy_feedback.spy.pushInfo.assert_has_calls(
        [
            mocker.call("OpenStreetMap server timeout, retrying (2/5)"),
            mocker.call("OpenStreetMap server timeout, retrying (3/5)"),
            mocker.call("OpenStreetMap server timeout, retrying (4/5)"),
            mocker.call("OpenStreetMap server timeout, retrying (5/5)"),
        ]
    )
    assert len(spy_feedback.spy.mock_calls) == 4


class SpyMultiStepFeedback(QgsProcessingMultiStepFeedback):  # pylint: disable=too-few-public-methods
    """
    Need for a custom spy feedback because of child algorithms and SIP
    which can't accept Mocks
    """

    def __init__(self):
        self.__feedback = QgsProcessingFeedback()
        super().__init__(4, self.__feedback)
        self.spy = mock.Mock()  # internal Mock

    def pushInfo(self, info):
        """We record the call in the internal Mock"""
        self.spy.pushInfo(info)
        super().pushInfo(info)
