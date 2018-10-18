import os
import requests
import json
import string
import sys
import csv
import datetime
import codecs
import argparse
from sqlalchemy import text
import shutil

url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street=919 Charles Ave&city=Winthrop Harbor&state=IL&ZIP=60096&benchmark=Public_AR_Current&vintage=Current_Current&layers=14&format=json"

response = requests.get(url)
x = json.loads(response.content)
# x = response.json()
# print(x)
# print(x['result'])
print("State from address components...")
print(x['result']['addressMatches'][0]['addressComponents']['state'])

print("Geographies:  States:")
print(x['result']['addressMatches'][1]['geographies']['States'])

print("Item in states")
print(x['result']['addressMatches'][1]['geographies']['States'][0]['NAME'])


print("down another level")
print(x['result']['addressMatches'][1]['coordinates'])


# print(x['addressComponents'])


    # x = json.loads(response.content)
    # print("Latitude = " + str(x['lat']))
    # print("Longitude = " + str(x['lng']))
    # Get request for distance between two zips
    # http://www.zipcodeapi.com/rest/<api_key>/distance.<format>/<zip_code1<zip_code2>/<units>
    # response2 = requests.get"http://www.zipcodeapi.com/rest
    # response2 = requests.get("http://www.zipcodeapi.com/rest/" + APIKey + "/" + distformat + "/" + CarthZip + "/" + zipcode + "/" + distunits)
    # y = json.loads(response2.content)
    # print("Distance from Carthage = " + str(y['distance']))
