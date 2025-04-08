# -*- coding: utf-8 -*-

import os
import inspect
import traceback
import xbmc
import xbmcaddon
import xbmcvfs

from urllib.request import Request
from urllib.request import urlopen
from urllib.request import HTTPError


class Common:

    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo('id')
    ADDON_NAME = ADDON.getAddonInfo('name')
    ADDON_VERSION = ADDON.getAddonInfo('version')

    STR = ADDON.getLocalizedString
    GET = ADDON.getSetting
    SET = ADDON.setSetting

    # ディレクトリパス
    PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    PLUGIN_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
    RESOURCES_PATH = os.path.join(PLUGIN_PATH, 'resources')
    DATA_PATH = os.path.join(RESOURCES_PATH, 'data')

    # キャッシュパス
    CACHE_PATH = os.path.join(PROFILE_PATH, 'cache')
    IMG_CACHE = os.path.join(CACHE_PATH, 'image')
    if not os.path.isdir(IMG_CACHE):
        os.makedirs(IMG_CACHE, exist_ok=True)
    HLS_CACHE = os.path.join(CACHE_PATH, 'hls')
    if not os.path.isdir(HLS_CACHE):
        os.makedirs(HLS_CACHE, exist_ok=True)

    # ファイルパス
    SMARTLIST_FILE = os.path.join(PROFILE_PATH, 'smatlist.js')

    # データベース
    DB_PATH = xbmcvfs.translatePath('special://database')
    CACHE_DB = os.path.join(DB_PATH, 'Textures13.db')

    # サムネイル
    DOWNLOADS = os.path.join(DATA_PATH, 'icons', 'folder.png')
    CALENDAR = os.path.join(DATA_PATH, 'icons', 'calendar.png')
    RADIO_TOWER = os.path.join(DATA_PATH, 'icons', 'satellite.png')
    CATEGORIZE = os.path.join(DATA_PATH, 'icons', 'tag.png')
    BROWSE_FOLDER = os.path.join(DATA_PATH, 'icons', 'folder.png')

    # 通知
    @staticmethod
    def notify(*messages, **options):
        # アドオン
        addon = xbmcaddon.Addon()
        # ポップアップする時間
        time = options.get('time', 10000)
        # ポップアップアイコン
        image = options.get('image', None)
        if image:
            pass
        elif options.get('error', False):
            image = 'DefaultIconError.png'
        else:
            image = 'DefaultIconInfo.png'
        # メッセージ
        messages = ' '.join(map(lambda x: str(x), messages))
        # ログ出力
        Common.log(messages, error=options.get('error', False))
        # ポップアップ通知
        xbmc.executebuiltin('Notification("%s","%s",%d,"%s")' % (addon.getAddonInfo('name'), messages, time, image))

    # ログ
    @staticmethod
    def log(*messages, **options):
        # アドオン
        addon = xbmcaddon.Addon()
        # ログレベル、メッセージを設定
        if isinstance(messages[0], Exception):
            level = xbmc.LOGERROR
            message = '\n'.join([
                ''.join(list(traceback.TracebackException.from_exception(messages[0]).format())),
                ' '.join(map(lambda x: str(x), messages[1:]))
            ])
        else:
            level = xbmc.LOGINFO
            frame = inspect.currentframe().f_back
            filename = os.path.basename(frame.f_code.co_filename)
            lineno = frame.f_lineno
            name = frame.f_code.co_name
            message = ': '.join([
                addon.getAddonInfo('id'),
                f'{filename}({lineno}) {name}',
                ' '.join(map(lambda x: str(x), messages))])
        # ログ出力
        xbmc.log(message, level)

    # HTTPリクエスト
    @staticmethod
    def request(url, headers={}, decode=True):
        try:
            req = Request(url, headers=headers)
            with urlopen(req) as res:
                content = res.read()
                content_type = res.info().get_content_type()
                if content_type.startswith('text/'):
                    content = content.decode()
        except HTTPError as e:
            content = None
            Common.log(e)
        return content
