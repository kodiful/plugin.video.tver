# -*- coding: utf-8 -*-

import sys
import xbmc, xbmcaddon
import socket

from resources.lib.browse import Browse

# HTTP接続におけるタイムアウト(秒)
socket.setdefaulttimeout(60)


if __name__  == '__main__':

    # 引数
    args, _ = Browse().update_query(sys.argv[2][1:])
    action = args.get('action', '')
    query = args.get('query',  '')

    # top
    if action == '':
        Browse().show('top')

    # select date
    elif action == 'setdate':
        Browse(query).show('date')

    # select channel
    elif action == 'setchannel':
        Browse(query).show('channel')

    # select genre
    elif action == 'setgenre':
        Browse(query).show('genre')

    # search
    elif action == 'search':
        Browse(query).search()

    # play
    elif action == 'play':
        Browse().play(args)

    # download
    elif action == 'download':
        Browse().download(args)

    # open settings
    elif action == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % xbmcaddon.Addon().getAddonInfo('id'))
