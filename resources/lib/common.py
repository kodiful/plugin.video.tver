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
    BROWSE_FOLDER = os.path.join(DATA_PATH, 'icons', 'set.png')

    # 通知
    @staticmethod
    def notify(*messages, **options):
        # アドオン
        addon = xbmcaddon.Addon()
        name = addon.getAddonInfo('name')
        # デフォルト設定
        if options.get('error'):
            image = 'DefaultIconError.png'
            level = xbmc.LOGERROR
        else:
            image = 'DefaultIconInfo.png'
            level = xbmc.LOGINFO
        # ポップアップする時間
        duration = options.get('duration', 10000)
        # ポップアップアイコン
        image = options.get('image', image)
        # メッセージ
        messages = ' '.join(map(lambda x: str(x), messages))
        # ポップアップ通知
        xbmc.executebuiltin(f'Notification("{name}","{messages}",{duration},"{image}")')
        # ログ出力
        Common.log(messages, level=level)

    # ログ
    @staticmethod
    def log(*messages, **options):
        # アドオン
        addon = xbmcaddon.Addon()
        # ログレベル、メッセージを設定
        if isinstance(messages[0], Exception):
            level = options.get('level', xbmc.LOGERROR)
            message = '\n'.join(list(map(lambda x: x.strip(), traceback.TracebackException.from_exception(messages[0]).format())))
            if len(messages[1:]) > 0:
                message += ': ' + ' '.join(map(lambda x: str(x), messages[1:]))
        else:
            level = options.get('level', xbmc.LOGINFO)
            frame = inspect.currentframe().f_back
            filename = os.path.basename(frame.f_code.co_filename)
            lineno = frame.f_lineno
            name = frame.f_code.co_name
            id = addon.getAddonInfo('id')
            message = f'Addon "{id}", File "{filename}", line {lineno}, in {name}'
            if len(messages) > 0:
                message += ': ' + ' '.join(map(lambda x: str(x), messages))
        # ログ出力
        xbmc.log(message, level)

    # HTTPリクエスト
    @staticmethod
    def request(url, headers={}, decode=True):
        try:
            req = Request(url, headers=headers)
            with urlopen(req) as res:
                content = res.read()
                if decode:
                    content = content.decode()
        except HTTPError as e:
            content = None
            Common.log(e)
        return content
