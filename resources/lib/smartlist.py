# -*- coding: utf-8 -*-

import os
import json
from urllib.parse import urlencode

from resources.lib.common import Common


class SmartList(Common):

    def __init__(self):
        return
    
    def contextmenu(self, url, keyword, edit=False):
        contextmenu = []
        if edit:
            args = {'action': 'beginEditSmartList', 'keyword': keyword, 'edit': keyword}
            contextmenu += [(self.STR(30904), 'RunPlugin(%s?%s)' % (url, urlencode(args)))]
            args = {'action': 'deleteSmartList', 'keyword': keyword}
            contextmenu += [(self.STR(30905), 'RunPlugin(%s?%s)' % (url, urlencode(args)))]
        else:
            args = {'action': 'beginEditSmartList', 'keyword': keyword, 'edit': ''}
            contextmenu += [(self.STR(30903), 'RunPlugin(%s?%s)' % (url, urlencode(args)))]
        return contextmenu

    def getList(self):
        if os.path.isfile(self.SMARTLIST_FILE):
            try:
                with open(self.SMARTLIST_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    smartlist = f.read()
                    smartlist = json.loads(smartlist)
                    return smartlist
            except Exception:
                return []
        else:
            return []

    def setList(self, smartlist):
        with open(self.SMARTLIST_FILE, 'w', encoding='utf-8', errors='ignore') as f:
            smartlist = sorted(smartlist, key=lambda item: item['keyword'])
            smartlist = json.dumps(smartlist, sort_keys=True, ensure_ascii=False, indent=4)
            f.write(smartlist)

    def beginEdit(self, keyword, edit=''):
        # ダイアログに設定
        self.SET('keyword', keyword)
        self.SET('edit', edit)

    def endEdit(self, keyword):
        # 既存のスマートリストから一致するものを削除
        smartlist = list(filter(lambda x: x['keyword'] != keyword, self.getList()))
        # データを追加
        smartlist.append({'keyword': keyword})
        # ファイルに書き込む
        self.setList(smartlist)

    def delete(self, keyword):
        self.setList(filter(lambda x: x['keyword'] != keyword, self.getList()))
