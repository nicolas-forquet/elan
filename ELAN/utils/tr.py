from PyQt5.QtCore import QCoreApplication, QTranslator

from ELAN.__about__ import DIR_PLUGIN_ROOT, LOCALE
from ELAN.toolbelt.log_handler import PlgLogger


class Translatable:

    TRANSLATION_INITIALIZED = False

    def tr(self, sourceText):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """

        if not Translatable.TRANSLATION_INITIALIZED:
            # initialize locale
            locale_path = (DIR_PLUGIN_ROOT / "resources" / "i18n" / f"ELAN_{LOCALE}.qm").resolve()
            if locale_path.exists():
                self.translator = QTranslator()
                self.translator.load(str(locale_path))
                QCoreApplication.installTranslator(self.translator)
            else:
                PlgLogger.log(f"no file {locale_path} found", log_level=1)
            Translatable.TRANSLATION_INITIALIZED = True

        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(self.__class__.__name__, sourceText)
