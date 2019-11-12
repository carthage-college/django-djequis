# from pathlib import Path
import requests
import os
import json
import base64
import django

# import time
# import datetime
# from datetime import datetime

# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()

from django.conf import settings
from django.core.cache import cache

AUTHORIZATION = 'Basic ' + settings.BB_SKY_CLIENT_ID + ":" + settings.BB_SKY_CLIENT_SECRET
urlSafeEncodedBytes = base64.urlsafe_b64encode(AUTHORIZATION.encode("utf-8"))
urlSafeEncodedStr = str(urlSafeEncodedBytes)

def get_local_token():
    current_token = cache.get('tokenkey')
    if current_token is None:
        # Read the file storing the latest access token
        with open(settings.BB_SKY_TOKEN_FILE, 'rb') as f:
            current_token = f.readline()
    return current_token


def get_refresh_token():
    refresh_token = cache.get('refreshkey')
    if refresh_token is None:
        # Read the file storing the latest access token
        with open(settings.BB_SKY_REFRESH_TOKEN_FILE, 'rb') as f:
            refresh_token = f.readline()
    return refresh_token


def token_refresh():
    print("In token_refresh")
    try:
        # Generates a new OAUTH2 access token and refresh token using
        # the current (unexpired) refresh token. Writes updated tokens
        # to appropriate files for subsequent reference
        # :return: Tuple containing (return_code, access_token, refresh_token)
        with open(settings.BB_SKY_REFRESH_TOKEN_FILE, 'r') as f:
            refresh_tokenf = f.readline()
            print(refresh_tokenf)
            refresh_token = get_refresh_token()
            print(refresh_token)
            ref_token_call = requests.post(
                url='https://oauth2.sky.blackbaud.com/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'grant_type': 'refresh_token',
                      'refresh_token': refresh_token,
                      'client_id': settings.BB_SKY_CLIENT_ID,
                      ## **** Can we enable this?
                      # ***'preserve_refresh_token': 'true',
                      'client_secret': settings.BB_SKY_CLIENT_SECRET,
                      # 'redirect_uri': settings.BB_SKY_CALLBACK_URI
                      }
            )

        status = ref_token_call.status_code
        response = ref_token_call.text

        if status == 200:
            tokens_dict = dict(json.loads(ref_token_call.text))
            refresh_token = tokens_dict['refresh_token']
            access_token = tokens_dict['access_token']

            # with open(settings.BB_SKY_TOKEN_FILE, 'w') as f:
            #     f.write(access_token)
            # (set, key,  value, expire time -- 0 means never)
            cache.set('tokenkey', access_token)

            # with open(settings.BB_SKY_REFRESH_TOKEN_FILE, 'w') as f:
            #     f.write(refresh_token)
            cache.set('refreshkey', refresh_token)

            # print(access_token)
            # print(refresh_token)

            return 1

        elif status == 403:  # OUT OF API QUOTA - Quit
            # Print HTML repsonse and exit function with empty DataFrame
            print('ERROR:  ' + str(status) + ":" + response)
            print('You\'re out of API Quota!')
            exit()
            return 0
        else:
            print('ERROR:  ' + str(status) + ":" + response)
            return 0

    except Exception as e:
        print("Error in token_refresh:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0
