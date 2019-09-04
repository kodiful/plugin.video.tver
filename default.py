# -*- coding: utf-8 -*-

import sys, os
import re
import datetime
import urllib, urlparse
import json
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

from resources.lib.common import urlread, log, notify, isholiday


class Const:

    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo('id')

    STR = ADDON.getLocalizedString

    # ディレクトリパス
    PLUGIN_PATH = xbmc.translatePath(ADDON.getAddonInfo('path').decode('utf-8'))
    RESOURCES_PATH = os.path.join(PLUGIN_PATH, 'resources')
    DATA_PATH = os.path.join(RESOURCES_PATH, 'data')
    IMAGE_PATH = os.path.join(DATA_PATH, 'image')

    # サムネイル
    CALENDAR    = os.path.join(IMAGE_PATH, 'icons8-calendar-filled-500.png')
    RADIO_TOWER = os.path.join(IMAGE_PATH, 'icons8-radio-tower-filled-500.png')
    CATEGORIZE  = os.path.join(IMAGE_PATH, 'icons8-categorize-filled-500.png')


class Browse:

    def __init__(self, query='bc=all&genre=all&bc=all'):
        self.query = query
        self.args = urlparse.parse_qs(self.query, keep_blank_values=True)

    def show(self, action):
        if action == 'top':
            self.show_top()
        elif action == 'date':
            self.show_date()
        elif action == 'channel':
            self.show_channel()
        elif action == 'genre':
            self.show_genre()

    def show_top(self):
        # 検索:日付
        self.__add_directory_item(Const.STR(30933),'',11,thumbnail=Const.CALENDAR,context='top')
        # 検索:チャンネル
        self.__add_directory_item(Const.STR(30934),'',12,thumbnail=Const.RADIO_TOWER,context='top')
        # 検索:ジャンル
        self.__add_directory_item(Const.STR(30935),'',13,thumbnail=Const.CATEGORIZE,context='top')
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_date(self):
        # すべての日付
        name = Const.STR(30820)
        # 月,火,水,木,金,土,日
        w = Const.STR(30920).split(',')
        # 次のアクション
        if self.args.get('bc') is None:
            mode = 12
        elif self.args.get('genre') is None:
            mode = 13
        else:
            mode = 15
        query = '%s&%s' % (self.query, urllib.urlencode({'date':''}))
        self.__add_directory_item(name,query,mode,thumbnail=Const.CALENDAR)
        # 直近30日分のメニューを追加
        for i in range(30):
            d = datetime.date.today() - datetime.timedelta(i)
            wd = d.weekday()
            # 8月31日(土)
            date1 = d.strftime(Const.STR(30919).encode('utf-8','ignore')).decode('utf-8') % w[wd]
            # 2019-08-31
            date2 = d.strftime('%Y-%m-%d')
            if isholiday(date2) or wd == 6:
                name = '[COLOR red]%s[/COLOR]' % date1
            elif wd == 5:
                name = '[COLOR blue]%s[/COLOR]' % date1
            else:
                name = date1
            query = '%s&%s' % (self.query, urllib.urlencode({'date':date2}))
            self.__add_directory_item(name,query,mode,thumbnail=Const.CALENDAR)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_channel(self):
        bc_list = [
            ('', Const.STR(30810)),
            ('ntv', Const.STR(30811)),
            ('ex', Const.STR(30812)),
            ('tbs', Const.STR(30813)),
            ('tx', Const.STR(30814)),
            ('cx', Const.STR(30815)),
            ('nhk', Const.STR(30816)),
        ]
        for id, name in bc_list:
            # 次のアクション
            if self.args.get('genre') is None:
                mode = 13
            elif self.args.get('date') is None:
                mode = 11
            else:
                mode = 15
            query = '%s&%s' % (self.query, urllib.urlencode({'bc':id}))
            self.__add_directory_item(name,query,mode,thumbnail=Const.RADIO_TOWER)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_genre(self):
        genre_list = [
            ('', Const.STR(30800)),
            ('drama', Const.STR(30801)),
            ('variety', Const.STR(30802)),
            ('documentary', Const.STR(30803)),
        	('anime', Const.STR(30804)),
        	('sport', Const.STR(30805)),
        	('other', Const.STR(30806)),
        ]
        for id, name in genre_list:
            # 次のアクション
            if self.args.get('bc') is None:
                mode = 12
            elif self.args.get('date') is None:
                mode = 11
            else:
                mode = 15
            query = '%s&%s' % (self.query, urllib.urlencode({'genre':id}))
            self.__add_directory_item(name,query,mode,thumbnail=Const.CATEGORIZE)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def search(self):
        # トークンを取得
        url = 'https://tver.jp/api/access_token.php'
        buf = urlread(url)
        jso = json.loads(buf)
        token = jso.get('token','').encode('utf-8')
        # 番組検索
        url = 'https://api.tver.jp/v4/search?catchup=1&%s&token=%s' % (self.query, token)
        buf = urlread(url)
        log(url)
        log(buf)
        jso = json.loads(buf)
        for data in jso.get('data', []):
            self.__add_item(data)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def play(self):
        # 番組詳細を取得
        url = self.query
        buf = urlread(url)
        args = map(lambda x:x.strip(" '\t"), re.search('addPlayer\((.*?)\);', re.sub(r'\n',' ',buf)).group(1).split(','))
        # ポリシーキーを取得
        url = 'https://players.brightcove.net/%s/%s_default/index.min.js' % (args[0], args[1])
        buf = urlread(url)
        pk = re.search('a.catalog\(\{accountId:accountId,policyKey:"(.*?)"\}\);', buf).group(1)
        # HLSマスターのURLを取得
        url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/videos/ref:%s' % (args[3], args[4])
        buf = urlread(url, ('Accept','application/json;pk=%s' % pk))
        jso = json.loads(buf)
        src = jso.get('sources')[4].get('src')
        xbmc.executebuiltin('PlayMedia(%s)' % src)

    def __add_item(self, data):
        name = data.get('title')
        url = 'https://tver.jp%s' % data.get('href')
        mode = 16
        image = data.get('images')[0]
        labels = {
            'title': data.get('title'),
            'studio': data.get('media'),
            'date': data.get('date'),
            'genre': '%s %s' % (data.get('media'),data.get('date'))
        }
        self.__add_directory_item(name, url, mode, image['small'], labels)

    def __add_directory_item(self, name, url, mode, thumbnail='', labels=None, context=None):
        # listitem
        listitem = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)
        listitem.setInfo(type='video', infoLabels=labels or {})
        # context menu
        contextMenu = []
        if context:
            # トップに戻る
            action = 'Container.Update(%s,replace)' % (sys.argv[0])
            contextMenu.append((Const.STR(30936),action))
        # アドオン設定
        contextMenu.append((Const.STR(30937),'RunPlugin(%s?mode=82)' % sys.argv[0]))
        listitem.addContextMenuItems(contextMenu, replaceItems=True)
        # add directory item
        url = '%s?url=%s&mode=%s' % (sys.argv[0], urllib.quote_plus(url), mode)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)


if __name__  == '__main__':

    # パラメータ抽出
    args = urlparse.parse_qs(sys.argv[2][1:], keep_blank_values=True)
    for key in args.keys():
        args[key] = args[key][0]
    mode = args.get('mode', '')
    url  = args.get('url',  '')

    # top
    if mode=='':
        Browse().show('top')

    # browse date
    elif mode=='11':
        Browse(url).show('date')

    # browse channel
    elif mode=='12':
        Browse(url).show('channel')

    # browse genre
    elif mode=='13':
        Browse(url).show('genre')

    # search
    elif mode=='15':
        Browse(url).search()

    # play
    elif mode=='16':
        Browse(url).play()

    # open settings
    elif mode=='82':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % Const.ADDON_ID)
