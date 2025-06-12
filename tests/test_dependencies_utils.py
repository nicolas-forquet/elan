"""
Tests for dependencies_utils module
"""

from pathlib import Path

import pytest

from ELAN.utils.dependencies_utils import (
    installPysewer,
    installWetlandoptimizer,
    pysewerInstalled,
    wetlandoptimizerInstalled,
)


@pytest.fixture(scope="function", autouse=True)
def external_libs_test(mocker, tmp_path):
    """
    Specific fixture to use a temporary EXTERNAL_LIRBARIES_DIR for the test.
    """

    # Temporary external library directory
    external_libs_test: Path = tmp_path / "external_libs_test"
    mocker.patch("ELAN.utils.dependencies_utils.EXTERNAL_LIRBARIES_DIR", new=external_libs_test)

    # We mock installLibrary function: don't use the real function that downloads and unzip everything.
    # Only create empty directories when it is called.
    installLibraryMock = mocker.patch(
        "ELAN.utils.dependencies_utils.installLibrary",
        side_effect=lambda library_name, _: (external_libs_test / library_name).mkdir(parents=True),
    )

    yield  # executes the test

    installLibraryMock.assert_called_once()


def test_pysewer_installed():
    assert not pysewerInstalled()
    assert not pysewerInstalled(external_libs=True)
    installPysewer()
    assert pysewerInstalled(external_libs=True)


def test_wetlandoptimizer_installed():

    assert not wetlandoptimizerInstalled()
    installWetlandoptimizer()
    assert wetlandoptimizerInstalled()
