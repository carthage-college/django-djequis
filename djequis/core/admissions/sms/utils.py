from twilio.base.exceptions import TwilioRestException

from djequis.core.admissions.sms.client import twilio_client as client


def is_valid_number(number):
    try:
        response = client.lookups.phone_numbers(number).fetch(type="carrier")
        return True
    except TwilioRestException as e:
        if e.code == 20404:
            return False
        else:
            raise e

