"""SKY API Authentication/Query Scripts
Modified from code by Mitch Hollberg
(mhollberg@gmail.com, mhollberg@cfgreateratlanta.org)
Python functions to
    a) Get an initial SKYApi token/refresh token and write them to a local file
    b) Make subsequent refreshes and updates to the SKYApi authentication based on tokens in the files.
"""

# from pathlib import Path
import requests
import sys
import os
import json
import time
import base64
import datetime
import django

import cryptography
from cryptography import fernet
from cryptography.fernet import Fernet
# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()
# ________________
from django.conf import settings

AUTHORIZATION = 'Basic ' + settings.BB_SKY_CLIENT_ID + ":" + settings.BB_SKY_CLIENT_SECRET
urlSafeEncodedBytes = base64.urlsafe_b64encode(AUTHORIZATION.encode("utf-8"))
urlSafeEncodedStr = str(urlSafeEncodedBytes)
# print(urlSafeEncodedStr)

# For Cryptography,
# This only needs to happen once...store and re-use
# key = fernet.Fernet.generate_key()
# type(key)
# file = open('key.key', 'wb') # wb = write bytes
# file.write(key)
# file.close()

def get_local_token(token_file=settings.BB_SKY_TOKEN_FILE):
    # Get the key from the file for encryption
    file = open('key.key', 'rb')
    k = file.read()
    # print(k)
    frn = Fernet(k)
    file.close()

    # Read the file storing the latest access token
    with open(token_file, 'rb') as f:
        cur_token = f.readline()
        # current_token = frn.decrypt(cur_token)
        current_token = cur_token

    # print(current_token)
    # print(cur_token)

    return current_token


def token_refresh(refresh_token_file=settings.BB_SKY_REFRESH_TOKEN_FILE ,
                  token_file=settings.BB_SKY_TOKEN_FILE):
    print("In token_refresh")
    try:
        # Get the key from the file
        file = open('key.key', 'rb')
        key = file.read()
        file.close()
        frn = Fernet(key)

        # Generates a new OAUTH2 access token and refresh token using
        # the current (unexpired) refresh token. Writes updated tokens
        # to appropriate files for subsequent reference
        # :return: Tuple containing (return_code, access_token, refresh_token)

        # NOTE for some reason if I encrypt the token files, something crashes
        # here.  It may be that converting the encode(ASCII) necessary to do
        # the encryption needs to be reversed after the read
        with open(refresh_token_file, 'r') as f:
            refresh_token_encrpt = f.readline()
            # refresh_token = frn.decrypt(refresh_token_encrpt)
            refresh_token = refresh_token_encrpt

            # print(refresh_token)

            ref_token_call = requests.post(
                url='https://oauth2.sky.blackbaud.com/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'grant_type': 'refresh_token',
                      'refresh_token': refresh_token,
                      'client_id': settings.BB_SKY_CLIENT_ID,
                      ## **** Can we enable this? ***'preserve_refresh_token': 'true',
                      'client_secret': settings.BB_SKY_CLIENT_SECRET,
                      # 'redirect_uri': settings.BB_SKY_CALLBACK_URI
                      }
            )

        # Todo: confirm ref_token_call.status_Code == 200,
        #  otherwise raise error, log and message user
        # print('Token Refresh call return code: '
        #       + str(ref_token_call.status_code))
        status = ref_token_call.status_code
        response = ref_token_call.text

        if status == 400:
            # Print HTML repsonse and exit function with empty DataFrame
            print('ERROR:  ' + str(status) + ":" + response)
            # return df_out

        if status == 403:  # OUT OF API QUOTA - Quit
            # Print HTML repsonse and exit function with empty DataFrame
            print('ERROR:  ' + str(status) + ":" + response)
            print('You\'re out of API Quota!')
            exit()
            return None

        # if status != 200:
        #     refresh_status, current_token, _ = token_refresh()
        #     continue


        tokens_dict = dict(json.loads(ref_token_call.text))
        refresh_token = tokens_dict['refresh_token']
        access_token = tokens_dict['access_token']

        # access_token_encrypt = frn.encrypt(access_token.encode('ASCII'))
        # print(access_token_encrypt)
        with open(token_file, 'w') as f:
            f.write(access_token)

        # refresh_token_encrpt = frn.encrypt(refresh_token.encode('ASCII'))
        with open(refresh_token_file, 'w') as f:
            f.write(refresh_token)

        # print(ref_token_call.status_code)
        # print(access_token)
        # print(refresh_token)

        return (ref_token_call.status_code, access_token, refresh_token)

    except Exception as e:
        print("Error in token_refresh:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0

def call_api(current_token, url):
    print("In call_api")
    try:
        # url='https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes'):
        # Given a url representing a SKY API Endpoint
        # :param url: a SKY API Endpoint URL
        # :param current_token:

        params = {'HOST': 'api.sky.blackbaud.com'}
        # df_out = pd.DataFrame()

        status = 'Initial Value'

        while status != 200 or url != '':
            time.sleep(.2)  # SKY API Rate limited to 5 calls/sec

            headers = {'Bb-Api-Subscription-Key': settings.BB_SKY_SUBSCRIPTION_KEY,
                       'Authorization': 'Bearer ' + current_token}

            response = requests.get(url=url,
                                    params=params,
                                    headers=headers)
            status = response.status_code

            if status == 400:
                # Print HTML repsonse and exit function with empty DataFrame
                print('ERROR:  ' + str(status) + ":" + response.text)
                return 0

            elif status == 403:   # OUT OF API QUOTA - Quit
                # Print HTML repsonse and exit function with empty DataFrame
                print('ERROR:  ' + str(status) + ":" + response.text)
                print('You\'re out of API Quota!')
                return 0

            elif status != 200:
                refresh_status, current_token, _ = token_refresh()
                return 0

            else:
                response_dict = json.loads(response.text)
                return response_dict

            # try:
            #     if response_dict['count'] == 0:
            #         url = ''
            #     else:
            #         url = response_dict['next_link']
            # except:     # No 'next_link' element, have hit last paginated response
            #     url = ''
    except Exception as e:
        print("Error in call_api:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0

def get_const_custom_fields(current_token, id):
    print("In get_const_custom_fields")
    try:
        urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
                + str(id) + '/customfields'
        x = call_api(current_token, urlst)
        print(x)

        if x == 0:
            print("NO DATA")
            return 0
        else:
            for i in x['value']:
                print(i['category'])
                print(i['parent_id'])
                print(i['value'])
                print(i['type'])
                print(i['id'])
                print(i['date_modified'])
            return 1
    except Exception as e:
        print("Error in get_const_custom_fields:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0


def get_relationships(current_token, id):
    urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
            + str(id) + '/relationships'
    try:

        x = call_api(current_token, urlst)
        if x == 0:
            print("NO DATA")
            return 0
        else:
            for i in x['value']:
                # print(i)
                print(i['relation_id'])
                print(i['type'])
                print(i['constituent_id'])
                print(i['relation_id'])
                print(i['reciprocal_type'])
                print(i['id'])
                print(i['date_modified'])
                print(i['is_organization_contact'])
                print(i['is_primary_business'])
                print(i['is_spouse'])
                # print(i['start'])
            return 1
    except Exception as e:
        print("Error in get_relationships:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0
def get_custom_fields(current_token):
    urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields/categories/details'

    x = call_api(current_token, urlst)
    if x == 0:
        print("NO DATA")
        return 0
    else:
        for i in x['value']:
            # print(i)
            print(i['name'])
            print(i['type'])
        return 1

def set_const_custom_field(current_token, id):
    urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields'

    x = call_api(current_token, urlst)
    if x == 0:
        print("NO DATA")
        return 0
    else:
        # body = "{
        #         "category": "Student Status",
        #         "comment": "Test",
        #         "date": "2019-11-17T00:00:00",
        #        "parent_id": "19278",
        #         "value": "Alumni"
        #      } "
        for i in x['value']:
            # print(i)
            print(i['category'])
            print(i['parent_id'])
            print(i['value'])
            print(i['comment'])
        return 1

def main():
    try:
        # Token is stored in a text file
        current_token = get_local_token()
        # print("Current Token = ")
        # print(current_token)

        # ret = get_const_custom_fields(current_token, 19278)
        ret = get_custom_fields(current_token)
        # ret = get_relationships(current_token, 1534657)
        # ret = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/constituents/search?search_text=1534657')

        print(ret)
    except Exception as e:
        print("Error in main:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)




# Once we have the tokens, we can make calls to the API
# since these return different things, will need separate code blocks
# to parse the results
# ret = call_api(current_token,
#                'https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/relationshiptypes')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields
# /categories')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/educations/statuses')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/educations/schools')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/search
# ?search_text=1534657')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/countries')

# THIS ONE DOESN'T SEEM TO WORK...
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/1590307
# /relationships')
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/19278
# /constituentcodes')

# This will return the name and type of the custom field categories
# "Student Status", "Text"
# x = call_api(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields
# /categories/details')

if __name__ == "__main__":
    # args = parser.parse_args()
    # test = args.test
    # database = args.database

    # if not database:
    #     print "mandatory option missing: database name\n"
    #     parser.print_help()
    #     exit(-1)
    # else:
    #     database = database.lower()

    # if database != 'cars' and database != 'train' and database != 'sandbox':
    #     print "database must be: 'cars' or 'train' or 'sandbox'\n"
    #     parser.print_help()
    #     exit(-1)
    #
    # if not test:
    #     test = 'prod'
    # else:
    #     test = "test"

    sys.exit(main())
