# -*- coding: utf-8 -*-

import sys
import os
import urllib
import xbmc, xbmcaddon, xbmcgui, xbmcplugin


class Downloader:

    def __init__(self):
        try:
            self.local_addon = xbmcaddon.Addon()
            self.local_id = self.local_addon.getAddonInfo('id')
            self.remote_id = 'plugin.video.downloader'
            self.remote_addon = xbmcaddon.Addon(self.remote_id)
            self.download_path = self.remote_addon.getSetting('download_path')
        except:
            self.local_addon = None
            self.local_id = None
            self.remote_id = None
            self.remote_addon = None
            self.download_path = None
        return

    def __available(self):
        return self.remote_addon is not None

    def __exists(self, filename):
        filepath = os.path.join(self.download_path, self.local_id, '%s.mp4' % filename)
        return os.path.isfile(filepath)

    def top(self):
        if self.__available():
            listitem = xbmcgui.ListItem(self.remote_addon.getLocalizedString(30927))
            listitem.setInfo(type='video', infoLabels={})
            url = 'plugin://%s?action=list&addonid=%s' % (self.remote_id, self.local_id)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    def menu(self, item):
        if self.__available():
            filename = item.get('filename', '')
            if self.__exists(filename):
                action = 'RunPlugin(plugin://%s?action=delete&addonid=%s&filename=%s)' % (self.remote_id, self.local_id, urllib.quote_plus(filename))
                menu = (self.remote_addon.getLocalizedString(30930), action)
            else:
                action = 'RunPlugin(plugin://%s?action=download&%s)' % (self.local_id, urllib.urlencode(item))
                menu = (self.remote_addon.getLocalizedString(30929), action)
            return menu

    def download(self, item, url):
        if self.__available():
            action = 'RunPlugin(plugin://%s?action=add&addonid=%s&url=%s&%s)' % (self.remote_id, self.local_id,  urllib.quote_plus(url),  urllib.urlencode(item))
            xbmc.executebuiltin(action)
