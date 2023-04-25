#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with sqlite module
"""

import sqlite3


class ConnectionContext(object):
    """
    Contextual class that handles the connection and cursor mechanism. Its intended to be an optimisation to allow
    for multiple calls to occur without connection overheads
    """

    def __init__(self, identifier, commit=False, get=False):

        self._identifier = identifier
        self._commit = commit
        self._get = get

        self._connection = None
        self._cursor = None
        self._results = list()

    def __enter__(self):
        self._connection = sqlite3.connect(self._identifier)
        self._cursor = self._connection.cursor()
        self._cursor.execute("PRAGMA foreign_keys = ON")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._get:
            self._results = self._cursor.fetchall()

        if self._commit:
            self._connection.commit()

        self._connection.close()

    @property
    def cursor(self):
        return self._cursor

    @property
    def results(self):
        return self._results
