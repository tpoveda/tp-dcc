#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with email
"""

import os
import webbrowser
try:
    import urllib2 as urllib
except ImportError:
    import urllib

from tp.common.python import osplatform


def open_web(url):
    """
    Open given web URL in user web browser
    :param url: str
    """

    if osplatform.is_linux():
        try:
            os.system('gio open {}'.format(url))
        except Exception:
            webbrowser.open(url, 0)
    else:
        webbrowser.open(url, 0)


def safe_open_url(url):
    """
    Opens given URL in a safe way
    :param url: str
    :return:
    """

    try:
        result = urllib.urlopen(url)
    except urllib.HTTPError as exc:
        raise Exception('{} : {}'.format(exc, exc.url))

    return result
