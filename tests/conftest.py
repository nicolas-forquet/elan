"""
Fixtures for Elan testing
"""

# function names don't begin with test_ here, they are fixtures
# pylint: disable=invalid-name


import site

import pytest

from ELAN.utils.dependencies_utils import EXTERNAL_LIRBARIES_DIR


@pytest.fixture(autouse=True)
def ignore_tr_logs(mocker):
    """
    This is a fixture to avoid translating message logs to ensure messages
    comparisons during tests.
    """

    mocker.patch("ELAN.utils.tr.PlgLogger")


@pytest.fixture(scope="session", autouse=True)
def external_libs():
    """
    This is a fixture to have external libraries available during tests.
    """

    site.addsitedir(str(EXTERNAL_LIRBARIES_DIR))


@pytest.fixture
def elan_processing(mocker, qgis_processing):  # pylint: disable=unused-argument
    """
    This is a fixture to do things that prepare testing Elan processings.

    Returns the processing module to call the run method
    """

    import processing  # pylint: disable=import-outside-toplevel

    return processing
