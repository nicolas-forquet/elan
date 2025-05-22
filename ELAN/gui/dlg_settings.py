#! python3  # noqa: E265

"""
Plugin settings dialog.
"""

# standard
import logging
from pathlib import Path

# PyQGIS
from qgis.core import QgsSettings
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QHBoxLayout, QMessageBox, QWidget
from qgis.utils import OverrideCursor

# project
from ELAN.__about__ import DIR_PLUGIN_ROOT, __title__, __version__
from ELAN.toolbelt import PlgLogger, PlgOptionsManager
from ELAN.utils import dependencies_utils
from ELAN.utils.tr import Translatable

logger = logging.getLogger(__name__)
FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / f"{Path(__file__).stem}.ui")


class DlgSettings(QWidget, FORM_CLASS, Translatable):
    """
    Dialog settings class
    """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.log = PlgLogger().log

        # header
        self.lbl_title.setText(f"{__title__} - Version {__version__}")

        # load previously saved settings
        self.loadSettings()

        self.pysewerCheckBtn.clicked.connect(self.pysewerCheck)
        self.pysewerInstallBtn.clicked.connect(self.pysewerInstall)

        self.wetlandoptimizerCheckBtn.clicked.connect(self.wetlandoptimizerCheck)
        self.wetlandoptimizerInstallBtn.clicked.connect(self.wetlandoptimizerInstall)

        self.resetDependenciesBtn.clicked.connect(self.resetDependencies)

    def pysewerCheck(self):
        """Check if pysewer is installed"""
        try:
            with OverrideCursor(Qt.CursorShape.WaitCursor):
                if dependencies_utils.pysewerInstalled(True):
                    msg = self.tr("pysewer is installed")
                else:
                    msg = self.tr("pysewer is not installed")
            QMessageBox.information(self, self.tr("Check pysewer"), msg)
        except RuntimeError as e:
            QMessageBox.critical(self, self.tr("Check pysewer"), str(e))

    def pysewerInstall(self):
        """Try to install pysewer and its dependencies"""

        # Ask user to continue install even if pysewer is already installed
        try:
            if dependencies_utils.pysewerInstalled(True):
                QMessageBox.information(self, self.tr("Install pysewer"), self.tr("pysewer is already installed."))
                return
        except RuntimeError as e:
            QMessageBox.critical(self, self.tr("Install pysewer"), str(e))
            return

        # Install pysewer
        try:
            with OverrideCursor(Qt.CursorShape.WaitCursor):
                dependencies_utils.installPysewer()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Install pysewer"), str(e))
            return

        QMessageBox.information(self, self.tr("Install pysewer"), self.tr("Installation successfull"))

    def wetlandoptimizerCheck(self):
        """Check if wetlandoptimizer is installed"""
        try:
            with OverrideCursor(Qt.CursorShape.WaitCursor):
                if dependencies_utils.wetlandoptimizerInstalled():
                    msg = self.tr("wetlandoptimizer is installed")
                else:
                    msg = self.tr("wetlandoptimizer is not installed")
            QMessageBox.information(self, self.tr("Check wetlandoptimizer"), msg)
        except RuntimeError as e:
            QMessageBox.critical(self, self.tr("Check wetlandoptimizer"), str(e))

    def wetlandoptimizerInstall(self):
        """Try to install wetlandoptimizer and its dependencies"""

        # Ask user to continue install even if wetlandoptimizer is already installed
        try:
            if dependencies_utils.wetlandoptimizerInstalled():
                QMessageBox.information(
                    self, self.tr("Install wetlandoptimizer"), self.tr("wetlandoptimizer is already installed.")
                )
                return
        except RuntimeError as e:
            QMessageBox.critical(self, self.tr("Install wetlandoptimizer"), str(e))
            return

        # Install wetlandoptimizer
        try:
            with OverrideCursor(Qt.CursorShape.WaitCursor):
                dependencies_utils.installWetlandoptimizer()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Install wetlandoptimizer"), str(e))
            return

        QMessageBox.information(self, self.tr("Install wetlandoptimizer"), self.tr("Installation successfull"))

    def resetDependencies(self):
        if (
            QMessageBox.question(
                self, self.tr("Reset dependencies"), self.tr("Do you really want to delete all ELAN dependencies?")
            )
            == QMessageBox.StandardButton.No
        ):
            return
        try:
            dependencies_utils.removeDependencies()
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Reset dependencies"), self.tr("Unable to reset dependencies:") + "\n" + str(e)
            )

    def closeEvent(self, event):
        """Map on plugin close.

        :param event: [description]
        :type event: [type]
        """
        self.closingPlugin.emit()
        event.accept()

    def loadSettings(self) -> dict:
        """Load options from QgsSettings into UI form."""
        settings = PlgOptionsManager.getPlgSettings()._asdict()

    def saveSettings(self):
        """Save options from UI form into QSettings."""
        # open settings group
        settings = QgsSettings()
        settings.beginGroup(__title__)

        # save plugin version
        settings.setValue("version", __version__)

        # close settings group
        settings.endGroup()


# pylint:disable=missing-class-docstring,too-few-public-methods,missing-function-docstring


class PlgOptionsFactory(QgsOptionsWidgetFactory):
    def icon(self):
        return QIcon(str(DIR_PLUGIN_ROOT / "resources/images/ELAN-LOGO-02_ICONE.png"))

    def createWidget(self, parent):
        return ConfigOptionsPage(parent)

    def title(self):
        return __title__


class ConfigOptionsPage(QgsOptionsPageWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.dlg_settings = DlgSettings(self)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.dlg_settings.setLayout(layout)
        self.setLayout(layout)
        self.setObjectName(f"mOptionsPage{__title__}")

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        self.dlg_settings.saveSettings()
