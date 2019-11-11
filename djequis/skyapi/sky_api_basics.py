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

# import cryptography
from datetime import datetime
# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()
# ________________
from django.conf import settings
from django.core.cache import cache

AUTHORIZATION = 'Basic ' + settings.BB_SKY_CLIENT_ID + ":" + settings.BB_SKY_CLIENT_SECRET
urlSafeEncodedBytes = base64.urlsafe_b64encode(AUTHORIZATION.encode("utf-8"))
urlSafeEncodedStr = str(urlSafeEncodedBytes)
# print(urlSafeEncodedStr)

def get_local_token(token_file=settings.BB_SKY_TOKEN_FILE):
    # x = cache.get('tokenkey')
    # y = cache.get('refreshkey')
    # print("Cache..")
    # print(x)
    # print(y)


    current_token = cache.get('tokenkey')
    if current_token is None:
        # Read the file storing the latest access token
        with open(token_file, 'rb') as f:
            current_token = f.readline()

    # print(current_token)

    return current_token

def get_refresh_token(refresh_token_file=settings.BB_SKY_REFRESH_TOKEN_FILE):
    # x = cache.get('tokenkey')
    # y = cache.get('refreshkey')
    # print("Cache..")
    # print(x)
    # print(y)

    refresh_token = cache.get('refreshkey')
    if refresh_token is None:
        # Read the file storing the latest access token
        with open(refresh_token_file, 'rb') as f:
            refresh_token = f.readline()

    # print(refresh_token)

    return refresh_token

def token_refresh(refresh_token_file=settings.BB_SKY_REFRESH_TOKEN_FILE ,
                  token_file=settings.BB_SKY_TOKEN_FILE):
    print("In token_refresh")
    # x = cache.get('tokenkey')
    # y = cache.get('refreshkey')
    try:
        # Generates a new OAUTH2 access token and refresh token using
        # the current (unexpired) refresh token. Writes updated tokens
        # to appropriate files for subsequent reference
        # :return: Tuple containing (return_code, access_token, refresh_token)

        # NOTE for some reason if I encrypt the token files, something crashes
        # here.  It may be that converting the encode(ASCII) necessary to do
        # the encryption needs to be reversed after the read
        with open(refresh_token_file, 'r') as f:
            refresh_tokenf = f.readline()
            print(refresh_tokenf)
            refresh_token = get_refresh_token()
            print(refresh_token)
            ref_token_call = requests.post(
                url='https://oauth2.sky.blackbaud.com/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'grant_type': 'refresh_token',
                      'refresh_token': refresh_tokenf,
                      'client_id': settings.BB_SKY_CLIENT_ID,
                      ## **** Can we enable this?
                      # ***'preserve_refresh_token': 'true',
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

        tokens_dict = dict(json.loads(ref_token_call.text))
        refresh_token = tokens_dict['refresh_token']
        access_token = tokens_dict['access_token']

        with open(token_file, 'w') as f:
            f.write(access_token)
            cache.set('tokenkey', access_token)

        with open(refresh_token_file, 'w') as f:
            f.write(refresh_token)
            cache.set('refreshkey', refresh_token)

        # print(ref_token_call.status_code)
        # print(access_token)
        # print(refresh_token)

        return 1
        # return refresh_token
        # return (ref_token_call.status_code, access_token, refresh_token)

    except Exception as e:
        print("Error in token_refresh:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0

def api_get(current_token, url):
    print("In api_get")
    try:
        params = {'HOST': 'api.sky.blackbaud.com'}
        status = 'Initial Value'

        while status != 200 or url != '':
            time.sleep(.2)  # SKY API Rate limited to 5 calls/sec

            headers = {'Bb-Api-Subscription-Key':
                           settings.BB_SKY_SUBSCRIPTION_KEY,
                       'Authorization': 'Bearer ' + current_token}

            response = requests.get(url=url,
                                    params=params,
                                    headers=headers)
            status = response.status_code
            # print(status)
            if status == 400:
                # Print HTML repsonse and exit function with empty DataFrame
                print('ERROR:  ' + str(status) + ":" + response.text)
                return 0

            elif status == 403:   # OUT OF API QUOTA - Quit
                # Print HTML repsonse and exit function with empty DataFrame
                print('ERROR:  ' + str(status) + ":" + response.text)
                print('You\'re out of API Quota!')
                return 0

            else:
                #     if response_dict['count'] == 0:
                response_dict = json.loads(response.text)
                return response_dict

    except Exception as e:
        print("Error in api_get:  " + e.message)
        # fn_write_error("Error in api_get - Main: "
        #                + e.message)
        return 0

def api_post(current_token, url, data):
    print("In api_post")
    try:
        params = {'HOST': 'api.sky.blackbaud.com'}
        status = 'Initial Value'

        headers = {'Content-Type': 'application/json',
                   'Bb-Api-Subscription-Key': settings.BB_SKY_SUBSCRIPTION_KEY,
                   'Authorization': 'Bearer ' + current_token}

        # while status != 200 or url != '':
        #     time.sleep(.2)  # SKY API Rate limited to 5 calls/sec

        # ref_token_call = requests.post(
        #     url='url',
        #     headers=headers,
        #     data={'grant_type': 'refresh_token',
        #           'refresh_token': refresh_token,
        #           'client_id': settings.BB_SKY_CLIENT_ID,
        #           ## **** Can we enable this? ***'preserve_refresh_token':
        #           # 'true',
        #           'client_secret': settings.BB_SKY_CLIENT_SECRET,
        #           # 'redirect_uri': settings.BB_SKY_CALLBACK_URI
        #           }
        # )


        # print(data)
        # Might need to be sent as 'data=json.dumps(data)
        response = requests.post(url=url, headers=headers,
                                params=params,
                                data=json.dumps(data)
                                )
        status = response.status_code
        stat_msg = response.text
        print(status)
        print(stat_msg)

        # if status == 400:
        #     # Print HTML repsonse and exit function with empty DataFrame
        #     print('ERROR:  ' + str(status) + ":" + response.text)
        #     return 0
        #
        # elif status == 403:   # OUT OF API QUOTA - Quit
        #     # Print HTML repsonse and exit function with empty DataFrame
        #     print('ERROR:  ' + str(status) + ":" + response.text)
        #     print('You\'re out of API Quota!')
        #     return 0
        #
        #
        # else:
        #     response_dict = json.loads(response.text)
        #     return response_dict

        # try:
        #     if response_dict['count'] == 0:
        #         url = ''
        #     else:
        #         url = response_dict['next_link']
        # except:     # No 'next_link' element, have hit last paginated
        # response
        #     url = ''
        return status
    except Exception as e:
        print("Error in api_get:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0

def get_const_custom_fields(current_token, id):
    print("In get_const_custom_fields")
    try:
        urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
                + str(id) + '/customfields'
        x = api_get(current_token, urlst)
        # print(x)

        if x == 0:
            print("NO DATA")
            return 0
        else:
            for i in x['value']:
                print("ID = " + i['id'])
                print("Category = " + i['category'])

                if 'comment' not in x['value']:
                    print("Comment not entered")
                else:
                    print("Comment = " + str(i['comment']))

                # print("Date = " + i['date'])
                # print("Date Added = " + i['date_added'])
                # print("Date Modified = " + i['date_modified'])
                print("Parent id = " + i['parent_id'])
                print("Type = " + i['type'])
                print("Value = " + i['value'])
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

        x = api_get(current_token, urlst)
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
    urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
            'customfields/categories/details'

    x = api_get(current_token, urlst)
    if x == 0:
        print("NO DATA")
        return 0
    else:
        for i in x['value']:
            # print(i)
            print(i['name'])
            print(i['type'])
        return 1

def get_custom_field_value(current_token, category):
    try:
        urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
                'customfields/categories/values?category_name=' + category
        x = api_get(current_token, urlst)
        if x == 0:
            print("NO DATA")
            return 0
        else:
            # for i in x['value']:
            print(x)
                # print(i)
            return 1
    except Exception as e:
        print("Error in get_custom_field_value:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)
        return 0

def get_constituent_id(current_token, carthid):
    try:
        urlst =  'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
                 'search?search_text=1534657&search_field=lookup_id'

        x = api_get(current_token, urlst)
        if x == 0:
            print("NO DATA")
            return 0
        else:
            for i in x['value']:
            # print(x)
                print(i['id'])
                print(i['name'])
                print(i['lookup_id'])
                print(i['inactive'])
            return 1
    except Exception as e:
        print("Error in get_constituent_id:  " + e.message)
        # fn_write_error("Error in get_constituent_id.py - Main: "
        #                + e.message)
        return 0


def set_const_custom_field(current_token, id, value, category, comment):
    # print(current_token)
    #         "name": "Achievement",
    #         "type": "CodeTableEntry"
    #         "name": "Involvement",
    #         "type": "CodeTableEntry"
    #         "name": "Student Status",
    #         "type": "Text"
    #
    urlst = 'https://api.sky.blackbaud.com/constituent/v1/constituents/' \
            'customfields'

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    body = {'category': category, 'comment': comment, 'date': date_time,
            'parent_id': id, 'value': value}

    # print(urlst, body)

    x = api_post(current_token, urlst, body)
    if x == 0:
        print("Post Failure")
        return 0
    else:
        return 1

def main():
    try:
        # Token is stored in a text file
        current_token = get_local_token()
        # print("Current Token = ")
        # print(current_token)

        # # First, we have to get the internal ID from blackbaud for
        # the constituent
        ret = get_constituent_id(current_token, 1534657)
        print(ret)

        # Also need to check to see if the custom field exists
        # Does not appear we can filter by category or type...WHY???
        # ret = get_const_custom_fields(current_token, 20369)
        # print(ret)

        # Then we can deal with the custom fields...
        # If there is an entry, we have to decide if we are posting a new item
        #   or patching an existing one
        # ret = set_const_custom_field(current_token, 20369, 'Not a student',
        #                              'Student Status', 'Testing a post')
        # print(ret)



        # ret = get_custom_fields(current_token)
        # ret = get_custom_field_value(current_token, 'Student Status')
        ret = get_relationships(current_token, 20369)
        print(ret)

        # Refreshthe API tokens
        r = token_refresh()
        print(r)

    except Exception as e:
        print("Error in main:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)



# Once we have the tokens, we can make calls to the API
# since these return different things, will need separate code blocks
# to parse the results
# ret = api_get(current_token,
#                'https://api.sky.blackbaud.com/constituent/v1/
#                constituentcodetypes')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/relationshiptypes')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields
# /categories')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/educations/statuses')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/educations/schools')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/search
# ?search_text=1534657')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/countries')

# THIS ONE DOESN'T SEEM TO WORK...
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/1590307
# /relationships')
# x = api_get(current_token,
# 'https://api.sky.blackbaud.com/constituent/v1/constituents/19278
# /constituentcodes')

# This will return the name and type of the custom field categories
# "Student Status", "Text"
# x = api_get(current_token,
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
