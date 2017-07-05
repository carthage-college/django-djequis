import io
import os
import re
import sys
import ftplib
import argparse

from dateutil.relativedelta import relativedelta
from StringIO import StringIO

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH


from django.template import loader, Context
from django.utils.encoding import smart_bytes
from djequis.core.utils import sendmail
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
    output = t.render({ 'objs': data, 'next_year':NEXT_YEAR })

    return output

def main():
    sql = '''
        SELECT
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st,
            TRIM(NVL(INITCAP(ctry_table.txt), directory_vw.ctry)) AS ctry,
            zip, phone, email,
                MAX(
                    CASE grouping
                        WHEN    'Faculty'   THEN    3
                        WHEN    'Staff'     THEN    2
                        WHEN    'Student'   THEN    1
                                            ELSE    0
                    END
                    ) AS groupIndex, grouping
        FROM
            directory_vw
        LEFT JOIN ctry_table ON directory_vw.ctry = ctry_table.ctry
        GROUP BY
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st, ctry, zip, phone, email, grouping
        ORDER BY
            lastname, firstname, email
    '''
    folks = []
    if test:
        print sql
    sqlresult = do_sql(sql, earl=EARL)
    for s in sqlresult:
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
            'groupIndex':s[12],
            'grouping':s.grouping.decode('cp1252').encode('utf-8')
        })
    xml = paint_xml(folks)
    if test:
        print xml
        phile = "{}carthage_personas_draft_{:%Y-%m-%d}.xml".format(
            settings.OCLC_LOCAL_PATH,NOW
        )
        f = io.open(phile, 'w', encoding='utf8')
        f.write(xml)
        f.close()
        # send email that OCLC script has completed
        SUBJECT = '[OCLC SFTP] completed'
        BODY = 'OCLC SFTP process has been completed.\n\n'
        sendmail(
                settings.OCLC_TO_EMAIL,settings.OCLC_FROM_EMAIL,
                SUBJECT, BODY
            )
    else:
        temp = StringIO(xml.encode('utf-8'))
        ftp = ftplib.FTP(
            settings.OCLC_XTRNL_SRVR, settings.OCLC_XTRNL_USER,
            settings.OCLC_XTRNL_PASS
        )
        ftp.cwd(settings.OCLC_XTRNL_PATH)
        phile = "carthage_personas_draft_{:%Y-%m-%d}.xml".format(NOW)
        ftp.storlines("STOR " + phile, temp)
        ftp.quit()
        # send email that OCLC script has completed
        SUBJECT = '[OCLC SFTP] completed'
        BODY = 'OCLC SFTP process has been completed.\n\n'
        sendmail(
                settings.OCLC_TO_EMAIL,settings.OCLC_FROM_EMAIL,
                SUBJECT, BODY
            )

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
