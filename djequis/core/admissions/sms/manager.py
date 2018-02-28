# -*- coding: utf-8 -*-
from django.conf import settings

from djequis.core.admissions.sms.client import twilio_client


class Message(object):

    def __init__(self):

        self.client = twilio_client

    def status(self, sid, status):

        count = 0
        ms = self.client.messages(sid).fetch()
        while ms.status != status:
            # we limit the loop to 10 just in case something goes amiss
            # with the REST API end point. it can return:
            # accepted, queued, sending, sent, receiving or received.
            # and then finally delivered, undelivered, or failed.
            if count < 10:
                ms = self.client.messages(sid).fetch()
            else:
                break
            count += 1
            if ms.status == status:
                break

        return ms
