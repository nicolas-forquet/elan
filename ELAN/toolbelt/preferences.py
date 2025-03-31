#! python3  # noqa: E265

"""
    Plugin settings.
"""

# standard
import logging
from typing import NamedTuple

# PyQGIS
from qgis.core import QgsSettings

# package
from ELAN.__about__ import __title__, __version__

from .log_handler import PlgLogger

logger = logging.getLogger(__name__)
plg_logger = PlgLogger()


class PlgSettingsStructure(NamedTuple):
    """Plugin settings structure and defaults values."""

    # global
    version: str = __version__

    defaults = [
        False,
        __version__,
    ]


class PlgOptionsManager:
    """Plugin options manager"""

    @staticmethod
    def getPlgSettings() -> PlgSettingsStructure:
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings
        :rtype: PlgSettingsStructure
        """
        settings = QgsSettings()
        settings.beginGroup(__title__)

        options = PlgSettingsStructure(
            # normal
            version=settings.value(key="version", defaultValue=__version__, type=str),
        )

        settings.endGroup()

        return options

    @staticmethod
    def getValueFromKey(key: str, default=None, exp_type=None):
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings value matching key
        """
        if not hasattr(PlgSettingsStructure, key):
            logger.error("Bad settings key. Must be one of: %s", ",".join(PlgSettingsStructure._fields))
            return None

        settings = QgsSettings()
        settings.beginGroup(__title__)

        try:
            out_value = settings.value(key=key, defaultValue=default, type=exp_type)
        except Exception as err:
            logger.error(err)
            plg_logger.log(err)
            out_value = None

        settings.endGroup()

        return out_value
