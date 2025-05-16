"""
Processing provider module.
"""

# PyQGIS
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

# project
from ELAN.__about__ import DIR_PLUGIN_ROOT, __experimental__, __version__
from ELAN.processing.economical import EconomicalAlgorithm
from ELAN.processing.hydraulic import HydraulicAlgorithm, HydraulicUrbanCatchmentAlgorithm
from ELAN.processing.lca import LcaAlgorithm
from ELAN.processing.population import PopulationAlgorithm
from ELAN.processing.roads_buildings import RoadsBuildingsAlgorithm
from ELAN.processing.sewer_network import SewerNetworkAlgorithm
from ELAN.processing.trench_profile import TrenchProfileAlgorithm
from ELAN.processing.wetland_process import WetlandProcessAlgorithm
from ELAN.processing.scenario import ScenarioAlgorithm
from ELAN.utils.tr import Translatable


class ELANProvider(QgsProcessingProvider, Translatable):
    def loadAlgorithms(self):
        """Loads all algorithms belonging to this provider."""

        self.addAlgorithm(PopulationAlgorithm())
        self.addAlgorithm(RoadsBuildingsAlgorithm())
        self.addAlgorithm(WetlandProcessAlgorithm())
        self.addAlgorithm(SewerNetworkAlgorithm())
        self.addAlgorithm(TrenchProfileAlgorithm())
        self.addAlgorithm(ScenarioAlgorithm())

        if __experimental__:
            self.addAlgorithm(LcaAlgorithm())
            self.addAlgorithm(EconomicalAlgorithm())
            self.addAlgorithm(HydraulicAlgorithm())
            self.addAlgorithm(HydraulicUrbanCatchmentAlgorithm())

    def id(self) -> str:
        """Unique provider id, used for identifying it. This string should be a unique, short, character only
        string, eg "qgis" or "gdal". This string should not be localised.

        :return: provider ID
        :rtype: str
        """
        return "elan"

    def name(self) -> str:
        """Returns the provider name, which is used to describe the provider
        within the GUI. This string should be short (e.g. "Lastools") and localised.

        :return: provider name
        :rtype: str
        """
        return self.tr("ELAN")

    def longName(self) -> str:
        """Longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools". This string should
        be localised. The default implementation returns the same string as name().

        :return: provider long name
        :rtype: str
        """
        return self.tr("ELAN - Tools")

    def icon(self) -> QIcon:
        """QIcon used for your provider inside the Processing toolbox menu.

        :return: provider icon
        :rtype: QIcon
        """
        return QIcon(str(DIR_PLUGIN_ROOT / "resources/images/ELAN-LOGO-02_ICONE.png"))

    def versionInfo(self) -> str:
        """Version information for the provider, or an empty string if this is not \
        applicable (e.g. for inbuilt Processing providers). For plugin based providers, \
        this should return the plugin’s version identifier.

        :return: version
        :rtype: str
        """
        return __version__
