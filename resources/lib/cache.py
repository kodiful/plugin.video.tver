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
        os.makedirs(Common.CACHE_PATH)
        
    def update(self):
        size = 0
        num = 0
        for dirpath, _, filenames in os.walk(Common.CACHE_PATH):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
                        num += 1
                except OSError:
                    pass  # アクセスできないファイルなどをスキップ
        if size > 1024 * 1024:
            Common.SET('cache', f'{size/1024/1024:.1f} MB / {num} files')
        elif size > 1024:
            Common.SET('cache', f'{size/1024:.1f} kB / {num} files')
        else:
            Common.SET('cache', f'{size} bytes / {num} files')
