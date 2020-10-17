# -*- coding: utf-8 -*-

import sys
import os
import json
import urllib
import xbmc, xbmcaddon, xbmcgui, xbmcplugin


class Downloader:

    def __init__(self):
        self.local_addon = xbmcaddon.Addon()
        self.local_id = self.local_addon.getAddonInfo('id')
        try:
            self.remote_id = 'plugin.video.downloader'
            self.remote_addon = xbmcaddon.Addon(self.remote_id)
            self.download_path = self.remote_addon.getSetting('download_path')
        except:
            self.remote_id = None
            self.remote_addon = None
            self.download_path = None

    def __available(self):
        return self.remote_addon is not None

    def __exists(self, contentid):
        filepath = os.path.join(self.download_path, self.local_id, '%s.mp4' % contentid)
        return os.path.isfile(filepath)

    def top(self, icon_image=None):
        if self.__available():
            listitem = xbmcgui.ListItem(self.remote_addon.getLocalizedString(30927), iconImage=icon_image, thumbnailImage=icon_image)
            listitem.setInfo(type='video', infoLabels={})
            action = 'RunPlugin(plugin://%s?action=settings)' % (self.remote_id)
            contextmenu = [(self.remote_addon.getLocalizedString(30937), action)]
            listitem.addContextMenuItems(contextmenu, replaceItems=True)
            url = 'plugin://%s?action=list&addonid=%s' % (self.remote_id, self.local_id)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    def contextmenu(self, item, url=None):
        contextmenu = []
        if self.__available():
            contentid = item.get('contentid', '')
            if self.__exists(contentid):
                action = 'RunPlugin(plugin://%s?action=delete&addonid=%s&contentid=%s)' % (self.remote_id, self.local_id, urllib.quote_plus(contentid))
                contextmenu = [(self.remote_addon.getLocalizedString(30930), action)]
            else:
                dumps = json.dumps(item)
                if url is None:
                    action = 'RunPlugin(plugin://%s?action=download&json=%s)' % (self.local_id, urllib.quote_plus(dumps))
                else:
                    action = 'RunPlugin(plugin://%s?action=add&addonid=%s&url=%s&json=%s)' % (self.remote_id, self.local_id,  urllib.quote_plus(url), urllib.quote_plus(dumps))
                contextmenu = [(self.remote_addon.getLocalizedString(30929), action)]
        return contextmenu

    def download(self, item, url):
        if self.__available():
            dumps = json.dumps(item)
            action = 'RunPlugin(plugin://%s?action=add&addonid=%s&url=%s&json=%s)' % (self.remote_id, self.local_id,  urllib.quote_plus(url),  urllib.quote_plus(dumps))
            xbmc.executebuiltin(action)
