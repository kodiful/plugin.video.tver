# -*- coding: utf-8 -*-

import sys
import os
import re
import datetime
import json
import io

import xbmcgui
import xbmcplugin

from .common import *

from urllib.parse import urlencode
from urllib.parse import quote_plus
from urllib.parse import parse_qs
from PIL import Image

try:
    from sqlite3 import dbapi2 as sqlite
except Exception:
    from pysqlite2 import dbapi2 as sqlite

from resources.lib.common import *
from resources.lib.downloader import Downloader


class Browse:

    def __init__(self, query='weekday=all&tvnetwork=all&genre=all'):
        self.query = query
        self.args, _ = self.update_query(self.query)
        self.downloader = Downloader()

    def update_query(self, query, values=None):
        args = parse_qs(query, keep_blank_values=True)
        for key in args.keys():
            args[key] = args[key][0]
        args.update(values or {})
        return args, urlencode(args)

    def show_top(self):
        # 検索:曜日
        self.__add_directory_item(name=Const.STR(30933), query='', action='setweekday', iconimage=Const.CALENDAR)
        # 検索:チャンネル
        self.__add_directory_item(name=Const.STR(30934), query='', action='settvnetwork', iconimage=Const.RADIO_TOWER)
        # 検索:ジャンル
        self.__add_directory_item(name=Const.STR(30935), query='', action='setgenre', iconimage=Const.CATEGORIZE)
        # ダウンロード
        self.downloader.top(Const.DOWNLOADS)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_weekday(self):
        genre_list = [
            ('all', Const.STR(30830)),
            ('mon', Const.STR(30831)),
            ('tue', Const.STR(30832)),
            ('wed', Const.STR(30833)),
            ('thu', Const.STR(30834)),
            ('fri', Const.STR(30835)),
            ('sat', Const.STR(30836)),
            ('sun', Const.STR(30837)),
        ]
        for id, name in genre_list:
            # 次のアクション
            if self.args.get('tvnetwork') is None:
                action = 'settvnetwork'
            elif self.args.get('genre') is None:
                action = 'setgenre'
            else:
                action = 'search'
            _, query = self.update_query(self.query, {'weekday': id})
            self.__add_directory_item(name, query, action, iconimage=Const.CATEGORIZE)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_tvnetwork(self):
        tvnetwork_list = [
            ('all', Const.STR(30810)),
            ('nns', Const.STR(30811)),
            ('exnetwork', Const.STR(30812)),
            ('jnn', Const.STR(30813)),
            ('txn', Const.STR(30814)),
            ('fns', Const.STR(30815)),
            ('nhknet', Const.STR(30816)),
        ]
        for id, name in tvnetwork_list:
            # 次のアクション
            if self.args.get('genre') is None:
                action = 'setgenre'
            elif self.args.get('weekday') is None:
                action = 'setweekday'
            else:
                action = 'search'
            _, query = self.update_query(self.query, {'tvnetwork': id})
            self.__add_directory_item(name, query, action, iconimage=Const.RADIO_TOWER)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_genre(self):
        genre_list = [
            ('all', Const.STR(30800)),
            ('drama', Const.STR(30801)),
            ('variety', Const.STR(30802)),
            ('news_documentary', Const.STR(30803)),
            ('anime', Const.STR(30804)),
            ('sports', Const.STR(30805)),
            ('other', Const.STR(30806)),
        ]
        for id, name in genre_list:
            # 次のアクション
            if self.args.get('tvnetwork') is None:
                action = 'settvnetwork'
            elif self.args.get('weekday') is None:
                action = 'setweekday'
            else:
                action = 'search'
            _, query = self.update_query(self.query, {'genre': id})
            self.__add_directory_item(name, query, action, iconimage=Const.CATEGORIZE)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def search(self):
        # 検索結果取得
        weekday = self.args.get('weekday', 'all')
        tvnetwork = self.args.get('tvnetwork', 'all')
        genre = self.args.get('genre', 'all')
        keys = list(filter(lambda key: key != 'all', [weekday, tvnetwork, genre]))
        if len(keys) > 0:
            url = f'https://service-api.tver.jp/api/v1/callTagSearch/{keys[0]}?filterKey={"%2C".join(keys[1:])}'
            buf = urlread(url, ('x-tver-platform-type', 'web'))
            contents = json.loads(buf).get('result').get('contents')
        else:
            url = f'https://service-api.tver.jp/api/v1/callNewerDetail/all'
            buf = urlread(url, ('x-tver-platform-type', 'web'))
            contents = json.loads(buf).get('result').get('contents').get('contents')
        # 表示
        for data in sorted(contents, key=lambda data: self.__date(data.get('content').get('broadcastDateLabel')), reverse=True):
            self.__add_item(data.get('content'))
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __url(self, url):
        # episodeをダウンロード
        # https://statics.tver.jp/content/episode/epv3o3rrpl.json?v=18
        buf = urlread(url)
        episode = json.loads(buf)
        # "video": {
        #     "videoRefID": "37255_37254_38777",
        #     "accountID": "4394098883001",
        #     "playerID": "MfxS5MXtZ",
        #     "channelID": "ex"
        # },
        video = episode.get('video')
        videoRefID = video.get('videoRefID')
        accountID = video.get('accountID')
        playerID = video.get('playerID')
        # ポリシーキーを取得
        #　https://players.brightcove.net/4394098883001/MfxS5MXtZ_default/index.min.js
        url = f'https://players.brightcove.net/{accountID}/{playerID}_default/index.min.js'
        buf = urlread(url)
        # {accountId:"4394098883001",policyKey:"BCpkADawqM2XqfdZX45o9xMUoyUbUrkEjt-dMFupSdYwCw6YH7Dgd_Aj4epNSPEGgyBOFGHmLa_IPqbf8qv8CWSZaI_8Cd8xkpoMSNkyZrzzX7_TGRmVjAmZ_q_KxemVvC2gsMyfCqCzRrRx"}        
        policykey = re.search(r'options:\{accountId:"(.*?)",policyKey:"(.*?)"\}', buf.decode()).group(2)
        # playbackをダウンロード
        url = f'https://edge.api.brightcove.com/playback/v1/accounts/{accountID}/videos/ref%3A{videoRefID}'
        buf = urlread(url, ('accept', f'application/json;pk={policykey}'))
        playback = json.loads(buf)
        sources = playback.get('sources')
        filtered = filter(lambda source: source.get('ext_x_version') and source.get('src').startswith('https://'), sources)
        url = list(filtered)[-1].get('src')
        return url

    def play(self, url):
        url = self.__url(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), succeeded=True, listitem=xbmcgui.ListItem(path=url))

    def download(self, url, contentid):
        url = self.__url(url)
        self.downloader.download(url, contentid)

    def __add_item(self, item):
        # ID
        id = item.get('id')
        # 日付
        date = item.get('broadcastDateLabel')
        # タイトル
        title = []
        if date:
            title.append(date)
        if item.get('seriesTitle'):
            title.append(item.get('seriesTitle'))
        elif item.get('title'):
            title.append(item.get('title'))
        title = ' '.join(title)
        # 詳細
        description = []
        if item.get('title'):
            description.append(item.get('title'))
        if item.get('broadcastDateLabel'):
            description.append(item.get('broadcastDateLabel'))
        description = '\n'.join(description)
        # 放送局
        broadcasterName = item.get('broadcasterName')
        # サムネイル
        #thumbnail = f'https://statics.tver.jp/images/content/thumbnail/episode/small/{id}.jpg'
        thumbnail = self.__thumbnail(id)
        # URL
        url = f'https://statics.tver.jp/content/episode/{id}.json'
        # 番組情報
        pg = item['_summary'] = {
            'title': title,
            'url': url,
            'date': self.__date(date),
            'description': description,
            'source': broadcasterName,
            'category': '',
            'duration': '',
            'thumbnail': thumbnail,
            'thumbfile': thumbnail,
            'contentid': id,
        }
        # listitem
        labels = {
            'title': pg['title'],
            'plot': pg['description'],
            'plotoutline': pg['description'],
            'studio': pg['source'],
            'date': self.__labeldate(pg['date']),
        }
        listitem = xbmcgui.ListItem(pg['title'])
        listitem.setArt({'icon': pg['thumbnail'], 'thumb': pg['thumbnail'], 'poster': pg['thumbnail']})
        listitem.setInfo(type='video', infoLabels=labels)
        listitem.setProperty('IsPlayable', 'true')
        # context menu
        contextmenu = []
        contextmenu += [(Const.STR(30938), 'Action(Info)')]  # 詳細情報
        contextmenu += self.downloader.contextmenu(item)  # ダウンロード追加/削除
        contextmenu += [(Const.STR(30936), 'Container.Update(%s,replace)' % sys.argv[0])]  # トップに戻る
        contextmenu += [(Const.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])]  # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        url = '%s?action=%s&url=%s' % (sys.argv[0], 'play', quote_plus(pg['url']))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

    def __add_directory_item(self, name, query, action, iconimage=''):
        # listitem
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'icon': iconimage})
        # context menu
        contextmenu = []
        if query:
            contextmenu += [(Const.STR(30936), 'Container.Update(%s,replace)' % sys.argv[0])]  # トップに戻る
        contextmenu += [(Const.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])]  # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        url = '%s?action=%s&query=%s' % (sys.argv[0], action, quote_plus(query))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    def __date(self, itemdate):
        # 現在時刻
        now = datetime.datetime.now()
        year0 = now.strftime('%Y')
        date0 = now.strftime('%m-%d')
        # 日時を抽出
        date = '0000-00-00'
        m = re.match(r'(20[0-9]{2})年', itemdate)
        if m:
            date = '%s-00-00' % (m.group(1))
        m = re.match(r'([0-9]{1,2})月([0-9]{1,2})日', itemdate)
        if m:
            date1 = '%02d-%02d' % (int(m.group(1)), int(m.group(2)))
            date = '%04d-%s' % (int(year0) - 1 if date1 > date0 else int(year0), date1)
        m = re.match(r'([0-9]{1,2})/([0-9]{1,2})', itemdate)
        if m:
            date1 = '%02d-%02d' % (int(m.group(1)), int(m.group(2)))
            date = '%04d-%s' % (int(year0) if date1 < date0 else int(year0) - 1, date1)
        # 抽出結果
        return date

    def __labeldate(self, date):
        # listitem.date用に変換
        m = re.search('^([0-9]{4})-([0-9]{2})-([0-9]{2})', date)
        if m:
            date = '%s.%s.%s' % (m.group(3), m.group(2), m.group(1))
        return date

    def __thumbnail(self, id):
        # ファイルパス
        imagefile = os.path.join(Const.CACHE_PATH, f'{id}.jpg')
        if os.path.isfile(imagefile) and os.path.getsize(imagefile) < 1000:
            # delete imagefile
            os.remove(imagefile)
            # delete from database
            conn = sqlite.connect(Const.CACHE_DB)
            c = conn.cursor()
            # c.execute("SELECT cachedurl FROM texture WHERE url = '%s';" % imagefile)
            c.execute(f"DELETE FROM texture WHERE url = '{imagefile}';")
            conn.commit()
            conn.close()
        if os.path.isfile(imagefile):
            pass
        else:
            url = f'https://statics.tver.jp/images/content/thumbnail/episode/small/{id}.jpg'
            buffer = urlread(url)
            image = Image.open(io.BytesIO(buffer))  # 320x180
            image = image.resize((216, 122))
            background = Image.new('RGB', (216, 216), (0, 0, 0))
            background.paste(image, (0, 47))
            background.save(imagefile, 'PNG')
        return imagefile
