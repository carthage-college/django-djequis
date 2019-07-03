import calendar
import time
import datetime
import hashlib
import json
import requests


# Time in GMT
# GMT Zero hour is 1/1/70
x = 'Thu Jan 01 00:00:00 1970'
# print("Zero hour = " + x)
# Convert to a stucture format
y = time.strptime(x)
# print("Y = " + str(y))
#Calculate seconds from GMT zero hour
z = calendar.timegm(y)
# print("Zero hour in seconds = " + str(z))

# All we need is the following
# Current date and time
a = datetime.datetime.now()
# print("Current date and time = " + str(a))

# Format properly
b = a.strftime('%a %b %d %H:%M:%S %Y')
# print("B = " + b)

# convert to a struct time
c = time.strptime(b)
# print("C = " + str(b))

#Calculate seconds from GMT zero hour
utcts = calendar.timegm(c)
print("Seconds from UTC Zero hour = " + str(utcts))

sec_key = 'jP8yWR9WZar5vEtb6EZnqsYs'

hashstring = str(utcts) + sec_key
print("Hashstring = " + hashstring)


m = hashlib.md5()
print(m)
m.update(hashstring)
print(m.hexdigest)

# sendtime = datetime.now()
# print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

# url = "https://carthage.datacenter.adirondacksolutions.com/" \
#       "carthage_thd_test_support/apis/thd_api.cfc?" \
#       "method=studentBILLING&" \
#       "Key="+sec_key+"&" \
#       "utcts="+str(utcts)+"&" \
#       "h="+m.hexdigest+"&" \
#       "AccountCode=STD"
# print("URL = " + url)

url = "https://carthage.datacenter.adirondacksolutions.com/carthage_thd_test_support/apis/thd_api.cfc?method=studentBILLING&Key=jP8yWR9WZar5vEtb6EZnqsYs&utcts=1562154563&h=8e2e60889cfe4606a144ec597bbc7638&AccountCode=STD"
print("URL = " + url)

response = requests.get(url)
x = json.loads(response.content)
rtn = x['DATA'][0][0]
print(rtn)
print("Student ID = " + x['DATA'][0][0])
print("ItemDate = " + x['DATA'][0][1])
# print("Amount = " + str(x['DATA'][0][2]))
# print("TIMEFRAME = " + str(x['DATA'][0][3]))
# print("Term Code = " + x['DATA'][0][4])
# print("Bill Description = " + x['DATA'][0][5])
# print("Account Code = " + x['DATA'][0][6])
# print("Account Display Name = " + x['DATA'][0][7])
# print("Effective Date = " + x['DATA'][0][8])
# print("Exported = " + str(x['DATA'][0][9]))
# print("EXPORTTIMESTAMP = " + str(x['DATA'][0][10]))
# print("BILLEXPORTDATE  = " + str(x['DATA'][0][11]))
# print("TERMEXPORTSTARTDATE  = " + str(x['DATA'][0][12]))
# print("ITEMTYPE  = " + str(x['DATA'][0][13]))
# print("ASSIGNMENTID = " + str(x['DATA'][0][14]))
# print("DININGPLANID = " + str(x['DATA'][0][15]))
# print("STUDENTBILLINGINTERNALID = " + str(x['DATA'][0][16]))
# print("USERNAME = " + str(x['DATA'][0][17]))
# print("ADDITIONALID1 = " + str(x['DATA'][0][18]))

