#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to languages
"""

import re
import os
import locale


class Language(object):
    def __init__(self, en='', es='', jp=''):
        self.en = en
        self.es = es
        self.jp = jp

    def output(self):
        lang = 'en'
        env = re.sub('_.+', '', os.environ.get('MAYA_UI_LANGUAGE', ''))
        loc = re.sub('_.+', '', locale.getdefaultlocale()[0])
        env = re.sub('-.+', '', env)
        loc = re.sub('-.+', '', loc)

        if loc != '':
            lang = loc
        if env != '':
            lang = env
        if lang == 'ja' or lang == 'jp':
            return self.jp
        elif lang == 'en':
            return self.en
        elif lang == 'es':
            return self.es
        return self.en
