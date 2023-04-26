#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different functions related with encryptation
"""

import base64


def encode_base64(key, clear):
	"""
	Encodes given key as base64.

	:param str key: key to encode.
	:param str clear: string to encode.
	:return: base64 encoded data.
	:rtype: bytes
	"""

	enc = list()
	for i in range(len(clear)):
		key_c = key[i % len(key)]
		enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
		enc.append(enc_c)

	return base64.urlsafe_b64encode(''.join(enc))


def decode_base64(key, enc):
	"""
	Decodes base 64.

	:param str key: decode key.
	:param bytes enc: base64 encoded data.
	:return:
	"""

	dec = list()
	enc = base64.urlsafe_b64decode(enc)
	for i in range(len(enc)):
		key_c = key[i % len(key)]
		dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
		dec.append(dec_c)

	return ''.join(dec)
