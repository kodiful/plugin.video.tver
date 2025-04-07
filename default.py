# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcaddon

from resources.lib.common import Common
from resources.lib.browse import Browse
from resources.lib.cache import Cache
from resources.lib.smartlist import SmartList


# HTTP接続におけるタイムアウト(秒)
import socket
socket.setdefaulttimeout(60)


if __name__ == '__main__':

    # 引数
    args, _ = Browse().update_query(sys.argv[2][1:])
    action = args.get('action', '')
    query = args.get('query', '')

    # キャッシュサイズが未設定の場合は設定
    if Common.GET('cache') == '':
        Cache().update()

    # スマートリスト設定をクリア
    keyword = Common.GET('keyword')
    Common.SET('keyword', '')

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