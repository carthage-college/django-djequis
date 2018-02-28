# -*- coding: utf-8 -*-
from django.conf import settings

from djequis.core.admissions.sms.client import twilio_client as client

from twilio.base.exceptions import TwilioRestException


class Message(object):

    def __init__(self):

        self.client = client

    def status(self, sid, status):

        count = 0
        ms = self.client.messages(sid).fetch()
        while ms.status != status:
            # we limit the loop to 100 for now. the REST API end point
            # can take some time to return a status, which could be:
            # accepted, queued, sending, sent, receiving, or received.
            # and then finally delivered, undelivered, or failed.
            if count < 100:
                ms = self.client.messages(sid).fetch()
            else:
                break
            count += 1
            if ms.status == status:
                break

        return ms


    def valid_number(self, number):

        try:
            response = self.client.lookups.phone_numbers(number).fetch(
                type='carrier'
            )
            return True
        except TwilioRestException as e:
            if e.code == 20404:
                return False
            else:
                raise e
