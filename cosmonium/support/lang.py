"""
Language management module.

This module provides the LangManager class, which is responsible for detecting the user's language,
loading the appropriate translation files, and installing the translation for use throughout the application.
"""

import gettext
import os
import subprocess
import sys

from ..dircontext import defaultDirContext


class LangManager:
    """
    Manages language detection and translation loading.
    """

    def __init__(self):
        """
        Initializes the LangManager instance.
        """
        self.languages = None

    def find_lang(self):
        """
        Detects the user's preferred language(s) by checking environment variables or system settings.
        On macOS, uses 'defaults' command to retrieve default locale.
        On Windows, retrieve default UI language for the user.
        Sets self.languages to a list of language codes.
        """
        languages = None
        for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(envar)
            if val:
                languages = val.split(':')
                break
        if languages is None:
            if sys.platform == 'darwin':
                # TODO: This is a workaround until either Panda3D provides the locale to use
                # or we switch to pyobjc.
                # This should be moved to its own module
                status, output = subprocess.getstatusoutput('defaults read -g AppleLocale')
                if status == 0:
                    languages = [output]
                else:
                    print("Could not retrieve default locale")
            elif sys.platform == 'win32':
                import ctypes
                import locale

                language = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
                if language is not None:
                    languages = [language]
                else:
                    print("Could not retrieve default locale")

        print("Found languages:", ', '.join(languages))
        self.languages = languages

    def load_lang(self, domain: str, locale_path: str):
        """
        Loads the gettext translation for the given domain and locale path.
        If locale_path is None, returns a NullTranslations object.

        Args:
            domain: The translation domain.
            locale_path: Path to the locale directory containing translation files.

        Returns:
            gettext.NullTranslations or gettext.GNUTranslations: The translation object.
        """
        if locale_path is not None:
            return gettext.translation(domain, locale_path, languages=self.languages, fallback=True)
        else:
            return gettext.NullTranslations()

    def init_lang(self) -> None:
        """
        Initializes language detection and installs the translation globally.
        Finds the user's language, loads the translation, and installs it for use with the _() function.
        """
        self.find_lang()
        self.translation = self.load_lang('cosmonium', defaultDirContext.find_file('main', 'locale'))
        self.translation.install()
