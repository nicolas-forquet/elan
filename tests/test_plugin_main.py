"""Test ELAN plugin loading, initialization, and unloading"""

from qgis.utils import iface

from ELAN import classFactory

# pylint: disable=invalid-name,unused-argument


def mockIfaceMissingMethod(*args, **kwargs): ...


iface.registerOptionsWidgetFactory = mockIfaceMissingMethod
iface.unregisterOptionsWidgetFactory = mockIfaceMissingMethod
iface.removePluginMenu = mockIfaceMissingMethod
iface.addTabifiedDockWidget = mockIfaceMissingMethod
iface.removeDockWidget = mockIfaceMissingMethod


def test_plugin_main():
    """Launch main plugin class"""

    elan = classFactory(iface)
    elan.initGui()
    elan.unload()
