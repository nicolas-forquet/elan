#! python3  # noqa E265

"""
    Usage from the repo root folder:

    .. code-block:: bash
        # for whole tests
        python -m unittest tests.test_plg_metadata
        # for specific test
        python -m unittest tests.test_plg_metadata.TestPluginMetadata.test_version_semver
"""

# standard library
import unittest
from pathlib import Path

# 3rd party
from semver import VersionInfo

# project
from ELAN import __about__


class TestPluginMetadata(unittest.TestCase):
    """Test about module"""

    def test_metadata_types(self):
        """Test types."""
        # plugin metadata.txt file
        self.assertIsInstance(__about__.PLG_METADATA_FILE, Path)
        self.assertTrue(__about__.PLG_METADATA_FILE.is_file())

        # plugin dir
        self.assertIsInstance(__about__.DIR_PLUGIN_ROOT, Path)
        self.assertTrue(__about__.DIR_PLUGIN_ROOT.is_dir())

        # metadata as dict
        self.assertIsInstance(__about__.__plugin_md__, dict)

        # general
        self.assertIsInstance(__about__.__author__, str)
        self.assertIsInstance(__about__.__copyright__, str)
        self.assertIsInstance(__about__.__email__, str)
        self.assertIsInstance(__about__.__keywords__, list)
        self.assertIsInstance(__about__.__license__, str)
        self.assertIsInstance(__about__.__summary__, str)
        self.assertIsInstance(__about__.__title__, str)
        self.assertIsInstance(__about__.__title_clean__, str)
        self.assertIsInstance(__about__.__version__, str)
        self.assertIsInstance(__about__.__version_info__, tuple)

        # misc
        self.assertLessEqual(len(__about__.__title_clean__), len(__about__.__title__))

        # QGIS versions
        qgisminimumversion = __about__.__plugin_md__.get("general").get("qgisminimumversion")
        self.assertIsInstance(qgisminimumversion, str)
        qgismaximumversion = __about__.__plugin_md__.get("general").get("qgismaximumversion")
        self.assertIsInstance(qgismaximumversion, str)
        if len(qgisminimumversion.split(".")) == 2:
            qgisminimumversion += ".0"
        if len(qgismaximumversion.split(".")) == 2:
            qgismaximumversion += ".0"

        self.assertLessEqual(
            VersionInfo.parse(qgisminimumversion),
            VersionInfo.parse(qgismaximumversion),
            "Minimum QGIS version is >= maximum QGIS version",
        )

    def test_version_semver(self):
        """Test if version comply with semantic versioning."""
        self.assertTrue(VersionInfo.is_valid(__about__.__version__))


if __name__ == "__main__":
    unittest.main()
