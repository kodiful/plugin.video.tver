# -*- coding: utf-8 -*-

import sys
import json
import xbmc
import xbmcaddon

from resources.lib.common import *
from resources.lib.browse import Browse
from resources.lib.smartlist import SmartList

# HTTP接続におけるタイムアウト(秒)
import socket
socket.setdefaulttimeout(60)


class Cache():

    def __init__(self):
        self.files = os.listdir(Const.CACHE_PATH)

    def clear(self):
        for file in self.files:
            try:
                os.remove(os.path.join(Const.CACHE_PATH, file))
            except Exception:
                pass

    def update(self):
        size = 0
        for file in self.files:
            try:
                size = size + os.path.getsize(os.path.join(Const.CACHE_PATH, file))
            except Exception:
                pass
        if size > 1024 * 1024:
            Const.SET('cache', '%.1f MB / %d files' % (size / 1024 / 1024, len(self.files)))
        elif size > 1024:
            Const.SET('cache', '%.1f kB / %d files' % (size / 1024, len(self.files)))
        else:
            Const.SET('cache', '%d bytes / %d files' % (size, len(self.files)))


if __name__ == '__main__':

    # 引数
    args, _ = Browse().update_query(sys.argv[2][1:])
    action = args.get('action', '')
    query = args.get('query', '')

    # キャッシュサイズが未設定の場合は設定
    if Const.GET('cache') == '':
        Cache().update()

    # スマートリスト設定をクリア
    keyword = Const.GET('keyword')
    Const.SET('keyword', '')

    # top
    if action == '':
        Browse().show_top()

    # select date
    elif action == 'setweekday':
        Browse(query).show_weekday()

    # select channel
    elif action == 'settvnetwork':
        Browse(query).show_tvnetwork()

    # select genre
    elif action == 'setgenre':
        Browse(query).show_genre()

    # search
    elif action == 'search':
        Browse(query).search()

    # play
    elif action == 'play':
        Browse().play(args['url'])

    # download
    elif action == 'download':
        Browse().download(args['url'], args['contentid'])

    # clear cache
    elif action == 'cache':
        Cache().clear()
        Cache().update()

    # open settings
    elif action == 'settings':
        # update cache settings
        Cache().update()
        # open settings
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % xbmcaddon.Addon().getAddonInfo('id'))

    # smartlist
    elif action == 'beginEditSmartList':
        keyword = args.get('keyword')
        edit = args.get('edit')
        SmartList().beginEdit(keyword, edit)
        # open settings & focus smartlist category
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % xbmcaddon.Addon().getAddonInfo('id'))
        xbmc.executebuiltin('SetFocus(-99)')

    elif action == 'endEditSmartList':
        SmartList().endEdit(keyword)
        # refresh top page
        xbmc.executebuiltin('Container.Update(%s,replace)' % sys.argv[0])

    elif action == 'deleteSmartList':
        keyword = args.get('keyword')
        SmartList().delete(keyword)
        # refresh top page
        xbmc.executebuiltin('Container.Update(%s,replace)' % sys.argv[0])