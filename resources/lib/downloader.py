# -*- coding: utf-8 -*-

#
# plugin.video.garapon.tv/resources/lib/downloader.py
#

import sys
import os
import sqlite3
from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


class Downloader:

    def __init__(self):
        self.local_addon = xbmcaddon.Addon()
        self.local_id = self.local_addon.getAddonInfo('id')
        try:
            self.remote_id = 'plugin.video.downloader'
            self.remote_addon = xbmcaddon.Addon(self.remote_id)
            self.download_path = self.remote_addon.getSetting('download_path')
            self.db_path = os.path.join(xbmcvfs.translatePath(self.remote_addon.getAddonInfo('profile')), 'download.db')
            self.available = True
        except Exception:
            self.available = False

    # トップページに配置するダウンロードアイテム
    def top(self, iconimage=None):
        if self.available:
            listitem = xbmcgui.ListItem(self.remote_addon.getLocalizedString(30927))
            listitem.setArt({'icon': iconimage})
            listitem.setInfo(type='video', infoLabels={})
            action = 'RunPlugin(plugin://%s?action=settings)' % (self.remote_id)
            contextmenu = [(self.remote_addon.getLocalizedString(30937), action)]
            listitem.addContextMenuItems(contextmenu, replaceItems=True)
            url = 'plugin://%s?action=listitems&addonid=%s' % (self.remote_id, self.local_id)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    # 検索結果に設定するダウンロードメニュー（コンテクストメニュー）
    def contextmenu(self, summary, resolved=True):
        contextmenu = []
        if self.available:
            contentid = summary['contentid']
            url = summary['url']
            # サマリ情報をキャッシュする
            conn = sqlite3.connect(self.db_path, isolation_level=None)
            cursor = conn.cursor()
            data = {'addonid': self.local_id}
            data.update(summary)
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f'INSERT OR REPLACE INTO cache ({columns}) VALUES ({placeholders})'
            cursor.execute(sql, list(data.values()))
            conn.close()
            # mp4ファイルの有無を確認する
            mp4_file = os.path.join(self.download_path, self.local_id, '%s.mp4' % contentid)
            if os.path.isfile(mp4_file):
                # mp4ファイルがある場合は削除メニュー
                args = {'action': 'delete', 'addonid': self.local_id, 'contentid': contentid}
                contextmenu = [(self.remote_addon.getLocalizedString(30930), 'RunPlugin(plugin://%s?%s)' % (self.remote_id, urlencode(args)))]
            else:
                # mp4ファイルがある場合は追加メニュー
                if resolved:
                    args = {'action': 'add', 'addonid': self.local_id, 'contentid': contentid, 'url': url}
                    contextmenu = [(self.remote_addon.getLocalizedString(30929), 'RunPlugin(plugin://%s?%s)' % (self.remote_id, urlencode(args)))]
                else:
                    # resolveされていない場合はローカル側でaction=downloadを実装 -> resolveされたurlでDownloader().downloadを実行する
                    args = {'action': 'download', 'contentid': contentid, 'url': url}
                    contextmenu = [(self.remote_addon.getLocalizedString(30929), 'RunPlugin(plugin://%s?%s)' % (self.local_id, urlencode(args)))]
        return contextmenu    

    # ローカルでresolve後に実行するダウンロードメソッド
    def download(self, contentid, url):
        if self.available:
            args = {'action': 'add', 'addonid': self.local_id, 'contentid': contentid, 'url': url}
            xbmc.executebuiltin('RunPlugin(plugin://%s?%s)' % (self.remote_id, urlencode(args)))
