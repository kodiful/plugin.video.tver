# -*- coding: utf-8 -*-

import socket
import urllib.parse
import json
import threading
import ffmpeg
import os
import re
import shutil
import datetime
import xbmc

from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

from resources.lib.common import Common


class LocalProxy(HTTPServer, Common):

    def __init__(self):
        # ポート番号
        self.port = self.GET('port')
        # スレッドリスト
        self.threadlist = {}
        # ポート番号が取得できたらHTTPサーバを準備する
        if self.port:
            # 型変換
            self.port = int(self.port)
            # ポートが利用可能か確認する
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = s.connect_ex(('127.0.0.1', self.port))
            s.close()
            if result > 0:
                # HTTPサーバを初期化
                super().__init__(('', self.port), LocalProxyHandler)
            else:
                self.notify(f'Localproxy port {self.port} is busy')
        else:
            self.notify('Localproxy port is not defined')


class LocalProxyHandler(SimpleHTTPRequestHandler, Common):

    def log_message(self, format, *args):
        # デフォルトのログ出力を抑制する
        # format: '"%s" %s %s'
        # args: ('GET /abort;pBVVfZdW HTTP/1.1', '200', '-')
        return

    def do_HEAD(self):
        try:
            # HTTPリクエストをパースする
            request = urllib.parse.urlparse(self.path)
            # パスに応じて処理
            if request.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
            elif request.path == '/play' or request.path == '/download':
                self.send_response(302)
                self.end_headers()
            elif request.path.endswith('.m3u8'):
                self.send_response(200)
                self.send_header('Content-Type', 'application/x-mpegurl')
                self.end_headers()
            elif request.path.endswith('.ts'):
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp2t')
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.log(e)

    def do_GET(self):
        try:
            # HTTPリクエストをパースする
            request = urllib.parse.urlparse(self.path)
            # パスに応じて処理
            if request.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                html = self.threadlist2html()
                self.wfile.write(html.encode())
            elif request.path.endswith('.css'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/css')
                self.end_headers()
                # cssファイルの内容を返す
                paths = request.path.split('/')
                with open(os.path.join(self.DATA_PATH, paths[-2], paths[-1]), 'rb') as f:
                    self.wfile.write(f.read())
            elif request.path == '/play' or request.path == '/download':
                id = request.query
                # 処理スレッドでオーディオ/ビデオストリームを統合
                mux = Mux(id)
                thread = threading.Thread(target=mux.execute, daemon=True)
                # スレッドリストに格納
                self.server.threadlist[mux.dir] = threaddata = {'thread': thread, 'mux': mux, 'id': id, 'status': ''}
                # 処理スレッド起動
                thread.start()
                # 監視スレッド起動（再生時のみ/ダウンロード時は監視しない）
                if request.path == '/play':
                    watchdog = Watchdog(thread, mux, id, threaddata)
                    threading.Thread(target=watchdog.execute, daemon=True).start()
                if request.path == '/download':
                    threaddata['status'] = 'background'
                # HLS_FILEが生成されるまで待つ
                while mux.process is None or mux.process.returncode is None:
                    if os.path.exists(mux.m3u8_file):
                        break
                    xbmc.sleep(1000)
                # HLS_FILEへリダイレクト
                self.send_response(302)
                self.send_header('Location', f'http://127.0.0.1:{self.server.port}/{mux.dir}/{self.HLS_FILE}')
                self.end_headers()
                self.wfile.write(b'302 Found')
            elif request.path.endswith('.m3u8'):
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-mpegurl')
                    self.end_headers()
                    # m3u8ファイルの内容を返す
                    paths = request.path.split('/')
                    with open(os.path.join(self.HLS_CACHE, paths[-2], paths[-1]), 'rb') as f:
                        self.wfile.write(f.read())
                except (BrokenPipeError, ConnectionResetError):
                    pass
            elif request.path.endswith('.ts'):
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'video/mp2t')
                    self.end_headers()
                    # tsファイルの内容を返す
                    paths = request.path.split('/')
                    with open(os.path.join(self.HLS_CACHE, paths[-2], paths[-1]), 'rb') as f:
                        self.wfile.write(f.read())
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'500 Internal Server Error')
            self.log(e)

    def threadlist2html(self):
        # リスト化
        data = [['dir', 'id', 'thread.ident', 'thread.is_alive', 'ffmpeg.pid', 'ffmpeg.returncode', 'status']]
        for dir, item in self.server.threadlist.items():
            thread = item.get('thread')
            mux = item.get('mux')
            id = item.get('id')
            status = item.get('status')
            data.append([dir, id, thread.ident, thread.is_alive(), mux.process.pid, mux.process.returncode, status])
        # hrmlに変換
        html = ['<table>']
        html.append('<thead>')
        for row in data[:1]:
            html.append('<tr>')
            html.extend([f'<th>{cell}</th>' for cell in row])
            html.append('</tr>')
        html.append('</thead>')
        html.append('<tbody>')
        for row in data[1:]:
            html.append('<tr>')
            html.extend([f'<td>{cell}</td>' for cell in row])
            html.append('</tr>')
        html.append('</tbody>')
        html.append('</table>')
        # ページに埋め込む
        with open(os.path.join(self.DATA_PATH, 'html', 'template.html')) as f:
            template = f.read()
        return template.format(table='\n'.join(html))


class Watchdog(Common):

    def __init__(self, thread, mux, id, threaddata):
        self.thread = thread
        self.mux = mux
        self.id = id
        self.threaddata = threaddata
    
    def execute(self):
        while self.thread.is_alive():
            if self.mux.process is None:  # 処理開始前
                pass
            elif self.mux.process.returncode is None:  # 処理中
                if xbmc.Player().isPlaying():
                    item = xbmc.Player().getPlayingItem()
                    if item.getPath().find(self.id) == -1:
                        # スレッドと違うコンテンツが再生されているのでffmpegのプロセスを停止
                        self.log('new player:', item.getPath())
                        self.mux.process.terminate()
                        self.mux.process.wait()
                        self.log('MUX terminated:', self.id)
                        self.threaddata['status'] = 'new player'
                else:
                    # 再生されているコンテンツがないのでffmpegのプロセスを停止
                    self.log('no player')
                    self.mux.process.terminate()
                    self.mux.process.wait()
                    self.log('MUX terminated:', self.id)
                    self.threaddata['status'] = 'no player'
            else:  # 処理終了
                break
            # 待機
            xbmc.sleep(1000)


class Mux(Common):

    def __init__(self, id):
        self.id = id
        self.dir = f'{datetime.datetime.now().timestamp():.0f}.{id}'
        streams = self.get_streams(id)
        resolution = self.GET('resolution')
        self.audio_stream = streams[resolution]['audio']
        self.video_stream = streams[resolution]['video']
        dir_path = os.path.join(self.HLS_CACHE, self.dir)
        self.m3u8_file = os.path.join(dir_path, self.HLS_FILE)
        self.process = None
        # ディレクトリを新規作成
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)

    def execute(self):
        self.log('start mux:', self.id)
        self.log('video_stream:', self.video_stream)
        self.log('audio_stream:', self.audio_stream)
        # ストリーム統合のプロセスを開始
        input_video = ffmpeg.input(self.video_stream)
        input_audio = ffmpeg.input(self.audio_stream)
        self.process = ffmpeg.output(
            input_video.video,
            input_audio.audio,
            self.m3u8_file,
            c='copy',
            f='hls',
            hls_time=6,
            hls_list_size=0,
            hls_flags='append_list'
        ).run_async()
        # 終了を待機
        self.process.wait()
        # 処理結果に応じて後処理
        if self.process.returncode == 0:
            self.log('MUX complete:', self.id)
        else:
            self.log('MUX error (possibly due to interruption):', self.id)

    def get_streams(self, id):
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
        # マニフェストを取得
        # https://manifest.streaks.jp/v6/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/hls/v3/manifest.m3u8?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYyI6ImI3MDE3ODUyMjk5ODQ4M2Q5NDczMGQwNDFiNjgxMzRmIiwiZWRnZSI6IjZiNzk5ZjAyMDk0YzQxNWNhMzQzNGE2ZmIzOWFlMWVjIiwiY29kZWNzIjoiYXV0byIsImV4cCI6MTc0NDAwMjAwMCwidnA5IjoxLCJzbSI6IjI4ZTUyMmM0YWUzMDQyMzg5MzBiMmJjNjZlMDRhM2I4IiwicHB3IjoiNDc2In0.RQAoLnzksUAec5UzmnJR7z6epor9ZAG2Qjk77fqFA5o
        url = src
        buf = self.request(url, {'origin': 'https://tver.jp', 'referer': 'https://tver.jp'})
        '''
        #EXTM3U
        #EXT-X-VERSION:4
        #EXT-X-INDEPENDENT-SEGMENTS
        #EXT-X-CONTENT-STEERING:SERVER-URI="https://steering-manifest.streaks.jp/v1/tver-ex/28e522c4ae304238930b2bc66e04a3b8.hcsm?ppw=476"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="ts_AUDIO-0_1",NAME="pro_dbe61e17cf484f45bd2e99c1fdfb3e5e",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="und",URI="https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/audio/9f489a2e-1048-11f0-a957-0af26079631b/ts_audio_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="ts_AUDIO-0_2",NAME="pro_dbe61e17cf484f45bd2e99c1fdfb3e5e",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="und",URI="https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/audio/9f489a2e-1048-11f0-a957-0af26079631b/ts_audio_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="ts_AUDIO-1_1",NAME="pro_dbe61e17cf484f45bd2e99c1fdfb3e5e",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="und",URI="https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/audio/a110347a-1048-11f0-a957-0af26079631b/ts_audio_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="ts_AUDIO-1_2",NAME="pro_dbe61e17cf484f45bd2e99c1fdfb3e5e",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="und",URI="https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/audio/a110347a-1048-11f0-a957-0af26079631b/ts_audio_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4"
        #EXT-X-STREAM-INF:BANDWIDTH=5049726,AVERAGE-BANDWIDTH=3373249,CODECS="avc1.640028,mp4a.40.2",RESOLUTION=1920x1080,AUDIO="ts_AUDIO-0_1",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="476"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9834f516-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI
        #EXT-X-STREAM-INF:BANDWIDTH=5049726,AVERAGE-BANDWIDTH=3373249,CODECS="avc1.640028,mp4a.40.2",RESOLUTION=1920x1080,AUDIO="ts_AUDIO-0_2",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="3rf"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9834f516-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4
        #EXT-X-STREAM-INF:BANDWIDTH=3479115,AVERAGE-BANDWIDTH=2321698,CODECS="avc1.4D401F,mp4a.40.2",RESOLUTION=1280x720,AUDIO="ts_AUDIO-0_1",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="476"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/99ff7858-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI
        #EXT-X-STREAM-INF:BANDWIDTH=3479115,AVERAGE-BANDWIDTH=2321698,CODECS="avc1.4D401F,mp4a.40.2",RESOLUTION=1280x720,AUDIO="ts_AUDIO-0_2",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="3rf"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/99ff7858-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4
        #EXT-X-STREAM-INF:BANDWIDTH=2161707,AVERAGE-BANDWIDTH=1450924,CODECS="avc1.4D401F,mp4a.40.2",RESOLUTION=960x540,AUDIO="ts_AUDIO-1_1",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="476"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9bc1e658-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI
        #EXT-X-STREAM-INF:BANDWIDTH=2161707,AVERAGE-BANDWIDTH=1450924,CODECS="avc1.4D401F,mp4a.40.2",RESOLUTION=960x540,AUDIO="ts_AUDIO-1_2",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="3rf"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9bc1e658-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4
        #EXT-X-STREAM-INF:BANDWIDTH=1015802,AVERAGE-BANDWIDTH=709041,CODECS="avc1.42C01E,mp4a.40.2",RESOLUTION=640x360,AUDIO="ts_AUDIO-1_1",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="476"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9d84c438-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoiZXgtdm9kLXMtY2RuLnR2ZXIuanAifQ.HgyFGrmqoMXfjaKdOS1_qNBXJz49YMhnAyQds8LJuWI
        #EXT-X-STREAM-INF:BANDWIDTH=1015802,AVERAGE-BANDWIDTH=709041,CODECS="avc1.42C01E,mp4a.40.2",RESOLUTION=640x360,AUDIO="ts_AUDIO-1_2",CLOSED-CAPTIONS=NONE,FRAME-RATE=29.970,PATHWAY-ID="3rf"
        https://variants.streaks.jp/v5/tver-ex/ab1cca1967384cbf9a559c7f9fe23002/d35c34ea7eeb45949ce9944a4d094b74/video/9d84c438-1048-11f0-a957-0af26079631b/video_1743656888.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidm9kLXR2ZXItZXguc3RyZWFrcy5qcCJ9.gFB6tY0AVAieWcGE4c3zgk5NCM5qTQlc8MEYAuBgIR4
        '''
        # マニフェストをパース
        lines = buf.decode().split('\n')
        pattern = r'([^=,]+)=(".*?"|[^,]+)'
        results = {}
        # ppwを抽出
        line = list(filter(lambda x: x.startswith('#EXT-X-CONTENT-STEERING'), lines))[0]
        ppw = line.split('?')[1].strip('"').split('=')[1]
        # オーディオ
        astream = {}
        for line in filter(lambda x: x.startswith('#EXT-X-MEDIA'), lines):
            a = dict(re.findall(pattern, line.replace('#EXT-X-MEDIA:', '')))
            gid = a['GROUP-ID'].strip('"')
            astream[gid] = a['URI'].strip('"')
        # ビデオ
        lines = list(zip(filter(lambda x: x.startswith('#EXT-X-STREAM-INF'), lines), filter(lambda x: x.startswith('https://variants.streaks.jp/'), lines)))
        for line, vstream in filter(lambda x: x[0].find(f'PATHWAY-ID="{ppw}"') > -1, lines):
            a = dict(re.findall(pattern, line.replace('#EXT-X-STREAM-INF:', '')))
            gid = a['AUDIO'].strip('"')
            resolution = a['RESOLUTION']
            results[resolution] = {'audio': astream[gid], 'video': vstream}
        # パース結果
        '''
        {
            "1920x1080": {
                "audio": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/audio/a8e051f4-1051-11f0-aa78-0a4a5d71602f/ts_audio_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI",
                "video": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/video/9bbcb9a4-1051-11f0-aa78-0a4a5d71602f/video_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI"
            },
            "1280x720": {
                "audio": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/audio/a8e051f4-1051-11f0-aa78-0a4a5d71602f/ts_audio_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI",
                "video": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/video/9f09f964-1051-11f0-aa78-0a4a5d71602f/video_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI"
            },
            "960x540": {
                "audio": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/audio/ac20a990-1051-11f0-aa78-0a4a5d71602f/ts_audio_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI",
                "video": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/video/a254d0f8-1051-11f0-aa78-0a4a5d71602f/video_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI"
            },
            "640x360": {
                "audio": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/audio/ac20a990-1051-11f0-aa78-0a4a5d71602f/ts_audio_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI",
                "video": "https://variants.streaks.jp/v5/tver-tx/9cbbffa17ad94d9783bce157b2c3e28e/04df1e38e9b54b83b78c9a600ae6636e/video/a59c4fa2-1051-11f0-aa78-0a4a5d71602f/video_1743660711.m3u8?vt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlZGdlIjoidHgtdm9kLXMtY2RuLnR2ZXIuanAifQ.yVoOQz-O8VRMIgVewpCUB_0F5Z5WmnIUHd94Q99qjSI"
            }
        }
        '''
        return results
