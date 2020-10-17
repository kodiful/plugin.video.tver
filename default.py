# -*- coding: utf-8 -*-

import sys
import json
import xbmc, xbmcaddon

from resources.lib.common import convert, log, notify
from resources.lib.browse import Browse

# HTTP接続におけるタイムアウト(秒)
import socket
socket.setdefaulttimeout(60)


if __name__  == '__main__':

    # 引数
    args, _ = Browse().update_query(sys.argv[2][1:])
    action = args.get('action', '')
    query = args.get('query', '')

    # top
    if action == '':
        Browse().show_top()

    # select date
    elif action == 'setdate':
        Browse(query).show_date()

    # select channel
    elif action == 'setchannel':
        Browse(query).show_channel()

    # select genre
    elif action == 'setgenre':
        Browse(query).show_genre()

    # search
    elif action == 'search':
        Browse(query).search()

    # play
    elif action == 'play':
        item = convert(json.loads(args['json']))
        Browse().play(item)

    # download
    elif action == 'download':
        item = convert(json.loads(args['json']))
        Browse().download(item)

    # open settings
    elif action == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % xbmcaddon.Addon().getAddonInfo('id'))
