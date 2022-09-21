import gettext
import sys


def patch_gettext():
    # Patch gettext classes for Python 3.7 to support context in pgettext
    if sys.version_info < (3, 8):
        def pgettext(self, context, message):
            if self._fallback:
                return self._fallback.pgettext(context, message)
            return message
        gettext.NullTranslations.pgettext = pgettext
        gettext.GNUTranslations.CONTEXT = "%s\x04%s"

        def pgettext(self, context, message):
            ctxt_msg_id = self.CONTEXT % (context, message)
            missing = object()
            tmsg = self._catalog.get(ctxt_msg_id, missing)
            if tmsg is missing:
                if self._fallback:
                    return self._fallback.pgettext(context, message)
                return message
            return tmsg
        gettext.GNUTranslations.pgettext = pgettext
