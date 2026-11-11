import xbmcaddon

__plugin__ = 'Misc Pack'
__author__ = 'sfaxman'
__credits__ = 'bootsy'

addon = xbmcaddon.Addon(id='plugin.video.miscpack2')
rootDir = addon.getAddonInfo('path')
if rootDir.endswith(';'):
    rootDir = rootDir[:-1]

class Main:
    def __init__(self):
        self.pDialog = None
        self.run()

    def run(self):
        import core
        core.Main()

Main()
