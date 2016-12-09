import io
import os
import re
import sys
import ftplib
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
    OCLC Synchronization
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
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st, ctry, zip, phone, email,
                MAX(
                    CASE grouping
                        WHEN    'Faculty'   THEN    3
                        WHEN    'Staff'     THEN    2
                        WHEN    'Student'   THEN    1
                                            ELSE    0
                    END
                    ) AS groupIndex
        FROM
            directory_vw
        GROUP BY
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st, ctry, zip, phone, email
        ORDER BY
            lastname, firstname, email
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
