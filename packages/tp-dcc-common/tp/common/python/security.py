#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different functions related with security
"""

import base64


def encodeBase64(key, clear):
    enc = list()
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)

    return base64.urlsafe_b64encode(''.join(enc))


def decodeBase64(key, enc):
    dec = list()
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)

    return ''.join(dec)
