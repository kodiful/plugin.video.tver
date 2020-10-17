# -*- coding: utf-8 -*-

import sys, os
import re
import datetime, time
import urllib, urlparse
import json
import xbmc, xbmcgui, xbmcplugin

from common import *
from downloader import Downloader


class Browse:

    def __init__(self, query='bc=all&genre=all&bc=all'):
        self.query = query
        self.args, _ = self.update_query(self.query)
        self.downloader = Downloader()

    def update_query(self, query, values=None):
        args = urlparse.parse_qs(query, keep_blank_values=True)
        for key in args.keys():
            args[key] = args[key][0]
        args.update(values or {})
        return args, urllib.urlencode(args)

    def show_top(self):
        # ダウンロード
        self.downloader.top(Const.DOWNLOADS)
        # 検索:日付
        self.__add_directory_item(Const.STR(30933),'','setdate',thumbnail=Const.CALENDAR,context='top')
        # 検索:チャンネル
        self.__add_directory_item(Const.STR(30934),'','setchannel',thumbnail=Const.RADIO_TOWER,context='top')
        # 検索:ジャンル
        self.__add_directory_item(Const.STR(30935),'','setgenre',thumbnail=Const.CATEGORIZE,context='top')
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_date(self):
        # すべての日付
        name = Const.STR(30820)
        # 月,火,水,木,金,土,日
        w = Const.STR(30920).split(',')
        # 次のアクション
        if self.args.get('bc') is None:
            action = 'setchannel'
        elif self.args.get('genre') is None:
            action = 'setgenre'
        else:
            action = 'search'
        _, query = self.update_query(self.query, {'date':''})
        self.__add_directory_item(name, query, action, thumbnail=Const.CALENDAR, context='date')
        # 直近30日分のメニューを追加
        for i in range(30):
            d = datetime.date.today() - datetime.timedelta(i)
            wd = d.weekday()
            # 8月31日(土)
            date1 = d.strftime(Const.STR(30919).encode('utf-8')).decode('utf-8') % w[wd]
            # 2019-08-31
            date2 = d.strftime('%Y-%m-%d')
            if isholiday(date2) or wd == 6:
                name = '[COLOR red]%s[/COLOR]' % date1
            elif wd == 5:
                name = '[COLOR blue]%s[/COLOR]' % date1
            else:
                name = date1
            _, query = self.update_query(self.query, {'date':date2})
            self.__add_directory_item(name, query, action, thumbnail=Const.CALENDAR, context='date')
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
                action = 'setgenre'
            elif self.args.get('date') is None:
                action = 'setdate'
            else:
                action = 'search'
            _, query = self.update_query(self.query, {'bc':id})
            self.__add_directory_item(name, query, action, thumbnail=Const.RADIO_TOWER, context='channel')
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
                action = 'setchannel'
            elif self.args.get('date') is None:
                action = 'setdate'
            else:
                action = 'search'
            _, query = self.update_query(self.query, {'genre':id})
            self.__add_directory_item(name, query, action, thumbnail=Const.CATEGORIZE, context='genre')
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def search(self):
        # トークンを取得
        url = 'https://tver.jp/api/access_token.php'
        buf = urlread(url)
        jso = json.loads(buf)
        token = jso.get('token','')
        # 番組検索
        url = 'https://api.tver.jp/v4/search?catchup=1&%s&token=%s' % (self.query, token)
        buf = urlread(url)
        datalist = json.loads(buf).get('data',[])
        for data in sorted(datalist, key=lambda item: self.__date(item)[0], reverse=True):
            '''
            {
                "bool": {
                    "cast": 1
                },
                "catchup_id": "f0058710",
                "date": "7月14日(火)放送分",
                "expire": "10月21日(水) 00:53 終了予定",
                "ext": {
                    "adconfigid": null,
                    "allow_scene_share": true,
                    "catch": "",
                    "episode_number": "598",
                    "is_caption": false,
                    "live_lb_type": null,
                    "multiple_catchup": false,
                    "share_secret": "c950d127003629617cc5fffbcbde3c95",
                    "site_catch": "",
                    "stream_id": null,
                    "yospace_id": null
                },
                "href": "/feature/f0058710",
                "images": [
                    {
                        "image": "https://api-cdn.tver.jp/s3/@202010/image/@20201007/638c1baf-3a27-47f2-92f0-54038255ab77.jpg",
                        "large": "https://api-cdn.tver.jp/s3/@202010/large/@20201007/2444cd40-0558-4d18-923a-3496745ebbf0.jpg",
                        "right": "(C) ytv",
                        "small": "https://api-cdn.tver.jp/s3/@202010/small/@20201007/07009320-8d91-4308-85c4-7277758f03b3.jpg",
                        "type": "e_cut"
                    }
                ],
                "media": "読売テレビ",
                "mylist_id": "f0009802",
                "player": "videocloud",
                "pos": "/search",
                "publisher_id": "5330942432001",
                "reference_id": "Niketsu_598_200715",
                "service": "ts_ytv",
                "subtitle": "ジュニア衝撃ぬるいカップ麺＆芸人名言",
                "title": "にけつッ!!",
                "type": "catchup",
                "url": "http://www.ytv.co.jp/niketsu/"
            }
            '''
            # 表示
            self.__add_item(convert(data))
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def play(self, item):
        url = self.__extract_url(item)
        xbmc.executebuiltin('PlayMedia(%s)' % url)

    def download(self, item):
        url = self.__extract_url(item)
        self.downloader.download(item, url)

    def __extract_url(self, item):
        # 番組詳細を取得
        #
        # https://tver.jp/episode/77607556
        #
        url = item['_summary']['url']
        buf = urlread(url)
        args = {}
        keys = ('player_id','player_key','catchup_id','publisher_id','reference_id','title','sub_title','service','service_name','sceneshare_enabled','share_start')
        '''
        function showPlayer(){
        	if( canPlayMovie() ){
        		addPlayer(
        			'4394098882001',
        			'TtyB0eZ4Y',
        			'f0058835',
        			'4394098882001',
        			'104da7b3-2df3-491a-bab2-5f08793e608a',
        			'ぶらり途中下車の旅',
        			' 小田急線',
        			'ntv',
        			'日テレ無料',
        			true,
        			0
        		);
        	}else{
        		addSpPlayer(
        			'f0058835',
        			'ぶらり途中下車の旅',
        			' 小田急線',
        			'ntv',
        			'日テレ無料',
        			'https%3A%2F%2Ftver.jp%2Fepisode%2F77607556',
        			'',
        			'104da7b3-2df3-491a-bab2-5f08793e608a',
        			0,
        			''
        		);
        	}
        }
        '''
        vals = map(lambda x:x.strip(" '\t"), re.search(r'addPlayer\((.*?)\);', re.sub(r'\n',' ',buf)).group(1).split(','))
        for key, val in zip(keys,vals):
            args[key] = val
        # ポリシーキーを取得
        #
        # https://players.brightcove.net/4394098882001/TtyB0eZ4Y_default/index.min.js?_=1602300285436
        #
        url = 'https://players.brightcove.net/%s/%s_default/index.min.js' % (args['player_id'], args['player_key'])
        buf = urlread(url)
        #
        # options:{accountId:"4394098882001",policyKey:"BCpkADawqM1l5pA4XtMLusHj72LGzFewqKZzldpmNYTUQdoKnFL_GHhN3dg5FRnNQ5V7SOUKBl-tYFMt8CpSzuSzFAPhIHtVwmMz6F52VnMfu2UjDmeYfvvUqk0CWon46Yh-CZwIVp5vfXrZ"}
        #
        pk = re.search(r'options:\{accountId:"(.*?)",policyKey:"(.*?)"\}', buf).group(2)
        # HLSマスターのURLを取得
        if args['service'] != 'tx' and args['service'] != 'russia2018' and args['service'] != "gorin":
            ref_id = 'ref:' + args['reference_id']
        else:
            ref_id = args['reference_id']
        #
        # https://edge.api.brightcove.com/playback/v1/accounts/5102072603001/videos/ref%3Asunday_variety_episode_code_6950
        #
        url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/videos/%s' % (args['publisher_id'], ref_id)
        buf = urlread(url, ('Accept','application/json;pk=%s' % pk))
        jso = json.loads(buf)
        src = jso.get('sources')[3].get('src')
        #
        # https://manifest.prod.boltdns.net/manifest/v1/hls/v4/aes128/4394098882001/15157782-1259-4ba1-b9e6-ee7298b261f6/10s/master.m3u8?fastly_token=NWZhNjY1MTVfNGIyZjQzZDc0ZTg0YmY3NTg0OTE1YThjOGQzZjk2NDk5NTcyMzU4N2ViYzFiZDY2NDBjN2QwZWMxNTIwYjZmNw%3D%3D
        #
        return src

    def __date(self, item):
        # データの時刻情報
        itemdate = item.get('date', '')
        if isinstance(itemdate, unicode): itemdate = itemdate.encode('utf-8')
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
            date1 = '%02d-%02d' % (int(m.group(1)),int(m.group(2)))
            date = '%04d-%s' % (int(year0)-1 if date1>date0 else int(year0), date1)
        m = re.match(r'([0-9]{1,2})/([0-9]{1,2})', itemdate)
        if m:
            date1 = '%02d-%02d' % (int(m.group(1)),int(m.group(2)))
            date = '%04d-%s' % (int(year0) if date1<date0 else int(year0)-1, date1)
        # 抽出結果
        return date

    def __date2label(self, date):
        # listitem.date用に変換
        m = re.search('^([0-9]{4})-([0-9]{2})-([0-9]{2})', date)
        if m:
            date = '%s.%s.%s' % (m.group(3),m.group(2),m.group(1))
        return date

    def __contentid(self, item):
        publisher_id = item.get('publisher_id')
        reference_id = item.get('reference_id')
        contentid = '%s.%s' % (publisher_id, reference_id)
        return contentid

    def __add_item(self, item):
        name = item.get('title')
        action = 'play'
        thumbnail = item['images'][0]['small']
        # 番組情報
        item['_summary'] = {
            'title': item['title'],
            'url': 'https://tver.jp%s' % item['href'],
            'date': self.__date(item),
            'description': item['subtitle'],
            'source': item['media'],
            'category': '',
            'duration': '',
            'thumbnail': item['images'][0]['small'],
            'thumbfile': '',
            'contentid': self.__contentid(item),
        }
        # add directory item
        self.__add_directory_item(name, '', action, thumbnail, item)

    def __add_directory_item(self, name, query, action, thumbnail='', item=None, context=None):
        # listitem
        listitem = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)
        if item:
            s = item['_summary']
            labels = {
                'title': s['title'],
                'plot': '%s\n%s' % (s['date'], s['description']),
                'plotoutline': s['description'],
                'studio': s['source'],
                'date': self.__date2label(s['date']),
            }
            listitem.setInfo(type='video', infoLabels=labels)
        else:
            listitem.setInfo(type='video', infoLabels={})
        # context menu
        contextmenu = []
        if context != 'top':
            contextmenu += [(Const.STR(30936), 'Container.Update(%s,replace)' % sys.argv[0])] # トップに戻る
        if context is None:
            contextmenu += self.downloader.contextmenu(item) # ダウンロード
        contextmenu += [(Const.STR(30937), 'RunPlugin(%s?action=settings)' % sys.argv[0])] # アドオン設定
        listitem.addContextMenuItems(contextmenu, replaceItems=True)
        # add directory item
        if item:
            dumps = json.dumps(item)
            url = '%s?action=%s&query=%s&json=%s' % (sys.argv[0], action, urllib.quote_plus(query), urllib.quote_plus(dumps))
        else:
            url = '%s?action=%s&query=%s' % (sys.argv[0], action, urllib.quote_plus(query))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)