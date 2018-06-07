import string
import datetime
import os
import io
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import datetime, timedelta
import time
from time import strftime
import argparse
import uuid
from sqlalchemy import text
import shutil
import re
import logging
from logging.handlers import SMTPHandler
#import adp_ftp
import codecs

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
sys.path.append('/djequis/adp')

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

# from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djtools.fields import TODAY
from djequis.adp.utilities import fn_validate_field

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
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

# set global variable
global EARL
# determines which database is being called from the command line
# if database == 'cars':
#    EARL = INFORMIX_EARL_PROD
# elif database == 'train':
EARL = INFORMIX_EARL_TEST
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
engine = get_engine(EARL)

def fn_process_job(carthid, workercatcode, workercatdescr, businessunitcode,
                businessunitdescr, homedeptcode, homedeptdescr, jobtitlecode,
                jobtitledescr, positionstart, poseffectend, payrollcompcode,
                jobfunctioncode, jobfuncdtiondescription, jobclass,
                jobclassdescr, primaryposition, supervisorid, last, first,
                middle):
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to info
    handler = logging.FileHandler(
        '{0}apdtocx.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # create error file handler and set level to error
    handler = logging.FileHandler(
        '{0}apdtocx_error.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


    try:
        ##############################################################
        # must validate ID of supervisor
        # Split PCN_Aggr (Home Cost Number) into separate components
        # first I should determine if this is an insert or update - see if
        #   pcn_aggr is in the pos_table
        # validate function code in the func_table
        # Place dept number in func_area field in position table
        # Must account for Division, Dept
        # use PCN Codes to tie employee to job number
        # validate a number of fields as needed
        # add GL Func code to func_area in position table
        # if there is a secondary job record, do the same..
        ##############################################################

        spvrID = fn_validate_supervisor(supervisorid[3:10])

        # Construct the pcn code from existing items?
        # func_area = left(homedeptcode,3)
        # hrdept/pcn_03 = homedeptcode[:3]
        # pcn_04 = job title code
        # hrdiv = business unit code
        # pcn_aggr = jobfunctioncode-businessunitcode-homedeptcode-jobtitlecode
        pcnaggr = payrollcompcode + "-" + businessunitcode + "-" \
                      + homedeptcode[:3] + "-" + jobtitlecode

        func_code = fn_validate_field(homedeptcode[:3],"func","func",
                    "func_table", "char")
        if func_code != '':
            print('Validated func_code = ' + homedeptcode[:3] + '\n')
        else:
            print('Invalid Function Code ' + homedeptcode[:3] + '\n')
            logger.info(
                "Invalid Function  Code " + homedeptcode[:3] + '\n')
            raise ValueError(
                "Invalid Function  Code (HRPay) " + homedeptcode[:3] + '\n')

        # pcnaggr = "ADM-VPLI-LIS-INSTS"
        print('\n' + '----------------------')
        print('\n' + pcnaggr)
        print("Supervisor = " + str(spvrID) +'\n')

        ##############################################################
        # validate hrpay, values in this table should not change without
        # a project request as they affect a number of things
        ##############################################################
        hrpay_rslt = fn_validate_field(payrollcompcode,"hrpay","hrpay",
                            "hrpay_table", "char")
        if hrpay_rslt != '':
            print('Validated HRPay Code = ' + str(hrpay_rslt) + '\n')
        else:
            print('Invalid Payroll Company Code ' + str(payrollcompcode) + '\n')
            # logger.info("Invalid Payroll Company Code " + payrollcompcode + '\n')
            # raise ValueError("Invalid Payroll Company Code (HRPay) " + payrollcompcode + '\n')



        ##############################################################
        # New table in Informix - Worker Category
        # Not maintained in CX, so we will have to maintain it with
        # inserts and updates
        ##############################################################
        v_workercatcode = fn_validate_field(workercatcode,"work_cat_code",
                    "work_cat_code","cc_work_cat_table","char")
        if v_workercatcode == None or len(str(v_workercatcode)) == 0:
            q_ins_wc = '''INSERT INTO cc_work_cat_table (work_cat_code,
                      work_cat_descr, active_date) VALUES ({0},'{1}','{2}')
                      '''.format(workercatcode,workercatdescr,
                      datetime.now().strftime("%Y-%m-%d"))
            # print(q_ins_wc)
        else:
            q_upd_wc = '''UPDATE cc_work_cat_table set work_cat_desc = '{1}'
                      WHERE work_cat_code = {0}
                      '''.format(workercatcode, workercatdescr)
            # print(q_upd_wc)

        ###############################################################
        # Use PCN Agg to find TPos FROM position rec
        ###############################################################
        v_tpos = fn_validate_field(pcnaggr,"pcn_aggr","tpos_no",
                        "pos_table","char")
        print("v-tpos = " + str(v_tpos))

        if v_tpos == None or len(str(v_tpos)) == 0:
            # This insert query works . 5/25/18
            q_ins_pos = '''INSERT INTO pos_table(pcn_aggr, pcn_01, pcn_02, pcn_03, 
                      pcn_04, descr, ofc, func_area, supervisor_no, 
                      tenure_track, fte, max_jobs, hrpay, active_date) 
                      VALUES('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}',
                      {8},'{9}',{10},{11},'{12}','{13}')
                     '''.format(pcnaggr,payrollcompcode,businessunitcode,
                                func_code,jobtitlecode, jobtitledescr,
                                'ofc', func_code, supervisorid[3:9],
                                'tenure', 0, 0, payrollcompcode,
                                datetime.now().strftime("%Y-%m-%d"))

            # Need to return the tpos_no as it is created in the INSERT
            test_pcn = "EXT-PROV-ENG-CHR"   #use this if not doing live insert
            # for test

            print("New t_pos needed for = " + pcnaggr)
            # This select query works . 5/25/18
            q_get_tpos = '''SELECT tpos_no FROM pos_table
                       WHERE pcn_aggr = '{0}'
                       '''.format(test_pcn)
            #    if tpos exists return the tpos number to find the job record
            sql_tpos = do_sql(q_get_tpos, key=DEBUG, earl=EARL)
            row = sql_tpos.fetchone()
            tpos_result = row[0]
            v_tpos = tpos_result
            print("New tpos = " + str(v_tpos))
            # print(q_ins_pos)
        else:
            print("Validated t_pos = " + str(v_tpos))
            # This  query works . 5/25/18
            q_upd_pos = '''UPDATE pos_table SET pcn_aggr = '{0}', pcn_01 = '{1}', 
                    pcn_02 = '{2}', pcn_03 = '{3}', pcn_04 = '{4}', 
                    descr = '{5}', ofc = '{6}', func_area = '{7}', 
                    supervisor_no = {8}, tenure_track = '{9}', 
                    fte = {10}, max_jobs = {11}, hrpay = '{12}', 
                    active_date = '{13}', 
                    inactive_date = '' WHERE tpos_no = {14} 
                   '''.format(pcnaggr, jobfunctioncode, businessunitcode,
                              func_code, jobtitlecode, jobtitledescr,
                              'ofc', func_code, supervisorid[3:9],
                              'tenure', 0, 0, payrollcompcode,
                              datetime.now().strftime("%Y-%m-%d"),
                              v_tpos)
            # print(q_upd_pos)

        ##############################################################
        # validate the position, division, department
        ##############################################################
        # print("....Deal with division...")
        hrdivision = fn_validate_field(businessunitcode,"hrdiv","hrdiv",
                            "hrdiv_table", "char")
        if hrdivision == None or hrdivision == "":
            # This query works 5/25/18
            q_ins_div = '''INSERT INTO hrdiv_table(hrdiv, descr, beg_date, 
                            end_date) VALUES('{0}','{1}','{2}',null)
                            '''.format(businessunitcode, businessunitdescr,
                                datetime.now().strftime("%Y-%m-%d"))
            print("New HR Division = " + businessunitcode  + '\n')
            # print(q_ins_div)
        else:
            # This query works 5/25/18
            q_upd_div = '''UPDATE hrdiv_table SET descr = '{0}', 
                          beg_date = '{1}' WHERE hrdiv = '{2}' 
                          '''.format(businessunitdescr,
                          datetime.now().strftime("%Y-%m-%d"),
                          businessunitcode)
            print("Existing HR Division = " + hrdivision + '\n')
            # print(q_upd_div)


        # print("....Deal with department...")
        hrdepartment = fn_validate_field(homedeptcode[:3],"hrdept","hrdept",
                        "hrdept_table", "char")
        if hrdepartment==None or hrdepartment=="" or len(hrdepartment)==0:
            # This query works 5/25/18
            q_ins_dept = '''INSERT INTO hrdept_table(hrdept, hrdiv, descr, 
                                beg_date, end_date) VALUES('{0}','{1}','{2}',
                                '{3}', null)
                                  '''.format(homedeptcode[:3],
                                  businessunitcode, homedeptdescr,
                                  datetime.now().strftime("%Y-%m-%d"))

            print("New HR Department = " + homedeptcode[:3])
            # print(q_ins_dept+'\n')
        else:
             # This query works 5/25/18
             q_upd_dept = '''UPDATE hrdept_table SET hrdiv = '{1}', 
                                       descr = '{2}', beg_date = '{3}' WHERE 
                                       hrdept = '{0}' 
                                                 '''.format(func_code,
                                                            businessunitcode,
                                                            homedeptdescr,
                                                            datetime.now().strftime(
                                                                "%Y-%m-%d"))

        # print(q_upd_dept + '\n')
             print("Existing HR Department = " + hrdepartment)

        ##############################################################
        # validate hrstat,
        ##############################################################
        v_job_function_code = fn_validate_field(jobfunctioncode,"hrstat",
                                "hrstat", "hrstat_table","char")
        if v_job_function_code == None or len(v_job_function_code)==0:
            # print('Code ' + jobfunctioncode + ' returned no hrstat info')
            # Insert into hr_stat
            # This query works 5/25/18
            q_ins_stat = '''INSERT INTO hrstat_table(hrstat, txt, 
                           active_date, inactive_date) VALUES('{0}','{1}','{2}',null)
                           '''.format(jobfunctioncode,
                               jobfuncdtiondescription,
                               datetime.now().strftime("%Y-%m-%d"))
            # print(q_ins_stat)
            print("New Job Function Code = " + jobfunctioncode)
        else:
            hrstat_rslt = row[0]
            valid_hrstat = hrstat_rslt
            print("Existing Job Function Code = " + v_job_function_code)
            # This query works 5/25/18
            q_upd_stat = '''UPDATE hrstat_table SET txt = '{1}' 
                          WHERE hrstat = '{0}'
                        '''.format(v_job_function_code, jobfuncdtiondescription)
            print(q_upd_stat)

        ##############################################################
        # Determine job rank for job_rec
        ##############################################################
        rank = ''
        if primaryposition == 'Yes' and poseffectend == '':
            rank = 1
        elif primaryposition == 'No' and poseffectend == '':
            rank = 2
        elif poseffectend != '':
            rank = ''
        print("Rank = " + str(rank) +'\n')


        # ##############################################################
        # If job rec exists in job_rec -update, else insert
        # ##############################################################
        q_get_job = '''SELECT job_no, tpos_no, id
                        FROM job_rec
                        WHERE tpos_no = {0}
                        and id = {1}
                        and end_date is null
                                      '''.format(v_tpos,carthid,positionstart)
        # Something in the formatting of the date is failing...
        # and beg_date = '{2}'

        print(q_get_job)
        sql_job = do_sql(q_get_job, key=DEBUG, earl=EARL)

        if sql_job != None:
            #  if no record, no duplicate
                #     insert
                print('Code ' + str(v_tpos) + ' returned no job info for '
                       + last + ' id = ' + str(carthid))

            # NOTE:  NEED TO ADD JOB CLASS CODE into HRCLASS field
                # Insert into job rec
                # Query works as of 5/29/18
                q_ins_job = ''' INSERT INTO job_rec
                (tpos_no, descr, bjob_no, id, hrpay, supervisor_no,
                 hrstat, egp_type, hrdiv, hrdept, comp_beg_date, comp_end_date,
                 beg_date, end_date, active_ctrct, ctrct_stat, excl_srvc_hrs,
                 excl_web_time, job_title, title_rank, hrclass)
                 VALUES ({0}, '{1}', 0, {2}, '{3}', {4}, '{5}', '{6}', '{7}', 
                 "N/A", null, null, '{8}', null, "N", "N/A", "N", "N", '{9}', 
                 {10},'{11}','{12}'
                                     '''.format(v_tpos, jobtitledescr, carthid,
                                        payrollcompcode, spvrID,
                                        jobfunctioncode, businessunitcode,
                                        func_code, datetime.now().strftime("%Y-%m-%d"),
                                        jobtitledescr, rank, workercatcode,
                                        jobclass)
                # print(q_ins_job)
                print("New Job Record for " + last + ', id = ' + str(carthid))
        else:
            row = sql_job.fetchone()
            job_rslt = row
            valid_job = job_rslt
            print('valid job found')
            q_upd_job = ''' 
                UPDATE job_rec SET descr = '{1}', 
                bjob_no = 0, id = {2}, hrpay = '{3}', supervisor_no = {4},
                hrstat = '{5}', egp_type = "", hrdiv '{6}', hrdept = '{7}', 
                comp_beg_date = null, comp_end_date = null, beg_date = {8}, 
                end_date = null, active_ctrct = "", ctrct_stat = "",  
                excl_srvc_hrs = 0, excl_web_time = "", job_title = '{1}', 
                title_rank = "", worker_ctgry = '{9}', hrclass = '{10}' 
                WHERE job_no = {0}) '''.format(valid_job, jobtitledescr,
                    carthid, payrollcompcode, spvrID, jobfunctioncode,
                    businessunitcode, func_code,
                    datetime.now().strftime("%Y-%m-%d"), jobtitledescr,
                    rank, workercatcode, jobclass)
            print(q_upd_job)
            print("Update Job Record for " + last + ', id = ' + str(carthid))


        ##############################################################
        # TENURE - This will go into HREMP_REC...
        ##############################################################

        if workercatcode == "T":  #tenure
            is_tenured = "Y"
            is_tenure_track = "N"
        elif workercatcode == "TE":
            is_tenured = "N"
            is_tenure_track = "Y"
        else:
            is_tenured = "N"
            is_tenure_track = "N"

        # Same as all others, first have to avoid duplicate by finding out
        # if a record already exists
        q_get_emp_rec = '''SELECT id, home_tpos_no
                           FROM hremp_rec
                           WHERE id = {0}
                           '''.format(carthid)
        #print(q_get_emp_rec)
        sql_emp = do_sql(q_get_emp_rec, key=DEBUG, earl=EARL)
        row = sql_emp.fetchone()

        if row == None:
            print("No Emp record")
            # This query works  5/25/18
            sql_emp_insert = '''INSERT into hremp_rec (id, home_tpos_no, 
                ss_first, ss_middle, ss_last, ss_suffix, tenure, tenure_date, 
                is_tenured, is_tenure_track)
                VALUES({0},{1}, 
                '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', 
                  '{8}','{9}')
                    '''.format(carthid, v_tpos, first,middle,last,"","","",
                        is_tenured,is_tenure_track)
            # print(sql_emp_insert)
            print("Insert into hremp_rec")
        else:
            print('Found Emp Rec')
            emp_rslt = row
            # print(emp_rslt)
            # this query words - 05/25/2018
            sql_emp_upd = '''UPDATE hremp_rec SET home_tpos_no = {1}, 
            ss_first = '{2}', ss_middle = '{3}', ss_last = '{4}', 
            ss_suffix = '{5}', tenure = '{6}', tenure_date = '{7}',
            is_tenured = '{8}', is_tenure_track = '{9}'
            WHERE id = {0}
            '''.format(carthid, v_tpos, first, middle, last, "", "", "",
                 is_tenured,is_tenure_track)
            # print(sql_emp_upd)
            print("Update HREMP_REC, ")


        ##############################################################
        # To do....
        # Job Class Code, HRClass field in Job Rec
        # Need to add definitions as needed in hrclass_table
        ##############################################################
        # If job Class Code != ""
        #    update
        # elif
        #    insert jobclass, jobclassdescr

        ##############################################################
        # Faculty Qualifications - This will go into facqual_rec...
        # and qual_table - No longer part of Job Title
        # Probably not in scope as these titles do not affect pay
        ##############################################################

    except Exception as e:
        print(e)

##########################################################
# Functions
##########################################################
def fn_validate_supervisor(id):
    q_val_super = '''SELECT hrstat FROM job_rec WHERE id = {0}
                                           '''.format(id)
    #print(q_val_super)
    sql_val_super = do_sql(q_val_super, key=DEBUG, earl=EARL)
    row = sql_val_super.fetchone()

    if row == None:
        # Not found
        return(0)
    else:
        # Not Eligible
        if row[0].strip() == 'VEND':
            return(0)
        elif row[0].strip() == 'OTH':
            return(0)
        elif row[0].strip() == 'LV':
            return(0)
        elif row[0].strip() == 'SA':
            return(0)
        elif row[0].strip() == 'STU':
            return(0)
        elif row[0].strip() == 'PDG':
            return(0)
        elif row[0].strip() == 'STD':
            return(0)
        # Valid as Supervisor
        else:
            return(id)




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

    if database != 'cars' and database != 'train':
        print "database must be: 'cars' or 'train'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())
