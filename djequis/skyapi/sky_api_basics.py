"""SKY API Authentication/Query Scripts
Mitch Hollberg (mhollberg@gmail.com, mhollberg@cfgreateratlanta.org)
Python functions to
    a) Get an initial SKYApi token/refresh token and write them to a local file
    b) Make subsequent refreshes and updates to the SKYApi authentication based on tokens in the files.

"""

# from pathlib import Path
import requests
import json
import time
# import pandas as pd
import base64
import datetime

# Look here https://developer.blackbaud.com/apps/ to get following codes
CLIENT_ID = '71489b32-efa5-4459-aa3a-2845d327de4e'  # aka application ID
CLIENT_SECRET = '9Hz3qk8NhHRndn2vy84k4g11gqR9nGFznAHUYOntrmE='  # aka Application Secret

# We'll store our tokens in local files; specify file locations below
TOKEN_FILE = "SKYApi_Token.txt"
REFRESH_TOKEN_FILE = "SKYApi_Refresh_Token.txt"

CALLBACK_URI = r'https://www.getpostman.com/oauth2/callback'
AUTHORIZE_URL = "https://oauth2.sky.blackbaud.com/authorization"
TOKEN_URL = "https://oauth2.sky.blackbaud.com/token"

AUTHORIZATION = 'Basic ' + CLIENT_ID + ":" + CLIENT_SECRET
urlSafeEncodedBytes = base64.urlsafe_b64encode(AUTHORIZATION.encode("utf-8"))
urlSafeEncodedStr = str(urlSafeEncodedBytes)
# print(urlSafeEncodedStr)


SUBSCRIPTION_KEY = r'02e7fb9ac1794913b10df1d78bde15d7'



def get_initial_token():
    """
    Execute process for user to authenticate and generate an OAUTH2
     token to the SKY API
     Mitch Hollberg (mhollberg@gmail.com /mhollberg@cfgreateratlanta.org)
    :return:
    """
    # step A - simulate a request from a browser on the authorize_url:
    # will return an authorization code after the user is
    # prompted for credentials.

    authorization_redirect_url = AUTHORIZE_URL + \
                                 '?response_type=code&client_id=' + \
                                 CLIENT_ID + '&redirect_uri=' \
                                 + CALLBACK_URI

    print("Click the following url and authorize. It will redirect you to a blank website with the url"
          " 'https://127.0.0.1/?code=xxxx'. Copy the value of the code (after the '=' sign). "
          "Paste that code into the prompt below.")
    print("---  " + authorization_redirect_url + "  ---")
    # this input wasn't working for some reason...didn't like data type?
    # authorization_code = input('Paste code here: ')
    authorization_code = 'c670bf242da34d028e2d254bd5433baf'
    print(authorization_code)


    # STEP 2: Take initial token, retrieve access codes and floater token
    ref_token_getter = requests.post(
        url='https://oauth2.sky.blackbaud.com/token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={'grant_type': 'authorization_code',
              'code': authorization_code,
              'client_id': CLIENT_ID,
              'client_secret': CLIENT_SECRET,
              'redirect_uri': CALLBACK_URI}
    )

    tokens_dict = dict(json.loads(ref_token_getter.text))
    # print(tokens_dict)

    # for key, value in tokens_dict.items():
        # print(key)
        # print(value)
        # print(key + ":" + value)
        # print(f'{key}: {value}')

    refresh_token = tokens_dict['refresh_token']
    access_token = tokens_dict['access_token']

    with open(TOKEN_FILE, 'w') as f:
        f.write(access_token)

    with open(REFRESH_TOKEN_FILE, 'w') as f:
        f.write(refresh_token)

    return ref_token_getter.status_code


def get_local_token(token_file=TOKEN_FILE):
    """
    Read the file storing the latest access token
    :return: value of current authentication token
    """
    with open(token_file, 'r') as f:
        current_token = f.readline()

    return current_token


def token_refresh(refresh_token_file=REFRESH_TOKEN_FILE,
                  token_file=TOKEN_FILE):
    """
    Generates a new OAUTH2 access token and refresh token using
    the current (unexpired) refresh token. Writes updated tokens
    to appropriate files for subsequent reference
    :param refresh_token_file: filepath of file storing refresh token
    :param token_file: filepath of file storing access token
    :return: Tuple containing (return_code, access_token, refresh_token)
    """
    with open(refresh_token_file, 'r') as f:
        refresh_token = f.readline()

    with open(TOKEN_FILE, 'r') as f:
        current_token = f.readline()

        ref_token_call = requests.post(
            url='https://oauth2.sky.blackbaud.com/token',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={'grant_type': 'refresh_token',
                  'refresh_token': refresh_token,
                  'client_id': CLIENT_ID,
                  ## **** Can we enable this? ***'preserve_refresh_token': 'true',
                  'client_secret': CLIENT_SECRET,
                  # 'redirect_uri': CALLBACK_URI
                  }
        )

    # Todo: confirm ref_token_call.status_Code == 200,
    #  otherwise raise error, log and message user
    # print(f'Token Refresh call return code: {ref_token_call.status_code}')

    tokens_dict = dict(json.loads(ref_token_call.text))
    refresh_token = tokens_dict['refresh_token']
    access_token = tokens_dict['access_token']

    with open(token_file, 'w') as f:
        f.write(access_token)

    with open(refresh_token_file, 'w') as f:
        f.write(refresh_token)

    return (ref_token_call.status_code, access_token, refresh_token)


def call_api(current_token,
             url='https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes'):
    """
    Given a url representing a SKY API Endpoint

    :param url: a SKY API Endpoint URL
    :param current_token:
    :return: Pandas DataFrame object
    """

    params = {'HOST': 'api.sky.blackbaud.com'}
    # df_out = pd.DataFrame()

    status = 'Initial Value'

    while status != 200 or url != '':
        time.sleep(.2)  # SKY API Rate limited to 5 calls/sec

        headers = {'Bb-Api-Subscription-Key': SUBSCRIPTION_KEY,
                   'Authorization': 'Bearer ' + current_token}

        response = requests.get(url=url,
                                params=params,
                                headers=headers)
        status = response.status_code


        if status == 400:
            # Print HTML repsonse and exit function with empty DataFrame
            print('ERROR:  ' + str(status) + ":" + response.text)
            # return df_out

        if status == 403:   # OUT OF API QUOTA - Quit
            # Print HTML repsonse and exit function with empty DataFrame
            print('ERROR:  ' + str(status) + ":" + response.text)
            print('You\'re out of API Quota!')
            exit()
            return None

        if status != 200:
            refresh_status, current_token, _ = token_refresh()
            continue
        response_dict = json.loads(response.text)

        try:
            if response_dict['count'] == 0:
                url = ''
            else:
                url = response_dict['next_link']
        except:     # No 'next_link' element, have hit last paginated response
            url = ''

        for i in response_dict['value']:
            print(i)

    return 1


def main():
    # This should only need to be run once every 60 days ???
    # Not that the authorization code changes with every run, can't re-run
    # without returning the new auth code

    # ret = get_initial_token()
    # print("Initial Token = ")
    # print(ret)

    # Token is stored in a text file
    current_token = get_local_token()
    # print("Current Token = ")
    # print(current_token)

    # Refresh token works around the 60 minute expiration of the authorization
    ret2 = token_refresh(REFRESH_TOKEN_FILE, TOKEN_FILE)
    # print("Refresh Token = ")
    # print(ret2)

    # Once we have the tokens, we can make calls to the API
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/constituentcodetypes')
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/relationshiptypes')
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields/categories')
    x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/educations/statuses')
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/educations/schools')
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/constituents/search?search_text=1534657')
    # x = call_api(current_token, 'https://api.sky.blackbaud.com/constituent/v1/countries')

    print(str(x))

main()

