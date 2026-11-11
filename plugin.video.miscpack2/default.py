# -*- coding: utf-8 -*-
import sys
import os.path
import traceback

import xbmcaddon

__plugin__ = 'Misc Pack 2'
__author__ = 'sfaxman'
__credits__ = 'bootsy'

ADDON_ID = 'plugin.video.miscpack2'


def _heading_text(s):
    try:
        s = s.encode('utf-8')  # Python 2 dialogs want bytes
    except AttributeError:
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
            path = os.path.join(sd, 'miscpack2_crash.txt')
            f = open(path, 'w')
            f.write(tb_text)
            f.close()
    except Exception:
        pass
    try:
        import xbmcgui
        lines = tb_text.strip().splitlines()
        msg = '[%s]\n%s\n%s' % (where, lines[-2] if len(lines) > 1 else '', lines[-1])
        if path:
            msg = msg + '\nDetay: ' + path
        xbmcgui.Dialog().ok(_heading_text('Misc Pack 2 Crash'), _heading_text(msg))
    except Exception:
        pass


def _safe_main():
    try:
        import core
        core.Main()
    except Exception:
        report_crash(traceback.format_exc(), 'core.Main / import core')


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
