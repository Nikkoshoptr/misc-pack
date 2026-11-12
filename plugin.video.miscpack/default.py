# -*- coding: utf-8 -*-
import sys
import os.path
import traceback

import xbmcaddon

__plugin__ = 'Misc Pack'
__author__ = 'sfaxman'
__credits__ = 'bootsy'

ADDON_ID = 'plugin.video.miscpack'


def _dialog_safe(s):
    # Kodi renders [xxx] as a GUI markup tag and swallows the text; any
    # brackets in a traceback would hide the reason -> replace them
    s = str(s).replace('[', '(').replace(']', ')')
    try:
        s = s.encode('utf-8')  # Python 2 dialogs want bytes
    except AttributeError:
        pass
    except UnicodeDecodeError:
        pass
    return s


def report_crash(tb_text, where):
    """Show the crash reason on screen and write it to a file (Py2/3 safe)."""
    path = ''
    try:
        import xbmc
        import xbmcvfs
        addon = xbmcaddon.Addon(id=ADDON_ID)
        tp = getattr(xbmcvfs, 'translatePath', None) or getattr(xbmc, 'translatePath')
        sd = tp(addon.getAddonInfo('profile'))
        if sd and not os.path.exists(sd):
            try:
                os.makedirs(sd)
            except Exception:
                pass
        if sd:
            path = os.path.join(sd, 'miscpack_crash.txt')
            f = open(path, 'w')
            f.write(tb_text)
            f.close()
    except Exception:
        pass
    try:
        import xbmcgui
        dlg = xbmcgui.Dialog()
        lines = tb_text.strip().splitlines()
        body = where + '\n\n' + '\n'.join(lines)
        if path:
            body = body + '\n\nDetay dosya: ' + path
        try:
            # scrollable full-text viewer: best for tracebacks
            dlg.textviewer(_dialog_safe('Misc Pack Crash'), _dialog_safe(body))
        except Exception:
            dlg.ok(_dialog_safe('Misc Pack Crash'),
                   _dialog_safe((lines[-1] if lines else 'bos traceback') + '\n' + where))
    except Exception:
        pass


def _safe_main():
    try:
        import core
    except Exception:
        report_crash(traceback.format_exc(), 'ASAMA 1 - import core')
        return
    try:
        core.Main()
    except Exception:
        report_crash(traceback.format_exc(), 'ASAMA 2 - core.Main')


class Main:
    def __init__(self):
        self.pDialog = None
        self.run()

    def run(self):
        _safe_main()


if __name__ == '__main__':
    try:
        Main()
    except Exception:
        report_crash(traceback.format_exc(), 'default.py startup')
