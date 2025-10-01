"""
Fixtures for ELAN testing
"""

import site

import pytest

from ELAN.utils.dependencies_utils import EXTERNAL_LIRBARIES_DIR


@pytest.fixture(scope="session", autouse=True)
def set_external_lib_path():
    """
    This is a fixture to have external libraries available during tests, if they are
    present in EXTERNAL_LIRBARIES_DIR.
    """

    site.addsitedir(str(EXTERNAL_LIRBARIES_DIR))


@pytest.fixture(scope="function")
def elan_processing(mocker, qgis_processing):
    """
    This is a fixture to do things that prepare testing ELAN processings.

    Returns the processing module to call the run method
    """

    import processing

    mocker.patch("ELAN.utils.tr.PlgLogger")  # don't care about logging anything from translations
    return processing
