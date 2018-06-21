import os
import string
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import datetime, timedelta
import codecs
import time
from time import strftime
import argparse
#import uuid
from sqlalchemy import text
import shutil
#import re
import logging
from logging.handlers import SMTPHandler

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

# Imports for additional modules and functions written as part of this project
from djequis.adp.utilities import fn_validate_field, fn_write_log, fn_write_error

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""
# parser = argparse.ArgumentParser(description=desc)
#
# parser.add_argument(
#     "--test",
#     action='store_true',
#     help="Dry run?",
#     dest="test"
# )
# parser.add_argument(
#     "-d", "--database",
#     help="database name.",
#     dest="database"
# )
#
# # set global variable
# global EARL
# # determines which database is being called from the command line
# # if database == 'cars':
# #    EARL = INFORMIX_EARL_PROD
# # elif database == 'train':
# # EARL = INFORMIX_EARL_TEST
# # elif database == 'sandbox'
# EARL = INFORMIX_EARL_SANDBOX
# # else:
#     # this will raise an error when we call get_engine()
#     # below but the argument parser should have taken
#     # care of this scenario and we will never arrive here.
# #    EARL = None
# # establish database connection
# engine = get_engine(EARL)

# write out the .sql file
scr = open("apdtocx_output.sql", "a")

def fn_process_second_job(carthid, workercatcode, pcnaggr, jobtitledescr,
                          positionstart, poseffectend, jobfunctioncode,
                          supervisorid, rank, fullname, EARL):
    engine = get_engine(EARL)

    try:
        ##############################################################
        # Differs from regular job rec routine
        # Most of the information has already been validated since this
        # job is in the same record row as the primary
        # Same supervisor as primary job
        # Sane homedept code for the EMPLOYEE
        # Same business unit code for the EMPLOYEE
        # Same room and building, but probably can ignore since not primary position
        # Same worker category code and description, no validation needed
        # Payroll company code COULD be different, but shouldn't be
        # Job Function Code should be the same
        # Split PCN_Aggr (Home Cost Number) into separate components
        # first I should determine if this is an insert or update - see if
        #   pcn_aggr is in the pos_table
        # see if pcn code returns a position number
        # validate function code in the func_table (Position 2)
        # Place dept number in func_area field in position table
        # Must validate Division, Dept
        # NOT assuming custom field is correct, will notify if no matches
        # use PCN Codes to tie employee to job number
        ##############################################################

        ###############################################################
        # disassmble pcn code into parts JobType, Div, Dept, Job code
        ###############################################################
        print(pcnaggr)
        len = pcnaggr.__len__()
        pos1 = pcnaggr.find('-', 0)
        paycode = pcnaggr[:pos1]
        pos2 = pcnaggr.find('-', pos1 + 1, len)
        div = pcnaggr[pos1 + 1:pos2]
        pos3 = pcnaggr.find('-', pos2 + 1, len)
        dept = pcnaggr[pos2 + 1:pos3]
        jobnum = pcnaggr[pos3 + 1:len]

        # print("Job Type = " + str(paycode))
        # print("Div = " + str(div))
        # print("Dept = " + str(dept))
        # print("Job number =" + str(jobnum))

        spvrID = supervisorid[3:10]

        ###############################################################
        # Use PCN Agg to find TPos FROM position rec
        ###############################################################
        v_tpos = fn_validate_field(pcnaggr,"pcn_aggr","tpos_no",
                        "pos_table","char")
        # print("v-tpos = " + str(v_tpos))

        if v_tpos == 0:
        # if v_tpos == None or len(str(v_tpos)) == 0:
            #print("Position not valid")
            scr.write('Position not valid.\n');
        else:
            #print("Validated t_pos = " + str(v_tpos))
            scr.write('Validated t_pos ' + str(v_tpos) + '\n');

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

        ##############################################################
        # validate hrpay, values in this table should not change without
        # a project request as they affect a number of things
        ##############################################################
        hrpay_rslt = fn_validate_field(paycode,"hrpay","hrpay", "hrpay_table",
                                       "char")
        if hrpay_rslt != '':
            #print('Validated HRPay Code = ' + str(hrpay_rslt) + '\n')
            scr.write('Validated HRPay Code = ' + str(hrpay_rslt) + '\n');
        else:
            print('Invalid Payroll Company Code ' + str(paycode) + '\n')
            fn_write_log('Invalid Payroll Company Code ' + str(paycode) + '\n');
            # logger.info("Invalid Payroll Company Code " + paycode + '\n')
            # raise ValueError("Invalid Payroll Company Code (HRPay) " + paycode + '\n')

        func_code = fn_validate_field(dept,"func","func", "func_table", "char")
        if func_code != '':
            #print('Validated func_code = ' + dept + '\n')
            scr.write('Validated Function Code = ' + dept + '\n');
        else:
            #print('Invalid Function Code ' + dept + '\n')
            fn_write_log('Invalid Function Code = ' + dept + '\n');

        #print('\n' + '----------------------')
        #print('\n' + pcnaggr)
        ##############################################################
        # Need some additional info from existing cx records
        # ADP does not have field for second job title
        ##############################################################
        q_get_title = '''
          SELECT distinct job_rec.job_title  
          FROM job_rec Where tpos_no = {0}'''.format(v_tpos)
        #print(q_get_title)
        sql_title = do_sql(q_get_title, key=DEBUG, earl=EARL)
        titlerow = sql_title.fetchone()
        if titlerow is None:
            # print("Job Title Not found for tpos " + v_tpos)
            fn_write_log('Job Title Not found for tpos ' + v_tpos+ '\n');
        else:
            jr_jobtitle = titlerow[0]

        ##############################################################
        # validate the position, division, department
        ##############################################################
        # print("....Deal with division...")
        hrdivision = fn_validate_field(div,"hrdiv","hrdiv", "hrdiv_table",
                                       "char")

        if hrdivision == None or hrdivision == "":
            #print("HR Div not valid - " + div)
            scr.write('HR Div not valid ' + div + '\n');

        # print("....Deal with department...")
        hrdepartment = fn_validate_field(dept,"hrdept","hrdept", "hrdept_table",
                                         "char")
        #print(hrdepartment)
        if hrdepartment==None or hrdepartment=="":
            #print("HR Dept not valid - " + dept)
            fn_write_log('HR Dept not valid ' + dept + '\n');

        # ##############################################################
        # If job rec exists for employee in job_rec -update, else insert
        # ##############################################################
        q_get_job = '''
          SELECT job_no
          FROM job_rec
          WHERE tpos_no = {0}
          AND id = {1}
          AND end_date IS null
          '''.format(v_tpos,carthid,positionstart)
        #print(q_get_job)
        sql_job = do_sql(q_get_job, key=DEBUG, earl=EARL)
        jobrow = sql_job.fetchone()
        if jobrow is None:
            print("Job Number not found in job rec")
            #  if no record, no duplicate
            #     insert
            q_ins_job = '''
              INSERT INTO job_rec
              (tpos_no, descr, bjob_no, id, hrpay, supervisor_no, hrstat, 
              egp_type, hrdiv, hrdept, comp_beg_date, comp_end_date, beg_date, 
              end_date, active_ctrct, ctrct_stat, excl_srvc_hrs, excl_web_time, 
              job_title, title_rank, worker_ctgry)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?)'''
            q_ins_job_args = (v_tpos, jr_jobtitle, 0, carthid, paycode, spvrID,
                              jobfunctioncode, 'R', div, func_code, None, None,
                              datetime.now().strftime("%m/%d/%Y"), None, 'N',
                              'N/A', 'N', 'N', jobtitledescr, rank,
                              workercatcode)
            print(q_ins_job + str(q_ins_job_args))
            #print("New Job Record for " + fullname + ', id = ' + str(carthid))
            fn_write_log('New Job Record for ' + fullname + ', id = ' + str(carthid) + '\n');
            engine.execute(q_ins_job, q_ins_job_args)
            scr.write(q_ins_job + '\n');
        else:
            # jobrow = sql_job.fetchone()
            #print('valid job found = ' + str(jobrow[0]))
            #print('v_tpos = ' + str(v_tpos) )
            q_upd_job = '''
                UPDATE job_rec SET descr = ?,
                id = ?, hrpay = ?, supervisor_no = ?,
                hrstat = ?, hrdiv = ?, hrdept = ?,
                beg_date = ?, end_date = ?,
                job_title = ?,
                title_rank = ?, worker_ctgry = ?
                WHERE job_no = ?'''
            q_upd_job_args = (jr_jobtitle, carthid, paycode, spvrID,
                              jobfunctioncode, div, func_code,
                              datetime.now().strftime("%m/%d/%Y"),
                              None if poseffectend == '' else poseffectend,
                              jobtitledescr, rank, workercatcode, jobrow[0])
            #print(q_upd_job)
            #print(q_upd_job_args)
            #print("Update Job Record for " + fullname + ', id = ' + str(carthid))
            engine.execute(q_upd_job, q_upd_job_args)
            scr.write(q_upd_job + '\n');
            fn_write_log('Update Job Record for ' + fullname + ', id = ' + str(
                carthid) + '\n');

        ##############################################################
        # Faculty Qualifications - This will go into facqual_rec...
        # and qual_table - No longer part of Job Title
        # Probably not in scope as these titles do not affect pay
        ##############################################################

    except Exception as e:
        fn_write_error(e)
        # print(e)
