import calendar
import time
import datetime
import hashlib
import json
import requests


# Time in GMT
# GMT Zero hour is 1/1/70
x = 'Thu Jan 01 00:00:00 1970'
print("Zero hour = " + x)
# Convert to a stucture format
y = time.strptime(x)
# print("Y = " + str(y))
#Calculate seconds from GMT zero hour
z = calendar.timegm(y)
print("Zero hour in seconds = " + str(z))

# All we need is the following
# Current date and time
a = datetime.datetime.now()
print("Current date and time = " + str(a))

# Format properly
b = a.strftime('%a %b %d %H:%M:%S %Y')
print("B = " + b)

# convert to a struct time
c = time.strptime(b)
print("C = " + str(b))

#Calculate seconds from GMT zero hour
d = calendar.timegm(c)
print("Seconds from UTC Zero hour = " + str(d))

sec_key = 'jP8yWR9WZar5vEtb6EZnqsYs'

hashstring =  str(d) + sec_key
print(hashstring)


m = hashlib.md5()
m.update(hashstring)
print m.hexdigest()

# sendtime = datetime.now()
# print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

url = "https://carthage.datacenter.adirondacksolutions.com/" \
      "carthage_thd_test_support/apis/thd_api.cfc?" \
      "method=studentBILLING&" \
      "Key=jP8yWR9WZar5vEtb6EZnqsYs&" \
      "utcts=1562154563&" \
      "h=8e2e60889cfe4606a144ec597bbc7638&" \
      "AccountCode=STD"

# url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street=" \
#       + v_street + "&city=" + v_city + "&state=" + v_state + "&ZIP=" + v_zip\
#       + \
#       "&benchmark=Public_AR_Current&vintage=Current_Current&format=json"

response = requests.get(url)
x = json.loads(response.content)
rtn = x['DATA'][0][0]
print(rtn)
print("Student ID = " +  x['DATA'][0][0])
print("ItemDate = " + x['DATA'][0][1])
print("Amount = " + str(x['DATA'][0][2]))
print("TIMEFRAME = " + str(x['DATA'][0][3]))
print("Term Code = " + x['DATA'][0][4])
print("Bill Description = " + x['DATA'][0][5])
print("Account Code = " + x['DATA'][0][6])
print("Account Display Name = " + x['DATA'][0][7])
print("Effective Date = " + x['DATA'][0][8])
print("Exported = " + str(x['DATA'][0][9]))
print("EXPORTTIMESTAMP = " + str(x['DATA'][0][10]))
print("BILLEXPORTDATE  = " + str(x['DATA'][0][11]))
print("TERMEXPORTSTARTDATE  = " + str(x['DATA'][0][12]))
print("ITEMTYPE  = " + str(x['DATA'][0][13]))
print("ASSIGNMENTID = " + str(x['DATA'][0][14]))
print("DININGPLANID = " + str(x['DATA'][0][15]))
print("STUDENTBILLINGINTERNALID = " + str(x['DATA'][0][16]))
print("USERNAME = " + str(x['DATA'][0][17]))
print("ADDITIONALID1 = " + str(x['DATA'][0][18]))
# print(studentID)

# if not x['result']['addressMatches']:
#     print("No match")
# else:
    # print("State from address components...")
    # address = x['result']['addressMatches'][0]['matchedAddress']
    # ---These are the individual components of the address
    # state_abrv = x['result']['addressMatches'][0]['addressComponents'][
    # 'state']
    # zip = x['result']['addressMatches'][0]['addressComponents']['zip']
    # streetName = x['result']['addressMatches'][0]['addressComponents'][
    # 'streetName']
    # preQualifier = x['result']['addressMatches'][0]['addressComponents'][
    # 'preQualifier']
    # preDirection = x['result']['addressMatches'][0]['addressComponents'][
    # 'preDirection']
    # preType = x['result']['addressMatches'][0]['addressComponents'][
    # 'preType']
    # suffixType = x['result']['addressMatches'][0]['addressComponents'][
    # 'suffixType']
    # suffixDirection = x['result']['addressMatches'][0][
    # 'addressComponents']['suffixDirection']
    # suffixQualifier = x['result']['addressMatches'][0][
    # 'addressComponents']['suffixQualifier']
    # print("Suffix qualifier = " + suffixQualifier)
    # print("Suffix direction = " + suffixDirection)
    # print("Suffix type = " + suffixType)

    # print("Formatted Full Address = " + address)
    # print("Formatted Street Address = " + address.split(', ')[0])
    # print("Formatted Street Address w Unit = " + address.split(', ')[0]
    #       + ' ' + v_unit.upper())
    # print("Formatted City = " + address.split(', ')[1])
    # print("Formatted State = " + address.split(', ')[2])
    # print("Formatted Zip = " + address.split(', ')[3])

    # if not x['result']['addressMatches'][0]['geographies']['Unified School
    # Districts']:
    # if not x['result']['addressMatches'][0]['geographies']['Counties']:
    #     print('No county detail data')
    # else:
    #     county_code = \
    #     x['result']['addressMatches'][0]['geographies']['Counties'][0][
    #         'COUNTY']
    #     print("County Code = " + str(county_code))
    #     county_name = \
    #     x['result']['addressMatches'][0]['geographies']['Counties'][0]['NAME']
    #     print("County = " + str(county_name))
    #     state_code = \
    #     x['result']['addressMatches'][0]['geographies']['Counties'][0]['STATE']
    #     print("State FIPS = " + str(state_code))

# print(a)
# a = 'Fri Jan 02 12:00:00 1970'
# b = time.strptime(a)
# c = calendar.timegm(a)


# print("Noon Jan 1 1970 = " + str(c))

