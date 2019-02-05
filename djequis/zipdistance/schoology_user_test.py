import os
import string
import sys
import csv
import datetime
import codecs
import argparse
from sqlalchemy import text
import shutil

# import logging
# from logging.handlers import SMTPHandler
# from djtools.utils.logging import seperator

from django.conf import settings
from django.core.urlresolvers import reverse
# import requests
# import json
from math import sin, cos, sqrt, atan2, radians

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Update Zip table with Latitude, Longitude, Distance from Carthage
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
parser.add_argument(
    "-d", "--database",
    help="database name.",
    dest="database"
)
def main():
    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        # if database == 'cars':
        #     EARL = INFORMIX_EARL_PROD
        if database == 'train':
            #python zip_distance.py - -database = train - -test
            EARL = INFORMIX_EARL_TEST
        elif database == 'sandbox':
            #python zip_distance.py - -database = sandbox - -test
            EARL = INFORMIX_EARL_SANDBOX
        else:
            # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)


        ##############################################################
        # This is a test of an idea to set roles in Schoology separate from
        # the Jenzupload script.  
        # For Schoology users, just get all students and staff
        # Then call a function to query job rec and populate values
        #   for role and job title
        ##############################################################
        q_user = '''
          select distinct
            id_rec.firstname, nvl(addree_rec.alt_name,'') prefname, 
            id_rec.middlename, id_rec.lastname,
            id_rec.title name_prefix, trim(jenzprs_rec.host_username) username,
            TRIM(NVL(jenzprs_rec.e_mail,'')) EMAIL,
            to_number(jenzprs_rec.host_id) UniqueID,
            'Carthage College' school,
            jenzprs_rec.host_id schoology_id,
            '' pwd, '' gender, '' GradYr, '' additional_schools
        from jenzprs_rec
            left join jenzcst_rec
            on jenzprs_rec.host_id = jenzcst_rec.host_id
            and jenzcst_rec.status_code in ('FAC', 'STF', 'STU', 'ADM')
            join id_rec on id_rec.id =  jenzprs_rec.host_id
            left join prog_enr_rec TLE
            on TLE.id = jenzprs_rec.host_id
            and TLE.acst= 'GOOD'
            and TLE.tle = 'Y'
            left join addree_rec on addree_rec.prim_id = jenzprs_rec.host_id and addree_rec.style = 'N'

        WHERE jenzprs_rec.host_id in  
          (
            select to_number(host_id) as UID
            from jenzcrp_rec
            UNION  All
            select cx_id as UID
            from provsndtl_rec
            where subsys = 'MSTR'
            and action = 'Active'
            and roles not in ('Contractor')
        )

      
           
        group by id_rec.lastname, id_rec.firstname, prefname, id_rec.middlename,
            name_prefix, username,  email,
            UniqueID,   schoology_id'''.format()

        # (491198, 1522811, 1261378, 1380204)

        # (
        #     select to_number(host_id) as UID
        # from jenzcrp_rec
        #     UNION
        # All
        # select
        # cx_id as UID
        # from provsndtl_rec
        #     where
        # subsys = 'MSTR'
        #          and action = 'Active'
        #                       and roles not in ('Contractor')
        # )



        r_user = do_sql(q_user, key=DEBUG, earl=EARL)

        header = "firstname,preferred_first_name,middlename,lastname," \
                 "name_prefix,username,email,uniqueid,role,school," \
                 "schoology_id,position,pwd,gender,gradyr," \
                 "additional_schools" + "\n"
        # print(header)
        with open('user.csv', 'wb') as f:
            f.write(header)
        # print(row[1])


        try:
            for row in r_user:
                if row[9] != '':
                    fname = (row[0])
                    # prefname = row[1].replace(",", " ")
                    prefname = form_str(row[1])
                    midname = form_str(row[2])
                    lname = row[3]
                    prefix = row[4]
                    username = row[5]
                    email = row[6]
                    uniquid = row[9]
                    school = row[8]
                    schlgyid = row[9]
                    pwd = row[10]
                    gender = row[11]
                    gradyr = row[12]
                    addschl = row[13]
                    values = build_job_title(row[9])
                    position = values[0]
                    role = values[1]
                    # if position != 'None':
                    #     role = 'FAC'
                    # else:
                    #     role = 'STU'
                    #     position = ''

                    sline = str(fname) + ',' + prefname + ',' + midname + ',' + \
                         str(lname) + ',' + prefix + ',' + username + ',' + email + \
                         ',' + str(uniquid) + ',' + role + ',' + school + ',' +\
                         str(schlgyid) + ',' + str(position) + ',' + pwd + ',' +\
                         gender + ',' + gradyr + ',' + addschl + '\n'
                        # print(sline)

                    # csvWriter = csv.writer(open('user.csv', 'wb'), delimiter=',',
                    #                     quoting=csv.QUOTE_MINIMAL,
                    #                     escapechar='\\')

                    with open('user.csv', 'ab') as f:
                    #     csvWriter = csv.writer(f)
                    # csvWriter.writerow([sline])
                        f.write(sline)
                else:
                    print("q")
        except Exception as e:
            print("Error in main " + e.message + " " + str(row[9]))

    except Exception as e:
        # fn_write_error("Error in test, Error = " + e.message)
        print(e.message)

##########################################################
# Functions
##########################################################
def build_job_title(id):
    try:
        # print(id)
        title = ''


        title_sql = ''' select jr.beg_date, jr.job_no, 
            NVL(TRIM(jr.job_title),''),
            replace (trim(NVL(jr.title_rank,'')), '' ,'9') rank,
            NVL(TRIM(jr.descr),'') descr, NVL(TRIM(TLE.tle),'') TLE,
            CASE WHEN jr.hrpay NOT IN ('VEN', 'DPW', 'BIW', 'FV2', 'SUM', 'GRD')
	    	OR TLE.tle = 'Y' 
		    THEN 'FAC' ELSE 'STU' END AS ROLE,
            NVL(TRIM(jr.hrpay),'') HRPAY
            from job_rec jr  
            left join prog_enr_rec TLE
			on TLE.id = jr.id and TLE.acst= 'GOOD' and TLE.tle = 'Y' 
            where (jr.end_date is null or jr.end_date > CURRENT) 
            and jr.id = {0}
            order by rank asc, beg_date, job_no
            '''.format(id)

        # print(title_sql)
        sql_get_title = do_sql(title_sql, key=DEBUG, earl=EARL)
        exst_row = sql_get_title.fetchall()
        # print(exst_row)
        if exst_row is None:
            # print("No Existing primary jobs")
            return ['None', 'STU']
        elif len(exst_row) == 0:
            # print("No Existing primary jobs")
            return ['None','STU']
        else:
            c = 0
            for row in exst_row:
                # print (len(row[4]))
                # print("count = " + str(c))
                # Add ; only if second record, constructed title is not empty
                # and current record is not empty
                # print("next row = " + str(row[4]))
                if c > 0 and ((len(title) > 0 and row[2] != '') or (len(row[4]) > 0 and row[4] != '')):
                    title = title + "; "
                # print(title)
                if len(row[2]) > 0:
                    title = title + (row[2])
                elif len(row[2]) == 0:
                    title = title + (row[4])
                c = c + 1
            title = '"' + title + '"'
            role = row[6]

            print(title.format())
            return [title, role]

        # if len(title) == 0:
        #     return ''
        #     print('No Title')
        # else:

    except Exception as e:
        print("Error in function " + e.message + ' ' + str(id))
        return ['None','STU']

    # fn_write_error("Error in schoology_user_test.py build_job_title. ID = "
    #         + id + " Err = " + e.message)


def form_str(name_element):
    if len(name_element) > 0:
        return '"' + name_element + '"'
    else:
        return ''


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test
    database = args.database

    if not database:
        print "mandatory option missing: database name\n"
        parser.print_help()
        exit(-1)
    else:
        database = database.lower()

    if database != 'cars' and database != 'train' and database != \
            'sandbox':
        print "database must be: 'cars' or 'train' or 'sandbox'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())

