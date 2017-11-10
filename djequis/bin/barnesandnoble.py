import os
import sys
import pysftp
import csv
import time
import argparse
import shutil

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

from djequis.sql.barnesandnoble import TMP_ACTV_SESS
from djequis.sql.barnesandnoble import STU_ACAD_REC_100
from djequis.sql.barnesandnoble import STU_ACAD_REC_200
from djequis.sql.barnesandnoble import EXENRCRS
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL

desc = """
    Barnes and Noble Upload
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    # formatting date and time string 
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # set dictionary
    dict = {
        'AR100': STU_ACAD_REC_100,
        'AR200': STU_ACAD_REC_200,
        'EXENRCRS': EXENRCRS
        }
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # sFTP connection information for Barnes and Noble 1
    XTRNL_CONNECTION1 = {
        'host':settings.BARNESNOBLE1_HOST,
        'username':settings.BARNESNOBLE1_USER,
        'password':settings.BARNESNOBLE1_PASS,
        'port':settings.BARNESNOBLE1_PORT,
        'cnopts':cnopts
    }
    # sFTP connection information for Barnes and Noble 2
    XTRNL_CONNECTION2 = {
        'host':settings.BARNESNOBLE2_HOST,
        'username':settings.BARNESNOBLE2_USER,
        'password':settings.BARNESNOBLE2_PASS,
        'port':settings.BARNESNOBLE2_PORT,
        'cnopts':cnopts
    }
    for key, value in dict.items():
        if test:
            print key
        #######################################################################
        # Dict Value 'STU_ACAD_REC_100' selects active students and sets budget
        # limit for export (books = '100' & $3000.00)

        # Dict Value 'STU_ACAD_REC_200' selects active students and sets budget
        # limit for export (supplies = '200' & $50.00)

        # Dict Value 'EXENCRS' selects all current and future course-sections
        # (sec_rec) and instructor for Bookstore to order ISBN inventory
        #######################################################################
        sql = do_sql(value, earl=EARL)
        rows = sql.fetchall()
        for row in rows:
            if test:
                print row
        # set directory and filename to be stored
        filename=('{0}{1}.csv'.format(
            settings.BARNESNOBLE_CSV_OUTPUT,key
        ))
        # set destination path and new filename that it will be renamed to when archived
        archive_destination = ('{0}{1}_{2}_{3}.csv'.format(
            settings.BARNESNOBLE_CSV_ARCHIVED,'CCBAK',key,datetimestr
        ))
        # create .csv file
        csvfile = open(filename,"w");
        output = csv.writer(csvfile)
        # write header row to file
        if test:
            if key == 'AR100' or key == 'AR200': # write header row for (AR100, AR200)
                output.writerow([
                    "StudentID", "Elastname", "Efirstname", "Xmiddleinit",
                    "Xcred_limit", "EProviderCode", "Ebegdate", "Eenddate",
                    "Eidtype", "Erecordtype", "Eaccttype"
                    ])
            else: # write header row for EXENCRS
                output.writerow([
                    "bnUnitNo", "bnTerm", "bnYear", "bnDept", "bnCourseNo",
                    "bnSectionNo", "bnProfName", "bnMaxCapcty", "bnEstEnrlmnt",
                    "bnActEnrlmnt", "bnContdClss", "bnEvngClss", "bnExtnsnClss",
                    "bnTxtnetClss", "bnLoctn", "bnCourseTitl", "bnCourseID"
                ])
        # write data rows to file
        if rows is not None:
            for row in rows:
                output.writerow(row)
        else:
            print ("No values in list")
        csvfile.close()
        # renaming old filename to newfilename and move to archive location
        shutil.copy(filename, archive_destination)
    # set local path {/data2/www/data/barnesandnoble/}
    source_dir = ('{0}'.format(settings.BARNESNOBLE_CSV_OUTPUT))
    # set local path and filenames
    # variable == /data2/www/data/barnesandnoble/{filename.csv}
    fileAR100 = source_dir + 'AR100.csv'
    fileAR200 = source_dir + 'AR200.csv'
    fileEXENCRS = source_dir + 'EXENRCRS.csv'
    # sFTP PUT moves the EXENCRS.csv file to the Barnes & Noble server 1
    try:
        with pysftp.Connection(**XTRNL_CONNECTION1) as sftp:
            # used for testing
            #sftp.chdir("TestFiles/")
            sftp.put(fileEXENCRS, preserve_mtime=True)
            # deletes original file from our server
            os.remove(fileEXENCRS)
            # closes sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'BARNES AND NOBLE UPLOAD failed'
        BODY = 'Unable to PUT EXENCRS.csv to Barnes and Noble server.\n\n{0}'.format(str(e))
        sendmail(
            settings.BARNESNOBLE_TO_EMAIL,settings.BARNESNOBLE_FROM_EMAIL,
            BODY, SUBJECT
        )
    # sFTP PUT moves the AR100.csv file to the Barnes & Noble server 2
    try:
        with pysftp.Connection(**XTRNL_CONNECTION2) as sftp:
            # used for testing
            #sftp.chdir("TestFiles/")
            sftp.put(fileAR100, preserve_mtime=True)
            sftp.chdir("ToBNCB/")
            sftp.put(fileAR100, preserve_mtime=True)
            # deletes original file from our server
            os.remove(fileAR100)
            # closes sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'BARNES AND NOBLE UPLOAD failed'
        BODY = 'Unable to PUT AR100.csv to Barnes and Noble server.\n\n{0}'.format(str(e))
        sendmail(
            settings.BARNESNOBLE_TO_EMAIL,settings.BARNESNOBLE_FROM_EMAIL,
            BODY, SUBJECT
        )
    # sFTP PUT moves the AR200.csv file to the Barnes & Noble server 2
    try:
        with pysftp.Connection(**XTRNL_CONNECTION2) as sftp:
            # used for testing
            #sftp.chdir("TestFiles/")
            sftp.put(fileAR200, preserve_mtime=True)
            sftp.chdir("ToBNCB/")
            sftp.put(fileAR200, preserve_mtime=True)
            # deletes original file from our server
            os.remove(fileAR200)
            # closes sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'BARNES AND NOBLE UPLOAD failed'
        BODY = 'Unable to PUT AR200.csv to Barnes and Noble server.\n\n{0}'.format(str(e))
        sendmail(
            settings.BARNESNOBLE_TO_EMAIL,settings.BARNESNOBLE_FROM_EMAIL,
            BODY, SUBJECT
        )
    # sFTP upload complete send success message
    SUBJECT = 'BARNES AND NOBLE UPLOAD successful'
    BODY = 'The Barnes and Noble files files were successfully uploaded to the server.'
    sendmail(
        settings.BARNESNOBLE_TO_EMAIL,settings.BARNESNOBLE_FROM_EMAIL,
        BODY, SUBJECT
    )

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
