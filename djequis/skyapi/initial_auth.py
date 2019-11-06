# from pathlib import Path
import requests
import os
import json
import time
import base64
import datetime
import cryptography
from cryptography import fernet
from cryptography.fernet import Fernet

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

# For Cryptography,
# This only needs to happen once...store and re-use
key = fernet.Fernet.generate_key()
type(key)
file = open('key.key', 'wb') # wb = write bytes
file.write(key)
file.close()


def get_initial_token():
    """
    Execute process for user to authenticate and generate an OAUTH2
     token to the SKY API
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
    # this input wasn't working for some reason...
    authorization_code = raw_input("Paste code here: ")
    # authorization_code = input('Paste code here: ')
    # authorization_code = '8452fcbbc85f4b269fe5a10e659a9b0d'
    print("Authorization Code = ")
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
    print(tokens_dict)

    # for key, value in tokens_dict.items():
        # print(key)
        # print(value)
        # print(key + ":" + value)
        # print(f'{key}: {value}')

    print("-------------------------------")
    refresh_token = tokens_dict['refresh_token']
    print("refresh_token = ")
    print(refresh_token)

    # # os.remove(TOKEN_FILE)
    # # os.remove(REFRESH_TOKEN_FILE)
    # #
    # refresh_token_encrpt = frn.encrypt(refresh_token)
    # print(refresh_token_encrpt)
    #
    print("-------------------------------")
    access_token = tokens_dict['access_token']
    print("access_token = ")
    print(access_token)
    #
    # # access_token_encrypt = frn.encrypt(access_token)
    # # print(access_token_encrypt)
    #
    # # with open(TOKEN_FILE, 'wb') as f:
    # #     f.write(access_token)
    # #
    # # with open(REFRESH_TOKEN_FILE, 'wb') as f:
    # #     f.write(refresh_token_encrpt)
    #
    # return ref_token_getter.status_code

    # Get the key from the file for encryption
    file = open('key.key', 'rb')
    key = file.read()
    file.close()
    print(key)
    # frn = Fernet(key)
    frn = fernet.Fernet(key)
    txt = refresh_token.encode('ASCII')
    print txt

    txt2 = frn.encrypt(txt)
    print txt2

    with open("encrypted.txt", 'w') as f:
        f.write(txt2)

    with open("encrypted.txt", 'r') as f:
            decrypted = f.readline()

    txt3 = frn.decrypt(decrypted)
    print txt3

    return 1


def main():
    print("hi")
    ret = get_initial_token()
    print(ret)

main()