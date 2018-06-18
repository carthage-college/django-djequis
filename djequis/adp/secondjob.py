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
from djzbar.settings import INFORMIX_EARL_SANDBOX
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
# EARL = INFORMIX_EARL_TEST
# elif database == 'sandbox'
EARL = INFORMIX_EARL_SANDBOX
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
engine = get_engine(EARL)



# process_job(999999, "T", "Tenure", "PROV", "Provost" "329000", "English",
#               "639",
#             "Chair, English Department", "03/09/2018", "", "FVW",
#             "FT", "Faculty FT", "Yes", "FVW421457", "Kiesel","Alyson","J")

def fn_process_second_job(carthid, workercatcode, workercatdescr, pcnaggr,
                busunitcode, homedeptcode, homedeptdescr, room, bldg, jobtitledescr,
                positionstart, poseffectend, workcatcode, jobfunctioncode,
                jobfuncdtiondescription, primarypos, supervisorid, rank):

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


        # disassmble pcn code into parts JobType, Div, Dept, Job code

        print(pcnaggr)
        len = pcnaggr.__len__()
        pos1 = pcnaggr.find('-', 0)
        paycode = pcnaggr[:pos1]
        print("Job Type = " + str(paycode))
        pos2 = pcnaggr.find('-', pos1 + 1, len)
        div = pcnaggr[pos1 + 1:pos2]
        print("Div = " + str(div))
        pos3 = pcnaggr.find('-', pos2 + 1, len)
        dept = pcnaggr[pos2 + 1:pos3]
        print("Dept = " + str(dept))
        jobnum = pcnaggr[pos3 + 1:len]
        print("Job number =" + str(jobnum))



        ###############################################################
        # Use PCN Agg to find TPos FROM position rec
        ###############################################################
        v_tpos = fn_validate_field(pcnaggr,"pcn_aggr","tpos_no",
                        "pos_table","char")
        print("v-tpos = " + str(v_tpos))


        if v_tpos == None or len(str(v_tpos)) == 0:
            print("Position not valid")
        else:
            print("Validated t_pos = " + str(v_tpos))

        #     # This insert query works . 5/25/18
        #     q_ins_pos = '''INSERT INTO pos_table(pcn_aggr, pcn_01, pcn_02, pcn_03,
        #               pcn_04, descr, ofc, func_area, supervisor_no,
        #               tenure_track, fte, max_jobs, hrpay, active_date, prev_pos)
        #               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        #     q_ins_pos_args = (pcnaggr,paycode,div,
        #                         func_code,jobnum, jobtitledescr,
        #                         'ofc', func_code, supervisorid[3:9],
        #                         'tenure', 0, 0, paycode,
        #                         datetime.now().strftime("%m/%d/%Y"),'')
        #
        #     # print(q_ins_pos)
        #     # print(q_ins_pos_args)
        #
        #     engine.execute(q_ins_pos, q_ins_pos_args)
        #     # Need to return the tpos_no as it is created in the INSERT
        #     # test_pcn = "EXT-PROV-ENG-CHR"   #use this if not doing live insert
        #     # for test
        #
        #
        #     print("New t_pos needed for = " + pcnaggr)
        #     # This select query works . 5/25/18
        #     q_get_tpos = '''SELECT tpos_no FROM pos_table
        #                WHERE pcn_aggr = '{0}'
        #                '''.format(pcnaggr)
        #     #    if tpos exists return the tpos number to find the job record
        #     sql_tpos = do_sql(q_get_tpos, key=DEBUG, earl=EARL)
        #     row = sql_tpos.fetchone()
        #     tpos_result = row[0]
        #     v_tpos = tpos_result
        #     print("New tpos = " + str(v_tpos))
        #     # print(q_ins_pos)
        # else:
        #     print("Validated t_pos = " + str(v_tpos))
        #     # This  query works . 5/25/18
        #     q_upd_pos = '''UPDATE pos_table SET pcn_aggr = ?, pcn_01 = ?,
        #             pcn_02 = ?, pcn_03 = ?, pcn_04 = ?, descr = ?, ofc = ?,
        #             func_area = ?, supervisor_no = ?, tenure_track = ?,
        #             fte = ?, max_jobs = ?, hrpay = ?, active_date = ?,
        #             inactive_date = '' WHERE tpos_no = ?'''
        #     q_upd_pos_args = (pcnaggr, jobfunctioncode, div,
        #                       func_code, jobnum, jobtitledescr,
        #                       'ofc', func_code, supervisorid[3:9],
        #                       'tenure', 0, 0, paycode,
        #                       datetime.now().strftime("%m/%d/%Y"),
        #                       v_tpos)
        #     # print(q_upd_pos)
            # print(q_upd_pos_args)



        # ##############################################################
        # # validate hrpay, values in this table should not change without
        # # a project request as they affect a number of things
        # ##############################################################
        hrpay_rslt = fn_validate_field(paycode,"hrpay","hrpay",
                            "hrpay_table", "char")
        if hrpay_rslt != '':
            print('Validated HRPay Code = ' + str(hrpay_rslt) + '\n')
        else:
            print('Invalid Payroll Company Code ' + str(paycode) + '\n')
            # logger.info("Invalid Payroll Company Code " + paycode + '\n')
            # raise ValueError("Invalid Payroll Company Code (HRPay) " + paycode + '\n')
        #
        #
        #
        # func_code = fn_validate_field(dept,"func","func",
        #             "func_table", "char")
        # if func_code != '':
        #     print('Validated func_code = ' + dept + '\n')
        # else:
        #     print('Invalid Function Code ' + dept + '\n')
        #     logger.info(
        #         "Invalid Function  Code " + dept + '\n')
        #     raise ValueError(
        #         "Invalid Function  Code (HRPay) " + dept + '\n')
        #
        # print('\n' + '----------------------')
        # print('\n' + pcnaggr)
        #
        #
        # ##############################################################
        # # Need some additional info from existing cx records
        # ##############################################################
        # sql = "SELECT distinct job_rec.job_title, job_rec.hrstat FROM " \
        #       "job_rec Where tpos_no = ?"
        #
        #
        # ##############################################################
        # # validate the position, division, department
        # ##############################################################
        # # print("....Deal with division...")
        # hrdivision = fn_validate_field(div,"hrdiv","hrdiv",
        #                     "hrdiv_table", "char")
        # if hrdivision == None or hrdivision == "":
        #     # This query works 5/25/18
        #     q_ins_div = '''INSERT INTO hrdiv_table(hrdiv, descr, beg_date,
        #                     end_date) VALUES(?,?,?,null)'''
        #     q_ins_div_args = (div, businessunitdescr,
        #                         datetime.now().strftime("%m/%d/%Y"))
        #     print("New HR Division = " + div  + '\n')
        #     # print(q_ins_div + str(q_ins_div_args))
        #     engine.execute(q_ins_div, q_ins_div_args)
        # else:
        #     # This query works 5/25/18
        #     q_upd_div = '''UPDATE hrdiv_table SET descr = ?,
        #                   beg_date = ? WHERE hrdiv = ?'''
        #     q_upd_div_args = (businessunitdescr,
        #                   datetime.now().strftime("%m/%d/%Y"),
        #                   div)
        #     print("Existing HR Division = " + hrdivision + '\n')
        #     # print(q_upd_div + str(q_upd_div_args))
        #     engine.execute(q_upd_div, q_upd_div_args)
        #
        # # print("....Deal with department...")
        # hrdepartment = fn_validate_field(dept,"hrdept","hrdept",
        #                 "hrdept_table", "char")
        # if hrdepartment==None or hrdepartment=="" or len(hrdepartment)==0:
        #     # This query works 5/25/18
        #     q_ins_dept = '''INSERT INTO hrdept_table(hrdept, hrdiv, descr,
        #                         beg_date, end_date) VALUES(?,?,?,?,?)'''
        #     q_ins_dept_args = (dept, div,
        #                        homedeptdescr,
        #                        datetime.now().strftime("%m/%d/%Y"),None)
        #
        #     print("New HR Department = " + dept)
        #     # print(q_ins_dept + str(q_ins_dept_args) +'\n')
        #     engine.execute(q_ins_dept, q_ins_dept_args)
        # else:
        #     # This query works 5/25/18
        #     q_upd_dept = '''UPDATE hrdept_table SET hrdiv = ?, descr = ?,
        #           beg_date = ? WHERE hrdept = ?'''
        #     q_upd_dept_args = (div, homedeptdescr,
        #                        datetime.now().strftime("%m/%d/%Y"), func_code)
        #
        #     # print(q_upd_dept + str(q_upd_dept_args) + '\n')
        #     print("Existing HR Department = " + hrdepartment)
        #     engine.execute(q_upd_dept, q_upd_dept_args)
        #
        #
        #
        #
        #
        # ##############################################################
        # # Determine job rank for second job_rec
        # ##############################################################
        # rank = ''
        # if primaryposition == 'Yes' and poseffectend == '':
        #     rank = 1
        # elif primaryposition == 'No' and poseffectend == '':
        #     rank = 2
        # elif poseffectend != '':
        #     rank = ''
        # print("Rank = " + str(rank) +'\n')
        #
        #
        # # ##############################################################
        # # If job rec exists in job_rec -update, else insert
        # # ##############################################################
        # q_get_job = '''SELECT job_no
        #                 FROM job_rec
        #                 WHERE tpos_no = {0}
        #                 and id = {1}
        #                 and end_date is null
        #                               '''.format(v_tpos,carthid,positionstart)
        # # Something in the formatting of the date is failing...
        # # and beg_date = '{2}'
        #
        # print(q_get_job)
        # sql_job = do_sql(q_get_job, key=DEBUG, earl=EARL)
        # jobrow = sql_job.fetchone()
        # if jobrow is None:
        #     print("Job Number not found in job rec")
        #     #  if no record, no duplicate
        #     #     insert
        #     # NOTE:  NEED TO ADD JOB CLASS CODE into HRCLASS field
        #     # Insert into job rec
        #     # Query works as of 5/29/18
        #     q_ins_job = '''INSERT INTO job_rec
        #       (tpos_no, descr, bjob_no, id, hrpay, supervisor_no,
        #       hrstat, egp_type, hrdiv, hrdept, comp_beg_date,
        #       comp_end_date,
        #       beg_date, end_date, active_ctrct, ctrct_stat, excl_srvc_hrs,
        #       excl_web_time, job_title, title_rank, worker_ctgry, hrclass)
        #       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        #       ?, ?,
        #        ?, ?, ?)'''
        #
        #     q_ins_job_args = (v_tpos, jobtitledescr, 0, carthid,
        #                       paycode, spvrID, jobfunctioncode,
        #                       'R',
        #                       div, func_code, None, None,
        #                       datetime.now().strftime("%m/%d/%Y"), None,
        #                       'N', 'N/A', 'N',
        #                       'N', jobtitledescr, rank, workercatcode,
        #                       jobclass)
        #     print(q_ins_job + str(q_ins_job_args))
        #     print("New Job Record for " + last + ', id = ' + str(carthid))
        #     engine.execute(q_ins_job, q_ins_job_args)
        #
        # else:
        #     # jobrow = sql_job.fetchone()
        #     print('valid job found = ' + str(jobrow[0]))
        #     print('v_tpos = ' + str(v_tpos) )
        #
        #     q_upd_job = '''
        #         UPDATE job_rec SET descr = ?,
        #         id = ?, hrpay = ?, supervisor_no = ?,
        #         hrstat = ?, hrdiv = ?, hrdept = ?,
        #         beg_date = ?, end_date = ?,
        #         job_title = ?,
        #         title_rank = ?, worker_ctgry = ?, hrclass = ?
        #         WHERE job_no = ?'''
        #     q_upd_job_args = (jobtitledescr, carthid, paycode, spvrID,
        #             jobfunctioncode, div, func_code,
        #             datetime.now().strftime("%m/%d/%Y"),
        #             None if poseffectend == '' else poseffectend,
        #             jobtitledescr, rank, workercatcode, jobclass, jobrow[0])
        #     print(q_upd_job)
        #     print(q_upd_job_args)
        #
        #     print("Update Job Record for " + last + ', id = ' + str(carthid))
        #     engine.execute(q_upd_job, q_upd_job_args)
        #
        #

        ##############################################################
        # Faculty Qualifications - This will go into facqual_rec...
        # and qual_table - No longer part of Job Title
        # Probably not in scope as these titles do not affect pay
        ##############################################################

    except Exception as e:
        print(e)

