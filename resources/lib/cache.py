# -*- coding: utf-8 -*-

import os
import shutil

from resources.lib.common import Common


class Cache(Common):

    def __init__(self):
        pass

    def clear(self):
        if os.path.isdir(Common.CACHE_PATH) is True:
            shutil.rmtree(Common.CACHE_PATH)
        os.makedirs(Common.IMG_CACHE, exist_ok=True)
        os.makedirs(Common.HLS_CACHE, exist_ok=True)
        
    def update(self):
        size = 0
        for dirpath, _, filenames in os.walk(Common.CACHE_PATH):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
                except OSError:
                    pass  # アクセスできないファイルなどをスキップ
        if size > 1024 * 1024:
            Common.SET('cache', '%.1f MB' % (size / 1024 / 1024))
        elif size > 1024:
            Common.SET('cache', '%.1f kB' % (size / 1024))
        else:
            Common.SET('cache', '%d bytes' % size)
