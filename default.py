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
        jso = json.loads(buf)
        for data in sorted(jso.get('data',[]), key=lambda d: (self.__extract_date(d), d.get('media')), reverse=True):
            self.__add_item(data)
        # end of directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def play(self):
        # 番組詳細を取得
        #
        # https://tver.jp/episode/77607556
        #
        url = self.query
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
        xbmc.executebuiltin('PlayMedia(%s)' % src)

    def __extract_date(self, data):
        # 現在時刻
        now = datetime.datetime.now()
        year0 = now.strftime('%Y')
        date0 = now.strftime('%m-%d')
        # 日時を抽出
        date = '0000-00-00'
        m = re.match(r'(20[0-9]{2})年', data.get('date').encode('utf-8'))
        if m:
            date = '%s-00-00' % (m.group(1))
        m = re.match(r'([0-9]{1,2})月([0-9]{1,2})日', data.get('date').encode('utf-8'))
        if m:
            date1 = '%02d-%02d' % (int(m.group(1)),int(m.group(2)))
            date = '%04d-%s' % (int(year0)-1 if date1>date0 else int(year0), date1)
        m = re.match(r'([0-9]{1,2})/([0-9]{1,2})', data.get('date').encode('utf-8'))
        if m:
            date1 = '%02d-%02d' % (int(m.group(1)),int(m.group(2)))
            date = '%04d-%s' % (int(year0) if date1<date0 else int(year0)-1, date1)
        return date

    def __add_item(self, data):
        name = data.get('title')
        url = 'https://tver.jp%s' % data.get('href')
        mode = 16
        image = data.get('images')[0]
        # 番組情報
        labels = {
            'title': data.get('title'),
            'studio': data.get('media'),
            'date': self.__extract_date(data),
            'genre': '%s %s' % (data.get('media'), data.get('date'))
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
