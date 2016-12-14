import io
import os
import re
import sys
import ftplib
import csv
import argparse

from dateutil.relativedelta import relativedelta
from StringIO import StringIO

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

import django
django.setup()

from django.conf import settings
from django.template import loader, Context
from django.utils.encoding import smart_bytes

from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL
NEXT_YEAR = NOW + relativedelta(years=1)

# set up command-line options
desc = """
    Terradotta Synchronization
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def paint_xml(data):

    t = loader.get_template('oclc/personas.xml')
    c = Context({ 'objs': data, 'next_year':NEXT_YEAR })
    output = t.render(c)
    #print output
    return output

def main():
    sql = '''
        SELECT
            123456 AS UUUID, 'Kishline' AS Last_Name, 'Mike' AS First_Name, 'J.' AS Middle_Name, 'mkishline@carthage.edu' AS Email, '01/01/1970' AS DOB,
            'M' AS Gender, 'Y' AS Confidentiality_Indicator, 'Computer Science' AS Major_1, 'Classical Studies' AS Major_2, 'N/A' AS Minor_1, 'N/A' AS Minor_2,
            '4.0' AS GPA, '123 Test Drive' AS Home_Address_Line1, 'Suite 007' AS Home_Address_Line2, '2nd Floor' AS Home_Address_Line3, 'Kenosha' AS Home_Address_City,
            'WI' AS Home_Address_State, '53140' AS Home_Address_Zip, 'United States' AS Home_Address_Country, '262-867-5309' AS Phone_Number, 'SR' AS Class_Standing,
            'Batman' AS Emergency_Contact_Name, '262-228-2283' AS Emergency_Contact_Phone, 'Dark Knight' AS Emergency_Contact_Relationship,
            'United States' AS Country_of_Citizenship, 'White' AS Ethnicity, 'Y' AS Pell_Grant_Status,
            'Code Guy' AS HR_Title, '262-552-5527' AS HR_Campus_Phone, 'Y' AS HR_Flag,
            'ph1' AS Place_Holder_1, 'ph2' AS Place_Holder_2, 'ph3' AS Place_Holder_3, 'ph4' AS Place_Holder_4, 'ph5' AS Place_Holder_5,
            'ph6' AS Place_Holder_6, 'ph7' AS Place_Holder_7, 'ph8' AS Place_Holder_8, 'ph9' AS Place_Holder_9, 'ph10' AS Place_Holder_10,
            'ph11' AS Place_Holder_11, 'ph12' AS Place_Holder_12, 'ph13' AS Place_Holder_13, 'ph14' AS Place_Holder_14, 'ph15' AS Place_Holder_15
        FROM
            id_rec
        WHERE
            id_rec.id   =   371861
    '''
    folks = []
    if test:
        print sql
    sqlresult = do_sql(sql, earl=EARL)
    for s in sqlresult:
        if test:
            print "[{}] {}, {}: {} {}".format(
                s.id, s.lastname, s.firstname, s.email, s[12]
            )
        else:
            folks.append({
                'lastname':s.lastname.decode('cp1252').encode('utf-8'),
                'firstname':s.firstname.decode('cp1252').encode('utf-8'),
                'middlename':s.middlename.decode('cp1252').encode('utf-8'),
                'id':s.id,
                'addr_line1':s.addr_line1,
                'addr_line2':s.addr_line2,
                'city':s.city.decode('cp1252').encode('utf-8'),
                'st':s.st,
                'ctry':s.ctry.decode('cp1252').encode('utf-8'),
                'zip':s.zip,
                'phone':s.phone,
                'email':s.email,
                'groupIndex':s[12]
            })
    xml = paint_xml(folks)
    if test:
        print xml
    else:
        temp = StringIO(xml.encode('utf-8'))
        ftp = ftplib.FTP(
            settings.XTRNL_SRVR, settings.XTRNL_USER, settings.XTRNL_PASS
        )
        ftp.cwd(settings.XTRNL_PATH)
        phile = "carthage_personas_draft_{:%Y%m%d%H%M%S}.xml".format(NOW)
        ftp.storlines("STOR " + phile, temp)
        ftp.quit()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
