# pylint: disable=attribute-defined-outside-init

"""
Main plugin module.
"""

import site

# PyQGIS and PyQt
from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QToolBar
from qgis.utils import QDesktopServices, QUrl

# project
from ELAN.__about__ import DIR_PLUGIN_ROOT, __experimental__, __title__, __uri_homepage__
from ELAN.gui.dlg_settings import PlgOptionsFactory
from ELAN.scripts.treatment_train_plot import ProcessPlots
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

        :param iface: An interface instance that will be passed to this class which
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
        self.action_help = QAction(
            QgsApplication.getThemeIcon("mActionHelpContents.svg"),
            self.tr("Documentation"),
            self.iface.mainWindow(),
        )
        self.action_help.triggered.connect(self.showDocumentation)

        # -- Menu
        self.iface.addPluginToMenu(__title__, self.action_settings)
        self.iface.addPluginToMenu(__title__, self.action_help)

        # -- Permeability
        if __experimental__:
            self.permeabilite_panneau = QDockWidget()
            self.permeabilite_panneau.setWindowTitle("Seuil de perméabilité")
            self.permeabilite_panneau.setObjectName("SeuilPermeabilite")
            self.permeabilite_panneau.setWidget(PermeabilityWidget())
            self.iface.addTabifiedDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.permeabilite_panneau)
            self.permeabilite_panneau.setVisible(False)

        # -- Toolbar
        self.toolbar = QToolBar(__title__)
        self.toolbar.addAction(
            QIcon(str(DIR_PLUGIN_ROOT / "resources" / "images" / "bar_plot.jpeg")),
            self.tr("Show bar plot for treatment train layer"),
            lambda: ProcessPlots().barPlot(),
        )
        self.toolbar.addAction(
            QIcon(str(DIR_PLUGIN_ROOT / "resources" / "images" / "radar_plot.jpeg")),
            self.tr("Show radar plot for treatment train layer"),
            lambda: ProcessPlots().radarPlot(),
        )
        self.iface.addToolBar(self.toolbar)

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
                button_connect=self.showDocumentation,
            )
            self.provider = None

    @staticmethod
    def showDocumentation():
        """
        Shows the plugin documentation in the default web browser
        """

        QDesktopServices.openUrl(QUrl(__uri_homepage__))

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
        # -- Clean up menu
        self.iface.removePluginMenu(__title__, self.action_settings)
        self.iface.removePluginMenu(__title__, self.action_help)

        # -- Clean up toolbar
        self.toolbar.deleteLater()
        del self.toolbar

        if __experimental__:
            self.iface.removeDockWidget(self.permeabilite_panneau)
            del self.permeabilite_panneau

        # -- Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        del self.action_settings

        # -- Unregister processing
        if (registry := QgsApplication.processingRegistry()) is not None and self.provider is not None:
            registry.removeProvider(self.provider)
