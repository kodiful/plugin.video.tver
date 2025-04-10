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

    def play(self, id):
        url = self._get_manifest(id)
        listitem = xbmcgui.ListItem()
        listitem.setPath(url)
        listitem.setMimeType('application/x-mpegurl')
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

    def download(self, url, id):
        url = self._get_manifest(id)
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
            "id": "ep7ywezxdh",
            "version": 11,
            "title": "若林正恭＆井ノ原快彦＆ヒコロヒー＆弘中綾香アナ",
            "seriesID": "srrao7paa6",
            "endAt": 1744646580,
            "broadcastDateLabel": "4月7日(月)放送分",
            "isNHKContent": false,
            "isSubtitle": false,
            "ribbonID": 0,
            "seriesTitle": "激レアさんを連れてきた。",
            "isAvailable": true,
            "broadcasterName": "テレビ朝日",
            "productionProviderName": "テレビ朝日",
            "isEndingSoon": false
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
        #xbmcplugin.addDirectoryItem(int(sys.argv[1]), f'http://127.0.0.1:{port}/play?{id}', listitem, False)
        url = '%s?action=play&contentid=%s' % (sys.argv[0], id)
        #url = 'https://variants.streaks.jp/v5/tver-ex/f696c9a8084f4b80babc41d3a48de58a/d1e6a4622fb8425389103d6716e4ebd4/video/c9185baa-11d3-11f0-8e83-06bc9d11be6d/video_1743826427.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI'
        #url = 'http://127.0.0.1:8089/0/video.m3u8'
        #url = 'http://127.0.0.1:8089/0/manifest.m3u8'
        #url = '/Users/uchiyama/Library/Application Support/Kodi_21_2/addons/plugin.video.tver/addon_data/cache/hls/0/manifest.m3u8'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

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
        img_file = os.path.join(self.CACHE_PATH, f'{id}.jpg')
        if os.path.isfile(img_file) and os.path.getsize(img_file) < 1000:
            # delete img_file
            os.remove(img_file)
            # delete from database
            conn = sqlite.connect(self.CACHE_DB)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM texture WHERE url = :img_file', {'img_file': img_file})
            conn.commit()
            conn.close()
        if os.path.isfile(img_file):
            pass
        else:
            url = f'https://statics.tver.jp/images/content/thumbnail/episode/small/{id}.jpg'
            buffer = self.request(url, decode=False)
            image = Image.open(io.BytesIO(buffer))  # 320x180
            image = image.resize((216, 122))
            background = Image.new('RGB', (216, 216), (0, 0, 0))
            background.paste(image, (0, 47))
            background.save(img_file, 'PNG')
        return img_file

    def _get_manifest(self, id):
        # エピソードJSONをダウンロード
        # https://statics.tver.jp/content/episode/epmi3rnbm0.json
        url = f'https://statics.tver.jp/content/episode/{id}.json'
        buf = self.request(url)
        '''
        {
            "id": "epmi3rnbm0",
            "version": 15,
            "video": {
                "videoRefID": "1589_1588_55861",
                "accountID": "4394098883001",
                "playerID": "MfxS5MXtZ",
                "channelID": "ex"
            },
            "title": "お酒飲めないけど飲み会大好き芸人",
            "seriesID": "sr542nxzof",
            "seasonID": "sso0k36qo8",
            "description": "▽出川持ち込み企画▽酒ナシでも朝まで楽しめる▽ホリケン＆森田＆中岡＆芝▽ソフトドリンクに合う！お店メニュー紹介▽居酒屋での振る舞い方▽スタジオでシラフで乾杯",
            "no": 937,
            "broadcastProviderLabel": "テレビ朝日",
            "productionProviderLabel": "テレビ朝日",
            "broadcastDateLabel": "4月3日(木)放送分",
            "broadcastProviderID": "ex",
            "isSubtitle": false,
            "copyright": "(C)テレビ朝日",
            "viewStatus": {
                "startAt": 1743697980,
                "endAt": 1744302780
            },
            "isAllowCast": true,
            "share": {
                "text": "アメトーーク！\n#TVer",
                "url": "https://tver.jp/episodes/epmi3rnbm0"
            },
            "tags": {},
            "isNHKContent": false,
            "svod": [],
            "streaks": {
                "videoRefID": "1589_1588_55861",
                "mediaID": "ab1cca1967384cbf9a559c7f9fe23002",
                "projectID": "tver-ex"
            }
        }
        '''
        episode = json.loads(buf)
        streaks = episode.get('streaks')
        projectID = streaks.get('projectID')
        videoRefID = streaks.get('videoRefID')
        # プレイバックJSONを取得
        # https://playback.api.streaks.jp/v1/projects/tver-ex/medias/ref:1589_1588_55861
        url = f'https://playback.api.streaks.jp/v1/projects/{projectID}/medias/ref:{videoRefID}'
        buf = self.request(url, {'origin': 'https://tver.jp', 'referer': 'https://tver.jp'})
        '''
        {
            "project_id": "tver-ex",
            "id": "ab1cca1967384cbf9a559c7f9fe23002",
            "ref_id": "1589_1588_55861",
            "type": "file",
            "name": "アメトーーク！ アメトーーク！ 4月3日(木)放送分 お酒飲めないけど飲み会大好き芸人",
            "description": "▽出川持ち込み企画▽酒ナシでも朝まで楽しめる▽ホリケン＆森田＆中岡＆芝▽ソフトドリンクに合う！お店メニュー紹介▽居酒屋での振る舞い方▽スタジオでシラフで乾杯",
            "duration": 2796.843,
            "profile": "51ef4bc9763a43afb10a20267ca1e3c0",
            "poster": {
                "src": "https://vod-tver-ex.streaks.jp/uploads/media/poster_image/ab1cca1967384cbf9a559c7f9fe23002/298d7208-cca8-414f-bff9-58299fc59569.jpg"
            },
            "thumbnail": {
                "src": "https://vod-tver-ex.streaks.jp/uploads/media/thumbnail_image/ab1cca1967384cbf9a559c7f9fe23002/a46dcdd6-2169-470d-a230-8aea5d6107e3.jpg"
            },
            "sources": [
                {
                "id": "d35c34ea7eeb45949ce9944a4d094b74",
                "label": "hls_aes128",
                "type": "application/x-mpegURL",
                "resolution": "1920x1080",
                "ext_x_version": 3,
                "src": "https://manifest.streaks.jp/v6/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/hls/v3/manifest.m3u8?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYyI6ImI3MDE3ODUyMjk5ODQ4M2Q5NDczMGQwNDFiNjgxMzRmIiwiZWRnZSI6IjZiNzk5ZjAyMDk0YzQxNWNhMzQzNGE2ZmIzOWFlMWVjIiwiY29kZWNzIjoiYXV0byIsImV4cCI6MTc0NDAwMjAwMCwidnA5IjoxLCJzbSI6IjI4ZTUyMmM0YWUzMDQyMzg5MzBiMmJjNjZlMDRhM2I4IiwicHB3IjoiNDc2In0.RQAoLnzksUAec5UzmnJR7z6epor9ZAG2Qjk77fqFA5o",
                "cdn": "jocdn"
                }
            ],
            "tracks": [
                {
                "id": "d2c8c4e476124498b43b8b6cb10db26e",
                "kind": "thumbnails",
                "label": "thumbnail_tile0",
                "m3u8_embeded": false,
                "src": "https://tracks.streaks.jp/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/track/d2c8c4e476124498b43b8b6cb10db26e/thumbnails.vtt?ts=1743656894",
                "type": "text/vtt"
                }
            ],
            "cue_points": [
                {
                "name": "自動検出",
                "start_time": 2596.49,
                "end_time": null,
                "type": "ad"
                },
                {
                "name": "自動検出",
                "start_time": 2133.83,
                "end_time": null,
                "type": "ad"
                },
                {
                "name": "自動検出",
                "start_time": 1725.56,
                "end_time": null,
                "type": "ad"
                },
                {
                "name": "自動検出",
                "start_time": 1099.43,
                "end_time": null,
                "type": "ad"
                },
                {
                "name": "自動検出",
                "start_time": 609.509,
                "end_time": null,
                "type": "ad"
                }
            ],
            "chapters": [],
            "ads": [
                {
                "type": "vmap",
                "src": "https://vmap.v.ad-generation.jp/v1_0/13/5/[ads_params.guid]?ad_unit_id=tver_[ads_params.device_type]&label_site=tver&label_device=[ads_params.device_type]&label_streaming_type=vod&label_source=dio_product&rnd=[ads_params.random_32]&tp=[session.referer]&is_lat=[ads_params.is_lat]&label_is_lat=[ads_params.is_lat]&xuid_[ads_params.idtype]=[ads_params.rdid]&label_cu_uuid=[ads_params.rdid]&label_ppid=[ads_params.platformAdUid]&label_vr_uid=[ads_params.vr_uuid]&label_vr_pf=1028&label_vrtag_type=[ads_params.tag_type]&label_givn=[GOOGLE_INSTREAM_VIDEO_NONCE]&label_tvcu_g=[ads_params.tvcu_gender]&label_tvcu_age=[ads_params.tvcu_age]&label_tvcu_agegrp=[ads_params.tvcu_agegrp]&label_tvcu_zcode=[ads_params.tvcu_zcode]&label_tvcu_pcode=[ads_params.tvcu_pcode]&label_tvcu_ccode=[ads_params.tvcu_ccode]&label_tvcu_interest=[ads_params.interest]&label_tvcu_aud=[ads_params.audience]&label_tvcu_params=[ads_params.tvcu_params]&label_personal_is_lat=[ads_params.personalIsLat]&label_platform_uid=[ads_params.platformAdUid]&label_member_id=[ads_params.memberId]&label_vpmute=0&label_vr_uid2=[ads_params.platformVrUid]&label_gnr=[ads_params.program_category]&label_sub_gnr=[ads_params.sub_genre]&label_car=[ads_params.car]&label_ovp=play",
                "time_offset": null
                }
            ],
            "ad_fields": {
                "guid": "6370673690112",
                "advmapurl": "https://vmap.v.ad-generation.jp/v1_0/13/5/6370673690112?ad_unit_id=tver_{device}&label_site=tver&label_device={device}&label_streaming_type=vod&label_source=dio_product&rnd={random}&tp=[referrer_url]&is_lat={is_lat}&label_is_lat={is_lat}&xuid_{idtype}={uuid}&label_cu_uuid={uuid}&label_ppid={iuid}&label_vr_uid={vr_uid}&label_vr_pf=1028&label_vrtag_type={vrtag_type}&label_givn=[GOOGLE_INSTREAM_VIDEO_NONCE]&label_tvcu_g={gender}&label_tvcu_age={age}&label_tvcu_agegrp={agegrp}&label_tvcu_zcode={zcode}&label_tvcu_pcode={pcode}&label_tvcu_ccode={ccode}&label_tvcu_interest={interest}&label_tvcu_aud={audience}&label_tvcu_params={tvcu_params}&label_personal_is_lat={personalIsLat}&label_platform_uid={platformAdUid}&label_member_id={memberId}&label_vpmute=false&label_vr_uid2={vr_uid2}&label_gnr=variety&label_sub_gnr=",
                "sub_genre": "",
                "program_category": "variety"
            },
            "tags": [],
            "offline_enabled": true,
            "resolution": "1920x1080",
            "created_at": "2025-03-28T17:36:42.579+0900",
            "updated_at": "2025-04-04T13:21:27.409+0900",
            "copyright": "",
            "metrics": {
                "host": "tver-metrics.streaks.jp/v2",
                "sessionExpire": 1800000,
                "session_expire": 1800000,
                "pingTime": 20,
                "ping_time": 20,
                "sessionMaxAge": 86400,
                "session_max_age": 86400
            }
        }
        '''
        playback = json.loads(buf)
        sources = playback.get('sources')
        src = sources[0].get('src')
        # https://manifest.streaks.jp/v6/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/hls/v3/manifest.m3u8?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYyI6ImI3MDE3ODUyMjk5ODQ4M2Q5NDczMGQwNDFiNjgxMzRmIiwiZWRnZSI6IjZiNzk5ZjAyMDk0YzQxNWNhMzQzNGE2ZmIzOWFlMWVjIiwiY29kZWNzIjoiYXV0byIsImV4cCI6MTc0NDAwMjAwMCwidnA5IjoxLCJzbSI6IjI4ZTUyMmM0YWUzMDQyMzg5MzBiMmJjNjZlMDRhM2I4IiwicHB3IjoiNDc2In0.RQAoLnzksUAec5UzmnJR7z6epor9ZAG2Qjk77fqFA5o
        return src