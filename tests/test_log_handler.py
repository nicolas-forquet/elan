from unittest.mock import MagicMock

from qgis.gui import QgisInterface

from ELAN.toolbelt.log_handler import PlgLogger


def test_log_handler(mocker):
    """
    Unit test for logger
    """

    # Patch iface so that isinstance asserts in log_hangler are OK
    # (we need to patch over the qgis_interface fixture to handle the spec parameter)
    iface_mock: MagicMock = mocker.patch("ELAN.toolbelt.log_handler.iface", spec=QgisInterface)

    # Patch QgsMessageLog to spy the calls
    message_log_mock: MagicMock = mocker.patch("ELAN.toolbelt.log_handler.QgsMessageLog")

    # normal call
    PlgLogger.log("everything is fine")
    message_log_mock.logMessage.assert_called_once_with(
        level=0, message="everything is fine", notifyUser=False, tag="ELAN"
    )
    message_log_mock.reset_mock()

    # call with a non string parameter: should convert it to a string
    PlgLogger.log(54)
    message_log_mock.logMessage.assert_called_once_with(level=0, message="54", notifyUser=False, tag="ELAN")
    message_log_mock.reset_mock()

    # call with push: should trigger a message bar
    PlgLogger.log("hey", push=True)
    message_log_mock.logMessage.assert_called_once_with(level=0, message="hey", notifyUser=True, tag="ELAN")
    iface_mock.messageBar.return_value.pushMessage.assert_called_once_with(
        level=0, text="hey", title="ELAN", duration=3
    )
    message_log_mock.reset_mock()
    iface_mock.reset_mock()

    # call with application name
    PlgLogger.log("beware this warning!", log_level=1, application="The Best")
    message_log_mock.logMessage.assert_called_once_with(
        level=1, message="beware this warning!", notifyUser=False, tag="The Best"
    )
    message_log_mock.reset_mock()

    # call with log level "warning" and push
    PlgLogger.log("watch out this error!", log_level=2, push=True)
    message_log_mock.logMessage.assert_called_once_with(
        level=2, message="watch out this error!", notifyUser=True, tag="ELAN"
    )
    iface_mock.messageBar.return_value.pushMessage.assert_called_once_with(
        level=2, text="watch out this error!", title="ELAN", duration=9
    )
    message_log_mock.reset_mock()
    iface_mock.reset_mock()

    # call with log level "success" and application name
    PlgLogger.log("this is a big success", log_level=3, application="Fine")
    message_log_mock.logMessage.assert_called_once_with(
        level=3, message="this is a big success", notifyUser=False, tag="Fine"
    )
    message_log_mock.reset_mock()

    # call with log level "test" and push and application name
    PlgLogger.log("if we could test everything...", log_level=4, push=True, application="Testing app")
    message_log_mock.logMessage.assert_called_once_with(
        level=4, message="if we could test everything...", notifyUser=True, tag="Testing app"
    )
    iface_mock.messageBar.return_value.pushMessage.assert_called_once_with(
        level=4, text="if we could test everything...", title="Testing app", duration=15
    )
