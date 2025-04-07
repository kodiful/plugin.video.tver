# -*- coding: utf-8 -*-

import sys
import os
import re
import datetime
import json
import io
import re
import xbmcgui
import xbmcplugin

from urllib.parse import urlencode
from urllib.parse import quote_plus
from urllib.parse import parse_qs
from PIL import Image

from sqlite3 import dbapi2 as sqlite

from resources.lib.common import Common
from resources.lib.smartlist import SmartList
from resources.lib.downloader import Downloader


class Browse(Common):

    def __init__(self, query='weekday=all&tvnetwork=all&genre=all'):
        self.query = query
        self.args, _ = self.update_query(self.query)
        self.smartlist = SmartList()
        self.downloader = Downloader()

    def update_query(self, query, values=None):
        args = parse_qs(query, keep_blank_values=True)
        for key in args.keys():
            args[key] = args[key][0]
        args.update(values or {})
        return args, urlencode(args)

    def show_top(self):
        # 検索:曜日
        self.add_directory_item(name=self.STR(30933), query='', action='setweekday', iconimage=self.CALENDAR)
        # 検索:チャンネル
        self.add_directory_item(name=self.STR(30934), query='', action='settvnetwork', iconimage=self.RADIO_TOWER)
        # 検索:ジャンル
        self.add_directory_item(name=self.STR(30935), query='', action='setgenre', iconimage=self.CATEGORIZE)
        # ダウンロード
        self.downloader.top(self.DOWNLOADS)
        # スマートリスト
        for item in SmartList().getList():
            self.add_smartlist(item['keyword'], iconimage=self.BROWSE_FOLDER)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_weekday(self):
        genre_list = [
            ('all', self.STR(30830)),
            ('mon', self.STR(30831)),
            ('tue', self.STR(30832)),
            ('wed', self.STR(30833)),
            ('thu', self.STR(30834)),
            ('fri', self.STR(30835)),
            ('sat', self.STR(30836)),
            ('sun', self.STR(30837)),
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
            self.add_directory_item(name, query, action, iconimage=self.CATEGORIZE)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_tvnetwork(self):
        tvnetwork_list = [
            ('all', self.STR(30810)),
            ('nns', self.STR(30811)),
            ('exnetwork', self.STR(30812)),
            ('jnn', self.STR(30813)),
            ('txn', self.STR(30814)),
            ('fns', self.STR(30815)),
            ('nhknet', self.STR(30816)),
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
            self.add_directory_item(name, query, action, iconimage=self.RADIO_TOWER)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_genre(self):
        genre_list = [
            ('all', self.STR(30800)),
            ('drama', self.STR(30801)),
            ('variety', self.STR(30802)),
            ('news_documentary', self.STR(30803)),
            ('anime', self.STR(30804)),
            ('sports', self.STR(30805)),
            ('other', self.STR(30806)),
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
            self.add_directory_item(name, query, action, iconimage=self.CATEGORIZE)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def search(self):
        # 検索結果取得
        keyword = self.args.get('keyword', '')
        weekday = self.args.get('weekday', 'all')
        tvnetwork = self.args.get('tvnetwork', 'all')
        genre = self.args.get('genre', 'all')
        keys = list(filter(lambda key: key != 'all', [weekday, tvnetwork, genre]))
        if keyword:
            url = f'https://service-api.tver.jp/api/v1/callKeywordSearch?sortKey=score&filterKey={"%2C".join(keys)}&keyword={quote_plus(keyword)}'
            buf = self.request(url, {'x-tver-platform-type': 'web'})
            contents = json.loads(buf).get('result').get('contents')
            if len(contents) > 0:
                contents = list(filter(lambda x: x['score'] == 10, contents))
        elif len(keys) > 0:
            url = f'https://service-api.tver.jp/api/v1/callTagSearch/{keys[0]}?filterKey={"%2C".join(keys[1:])}'            
            buf = self.request(url, {'x-tver-platform-type': 'web'})
            contents = json.loads(buf).get('result').get('contents')
        else:
            url = f'https://service-api.tver.jp/api/v1/callNewerDetail/all'
            buf = self.request(url, {'x-tver-platform-type': 'web'})
            contents = json.loads(buf).get('result').get('contents').get('contents')
        # 表示
        for data in sorted(contents, key=lambda data: self._extract_date(data.get('content').get('broadcastDateLabel')), reverse=True):
            self.add_item(data.get('content'))
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def download(self, url, id):
        port = self.GET('port')
        url = f'http://127.0.0.1:{port}/download?{id}'
        self.downloader.download(url, id)

    def add_directory_item(self, name, query, action, iconimage=''):
        # listitem
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'icon': iconimage})
        # context menu
        contextmenu = []
        if query:
            contextmenu += [(self.STR(30936), 'Container.Update(%s,replace)' % sys.argv[0])]  # トップに戻る
        contextmenu += [(self.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])]  # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        url = '%s?action=%s&query=%s' % (sys.argv[0], action, quote_plus(query))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    def add_smartlist(self, keyword, iconimage=''):
        # listitem
        listitem = xbmcgui.ListItem(keyword)
        listitem.setArt({'icon': iconimage})
        # context menu
        contextmenu = []
        contextmenu += self.smartlist.contextmenu(sys.argv[0], keyword, True)  # スマートリストを変更
        contextmenu += [(self.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])]  # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        url = '%s?action=search&query=%s' % (sys.argv[0], urlencode({'keyword': keyword}))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

    def add_item(self, item):
        '''
        {
            "id": "epwyjk82m8",
            "version": 12,
            "title": "　",
            "seriesID": "srrao7paa6",
            "endAt": 1698076920,
            "broadcastDateLabel": "10月16日(月)放送分",
            "isNHKContent": false,
            "isSubtitle": false,
            "ribbonID": 0,
            "seriesTitle": "激レアさんを連れてきた。",
            "isAvailable": true,
            "broadcasterName": "テレビ朝日",
            "productionProviderName": "テレビ朝日"
        }
        '''
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
        thumbnail = self._create_thumbnail(id)
        # 番組情報
        pg = item['_summary'] = {
            'title': title,
            'url': f'https://statics.tver.jp/content/episode/{id}.json',
            'date': self._extract_date(date),
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
            'date': self._convert_date(pg['date']),
        }
        listitem = xbmcgui.ListItem(pg['title'])
        listitem.setArt({'icon': pg['thumbnail'], 'thumb': pg['thumbnail'], 'poster': pg['thumbnail']})
        listitem.setInfo(type='video', infoLabels=labels)
        listitem.setProperty('IsPlayable', 'true')
        # context menu
        contextmenu = []
        contextmenu += [(self.STR(30938), 'Action(Info)')]  # 詳細情報
        contextmenu += self.smartlist.contextmenu(sys.argv[0], title, False)  # スマートリストに追加
        contextmenu += self.downloader.contextmenu(item)  # ダウンロード追加/削除
        contextmenu += [(self.STR(30936), 'Container.Update(%s,replace)' % sys.argv[0])]  # トップに戻る
        contextmenu += [(self.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])]  # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        port = self.GET('port')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), f'http://127.0.0.1:{port}/play?{id}', listitem, False)

    def _extract_date(self, itemdate):
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

    def _convert_date(self, date):
        # listitem.date用に変換
        m = re.search('^([0-9]{4})-([0-9]{2})-([0-9]{2})', date)
        if m:
            date = '%s.%s.%s' % (m.group(3), m.group(2), m.group(1))
        return date

    def _create_thumbnail(self, id):
        # ファイルパス
        imagefile = os.path.join(self.IMG_CACHE, f'{id}.jpg')
        if os.path.isfile(imagefile) and os.path.getsize(imagefile) < 1000:
            # delete imagefile
            os.remove(imagefile)
            # delete from database
            conn = sqlite.connect(self.CACHE_DB)
            c = conn.cursor()
            # c.execute("SELECT cachedurl FROM texture WHERE url = '%s';" % imagefile)
            c.execute(f"DELETE FROM texture WHERE url = '{imagefile}';")
            conn.commit()
            conn.close()
        if os.path.isfile(imagefile):
            pass
        else:
            url = f'https://statics.tver.jp/images/content/thumbnail/episode/small/{id}.jpg'
            buffer = self.request(url, decode=False)
            image = Image.open(io.BytesIO(buffer))  # 320x180
            image = image.resize((216, 122))
            background = Image.new('RGB', (216, 216), (0, 0, 0))
            background.paste(image, (0, 47))
            background.save(imagefile, 'PNG')
        return imagefile
