import calendar
import time
import datetime
import hashlib
import json
import requests
import csv



print("x")

def encode_rows_to_utf8(rows):
    encoded_rows = []
    for row in rows:
        try:
            encoded_row = []
            for value in row:
                if isinstance(value, basestring):
                    value = value.decode('cp1252').encode("utf-8")
                encoded_row.append(value)
            encoded_rows.append(encoded_row)
        except Exception as e:
            fn_write_error("Error in encoded_rows routine " + e.message)
    return encoded_rows

def write_header():
    print("Write Header")
    with open('room_output.csv', 'wb') as room_output:
        csvWriter = csv.writer(room_output)
        csvWriter.writerow(["STUDENTNUMBER","ITEMDATE","AMOUNT","TIMEFRAME",
                            "TIMEFRAMENUMERICCODE","BILLDESCRIPTION",
                            "ACCOUNT","ACCOUNT_DISPLAY_NAME","EFFECTIVEDATE",
                            "EXPORTED","EXPORTTIMESTAMP","BILLEXPORTDATE",
                            "TERMEXPORTSTARTDATE","ITEMTYPE","ASSIGNMENTID",
                            "DININGPLANID","STUDENTBILLINGINTERNALID",
                            "USERNAME","ADDITIONALID1"])


def main():

    print("Main")
    try:
      # Time in GMT
      # GMT Zero hour is 1/1/70
      x = 'Thu Jan 01 00:00:00 1970'
      # print("Zero hour = " + x)
      # Convert to a stucture format
      y = time.strptime(x)
      # print("Y = " + str(y))
      #Calculate seconds from GMT zero hour
      z = calendar.timegm(y)
      print("Zero hour in seconds = " + str(z))

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

      # mystring = 'Enter String to hash'
      # Assumes the default UTF-8
      hash_object = hashlib.md5(hashstring.encode())
      print(hash_object.hexdigest())

      # sendtime = datetime.now()
      # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

      url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key="+sec_key+"&" \
            "utcts="+str(utcts)+"&" \
            "h="+hash_object.hexdigest()+"&" \
            "AccountCode=CMTR,ABRD,NOCH,UNDE,OFF,RABD,RFDB,RFPB,RFOD,RFOS," \
                    RFQU,RFT2,CCHI,STD,RFSG,RFTR,RFTD,RFTS,RFAP"
      print("URL = " + url)

      # url = "https://carthage.datacenter.adirondacksolutions.com/
      # carthage_thd_test_support/apis/thd_api.cfc?method=studentBILLING&
      # Key=jP8yWR9WZar5vEtb6EZnqsYs&
      # utcts=1562154563&
      # h=8e2e60889cfe4606a144ec597bbc7638&
      # AccountCode=STD"
      # print("URL = " + url)

      response = requests.get(url)
      x = json.loads(response.content)
      # print(x)
      y = (len(x['DATA'][0][0]))
      if not x['DATA']:
          print("No match")
      else:
          write_header()
          print("Start Loop")
          with open('room_output.csv', 'ab') as room_output:
              for i in x['DATA']:
                  print(i[0])

                  csvWriter = csv.writer(room_output, quoting=csv.QUOTE_NONNUMERIC)
                  csvWriter.writerow([i[0] + ',' + i[1] + ',' + str(i[2]) + ','
                  + str(i[3]) + ',' + i[4] + ',' + i[5] + ','
                  + i[6] + ',' + i[7] + ',' + i[8] + ','
                  + str(i[9]) + ',' + str(i[0]) + ','
                  + str(i[11]) + ',' + str(i[12]) + ','
                  + str(i[13]) + ',' + str(i[14]) + ','
                  + str(i[15]) + ',' + str(i[16]) + ','
                  + str(i[17]) + ',' + str(i[18])
                          ])


    except Exception as e:
          print("Error in adirondack_std_billing_api.py- Main:  " + e.message)
          # fn_write_error("Error in adirondack_std_billing_api.py - Main: "
          #                + e.message)

if __name__ == "__main__":
    main()
#     args = parser.parse_args()
#     test = args.test
#     database = args.database
#
# if not database:
#     print "mandatory option missing: database name\n"
#     parser.print_help()
#     exit(-1)
# else:
#     database = database.lower()
#
# if database != 'cars' and database != 'train' and database != 'sandbox':
#     print "database must be: 'cars' or 'train' or 'sandbox'\n"
#     parser.print_help()
#     exit(-1)
#
# sys.exit(main())
