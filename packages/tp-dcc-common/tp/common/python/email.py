#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities functions emails
"""

import email
import smtplib
from email.mime.text import MIMEText


class Email(object):
    def __init__(self, user=None, password=None):
        self._user = user
        self._password = password
        self._emails_list = list()
        self._server = None

        self._setup_message()

    def set_subject(self, subject):
        self._message['Subject'] = subject

    def add_message(self, text):
        self._message.attach(MIMEText(text))

    def send(self, list_of_emails):
        joined = email.Utils.COMMASPACE.join(list_of_emails)
        self._message['To'] = joined
        self._setup_server()
        self._server.sendmail(self._user, list_of_emails, self._message.as_string())
        self._server.quit()

    def _setup_server(self):
        self._server = smtplib.SMTP()
        self._server.set_debuglevel(1)

    def _setup_message(self):
        self._message = email.MIMEMultipart.MIMEMultipart()
        self._message['From'] = self._user
        self._message['Subject'] = ''
        self._message['To'] = list()


class LocalHost(Email, object):
    def __init__(self, user):
        super(LocalHost, self).__init__(user=user)

    def _setup_server(self):
        self._server = smtplib.SMTP('localhost')


class Gmail(Email, object):
    def _setup_server(self):
        super(Gmail, self)._setup_server()

        smtp_host = 'smtp.gmail.com'
        smtp_port = 587
        self._server.connect(smtp_host, smtp_port)
        self._server.ehlo()
        self._server.starttls()
        self._server.login(self._user, self._password)
