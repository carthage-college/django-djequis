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

from djequis.sql.barnesandnoble import DROP_TMP_GRACE
from djequis.sql.barnesandnoble import DROP_TMP_ACTV_SESS
from djequis.sql.barnesandnoble import DROP_TMP_UBAL
from djequis.sql.barnesandnoble import DROP_TMP_FUTURE_CRS
from djequis.sql.barnesandnoble import TMP_GRACE
from djequis.sql.barnesandnoble import SELECT_TMP_SESS_GRACE
from djequis.sql.barnesandnoble import TMP_ACTV_SESS
from djequis.sql.barnesandnoble import SELECT_TMP_ACTV_SESS
from djequis.sql.barnesandnoble import TMP_UBAL
from djequis.sql.barnesandnoble import SELECT_TMP_UBAL
from djequis.sql.barnesandnoble import STU_ACAD_REC_100
from djequis.sql.barnesandnoble import STU_ACAD_REC_200
from djequis.sql.barnesandnoble import TMP_FUTURE_CRS
from djequis.sql.barnesandnoble import SELECT_TMP_FUTURE_CRS
from djequis.sql.barnesandnoble import EXENCRS
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_session

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
    # set date and time string 
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Open session and create database connection 
    session = get_session(EARL)
    if test:
        print "database connection URL = {0}".format(EARL)

    # Just in case, drop tmp_sess_grace session table 
    sql = DROP_TMP_GRACE
    if test:
        print "drop tmp_sess_grace table"
    if test:
        print sql
    try:
        session.execute(sql)
        if test:
            print "tmp_sess_grace dropped"
    except:
        if test:
            print "no temp table: tmp_sess_grace"

    # Just in case, drop tmp_actv_sess session table 
    sql = DROP_TMP_ACTV_SESS
    if test:
        print "drop tmp_actv_sess table"
    if test:
        print sql
    try:
        session.execute(sql)
        if test:
            print "tmp_actv_sess dropped"
    except:
        if test:
            print "no temp table: tmp_actv_sess"

    # Just in case, drop tmp_UBAL session table 
    sql = DROP_TMP_UBAL
    if test:
        print "drop tmp_UBAL table"
    if test:
        print sql
    try:
        session.execute(sql)
        if test:
            print "tmp_UBAL dropped"
    except:
        if test:
            print "no temp table: tmp_UBAL"

    # Just in case, drop tmp_future_crs session table 
    sql = DROP_TMP_FUTURE_CRS
    if test:
        print "drop tmp_future_crs table"
    if test:
        print sql
    try:
        session.execute(sql)
        if test:
            print "tmp_future_crs dropped"
    except:
        if test:
            print "no temp table: tmp_future_crs"

    # Builds TempTable for pre & post grace periods per term
    sql = TMP_GRACE
    x = session.execute(sql)
    if test:
        print x.context.statement

    # Selecting tmp_sess_grace session table
    sql = SELECT_TMP_SESS_GRACE
    rows = session.execute(sql).fetchall()
    for row in rows:
        if test:
            print row

    # Builds TempTable for Acad_Calendar active terms
    sql = TMP_ACTV_SESS
    x = session.execute(sql)
    if test:
        print x.context.statement

    # Selecting tmp_actv_sess session table
    sql = SELECT_TMP_ACTV_SESS
    rows = session.execute(sql).fetchall()
    for row in rows:
        if test:
            print row

    # Builds TempTable for active UBAL holds
    sql = TMP_UBAL
    x = session.execute(sql)
    if test:
        print x.context.statement

    # Selecting tmp_UBAL session table
    sql = SELECT_TMP_UBAL
    rows = session.execute(sql).fetchall()
    for row in rows:
        if test:
            print row

    # Builds TempTable for active UBAL holds******
    sql = TMP_FUTURE_CRS
    x = session.execute(sql)
    if test:
        print x.context.statement

    # Selecting tmp_UBAL session table*****
    sql = SELECT_TMP_FUTURE_CRS
    rows = session.execute(sql).fetchall()
    for row in rows:
        if test:
            print row

    # set dictionary
    dict = {
        'AR100': STU_ACAD_REC_100,
        'AR200': STU_ACAD_REC_200,
        'exencrs': EXENCRS
        }
    """
    # go to directory on the server
    os.chdir(settings.BARNESNOBLE_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # SFTP connection information
    XTRNL_CONNECTION = {
       'host':settings.BARNESNOBLE_HOST,
       'username':settings.BARNESNOBLE_USER,
       'private_key':settingsBARNESNOBLE_PKEY,
       'private_key_pass':settings.BARNESNOBLE_PASS,
       'cnopts':cnopts
    }
    """
    for key, value in dict.items():
        if test:
            print key
    #######################################################################
    # Dict Value 'STU_ACAD_REC_100' selects active students and sets budget
    # limit for export (books = '100' & $3000.00)

    # Dict Value 'STU_ACAD_REC_200' selects active students and sets budget
    # limit for export (supplies = '200' & $50.00)

    # Dict Value 'EXENCRS' 
    #######################################################################
        sql = (value)
        x = session.execute(sql)
        rows = session.execute(sql).fetchall()
        for row in rows:
            if test:
                print row

        # set directory and filename to be stored
        filename=('{0}{1}_{2}.csv'.format(
            settings.BARNESNOBLE_CSV_OUTPUT,key,datetimestr
        ))
        # set directory and filename to be renamed
        new_filename=('{0}{1}.csv'.format(
            settings.BARNESNOBLE_CSV_OUTPUT,key
        ))

        # create .csv file
        phile=open(filename,"w");
        output=csv.writer(phile)

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

        phile.close()

        # renaming old filename to newfilename
        shutil.copy(filename, new_filename)
        """
        # SFTP the file to Carthage Bookstore
        try:
            with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
                #sftp.chdir("incoming/")
                sftp.put(filename, preserve_mtime=True)
                sftp.close()
            if test:
                print "success: BARNES AND NOBLE UPLOAD"
        except Exception, e:
            if test:
                print e
            else:
                SUBJECT = '[Barnes and Noble SFTP] BARNES AND NOBLE UPLOAD failed'
                BODY = 'Unable to PUT upload to Barnes and Noble server.\n\n{0}'.format(str(e))
                sendmail(
                    settings.BARNESNOBLE_TO_EMAIL,settings.BARNESNOBLE_FROM_EMAIL,
                    SUBJECT, BODY
                )
        """

    # Close session and close database connection 
    session.close()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
