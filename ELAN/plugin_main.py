# pylint: disable=attribute-defined-outside-init

"""
Main plugin module.
"""

import site
from functools import partial

# PyQGIS
from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QDockWidget
from qgis.utils import QDesktopServices, QUrl

# project
from ELAN.__about__ import __experimental__, __title__, __uri_homepage__
from ELAN.gui.dlg_settings import PlgOptionsFactory
from ELAN.toolbelt.log_handler import PlgLogger
from ELAN.utils.dependencies_utils import EXTERNAL_LIRBARIES_DIR
from ELAN.utils.tr import Translatable

if __experimental__:
    from ELAN.permeability_panel import PermeabilityWidget

try:
    from ELAN.processing.provider import ELANProvider

    PROCESSINGS_AVAILABLE = True
except ImportError:
    PROCESSINGS_AVAILABLE = False


site.addsitedir(str(EXTERNAL_LIRBARIES_DIR))


class ELANPlugin(Translatable):
    """Main class"""

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.provider = None

    def initGui(self):
        """Set up plugin UI elements."""

        # settings page within the QGIS preferences menu
        self.options_factory = PlgOptionsFactory()
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        # -- Actions
        self.action_settings = QAction(
            QgsApplication.getThemeIcon("console/iconSettingsConsole.svg"),
            self.tr("Settings"),
            self.iface.mainWindow(),
        )
        self.action_settings.triggered.connect(
            lambda: self.iface.showOptionsDialog(currentPage=f"mOptionsPage{__title__}")
        )

        # -- Menu
        self.iface.addPluginToMenu(__title__, self.action_settings)

        # -- Permeability
        if __experimental__:
            self.permeabilite_panneau = QDockWidget()
            self.permeabilite_panneau.setWindowTitle("Seuil de perméabilité")
            self.permeabilite_panneau.setObjectName("SeuilPermeabilite")
            self.permeabilite_panneau.setWidget(PermeabilityWidget())
            self.iface.addTabifiedDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.permeabilite_panneau)
            self.permeabilite_panneau.setVisible(False)

        # -- Processing
        if PROCESSINGS_AVAILABLE:
            self.provider = ELANProvider()
            if (registry := QgsApplication.processingRegistry()) is None:
                raise RuntimeError("Processing registry not found")
            registry.addProvider(self.provider)
        else:
            PlgLogger.log(
                message=self.tr("Error importing dependencies. ELAN processing modules are disabled."),
                log_level=2,
                push=True,
                duration=60,
                button=True,
                button_text=self.tr("How to fix it..."),
                button_connect=partial(
                    QDesktopServices.openUrl,
                    QUrl(f"{__uri_homepage__}/installation.html"),
                ),
            )
            self.provider = None

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
        # -- Clean up menu
        self.iface.removePluginMenu(__title__, self.action_settings)

        if __experimental__:
            self.iface.removeDockWidget(self.permeabilite_panneau)
            del self.permeabilite_panneau

        # -- Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        del self.action_settings

        # -- Unregister processing
        if (registry := QgsApplication.processingRegistry()) is not None and self.provider is not None:
            registry.removeProvider(self.provider)
