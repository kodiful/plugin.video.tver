# -*- coding: utf-8 -*-

import sys
import os
import socket
import threading
import subprocess
import xbmcgui

# extraディレクトリをパッケージのパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'extra'))

from resources.lib.common import Common
from resources.lib.cache import Cache
from resources.lib.localproxy import LocalProxy


if __name__ == '__main__':

    # HTTP接続のタイムアウト(秒)を設定
    socket.setdefaulttimeout(60)

    # ffmpegのパスを設定
    path = Common.GET('ffmpeg')
    if path and os.path.exists(path):
        PATH = os.environ['PATH']
        if os.name == 'nt':
            os.environ['PATH'] = '%s;%s' % (os.path.dirname(path), PATH)
        else:
            os.environ['PATH'] = '%s:%s' % (os.path.dirname(path), PATH)

    # ffmpegの起動を確認
    p = subprocess.Popen(['ffmpeg'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    status = p.stdout.readline().decode('utf-8', errors='shift_jis').strip()
    # macOS
    # OK => "'ffmpeg version 5.1.2 Copyright (c) 2000-2022 the FFmpeg developers'"
    # NG => "'/bin/sh: ffmpeg: command not found'"
    # Windows
    # OK => "ffmpeg version 6.0-essentials_build-www.gyan.dev Copyright (c) 2000-2023 the FFmpeg developers" + "built with gcc 12.2.0 (Rev10, Built by MSYS2 project)"
    # NG => "'ffmpeg' は、内部コマンドまたは外部コマンド、" + "操作可能なプログラムまたはバッチ ファイルとして認識されていません。"
    # Raspberry Pi OS
    # OK => "'ffmpeg version 5.1.6-0+deb12u1+rpt3 Copyright (c) 2000-2024 the FFmpeg developers'"
    # NG => "'/bin/sh: 1: ffmpeg: not found'"
    if status.find('ffmpeg version') == -1:
        xbmcgui.Dialog().ok(Common.ADDON_NAME, status)
        # ffmpaegのパスを設定
        xbmcgui.Dialog().ok(Common.ADDON_NAME, Common.STR(30022))  # ffmpegの場所を指定してください
        path = xbmcgui.Dialog().browse(1, Common.ADDON_NAME, 'files')
        if path:
            Common.SET('ffmpeg', path)
            xbmcgui.Dialog().ok(Common.ADDON_NAME, Common.STR(30020))  # Kodiを再起動してください
        else:
            xbmcgui.Dialog().ok(Common.ADDON_NAME, Common.STR(30021))  # サービスを起動できません
        sys.exit()

    # キャッシュをクリア
    Cache().clear()

    # ローカルプロキシを初期化
    httpd = LocalProxy()
    # 別スレッドでローカルプロキシを起動
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
