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
from djequis.adp.utilities import fn_validate_field, fn_write_log

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""

# write out the .sql file
scr = open("apdtocx_output.sql", "a")


#############################################
# Begin Processing
#############################################
def fn_process_job(carthid, workercatcode, workercatdescr, businessunitcode,
                businessunitdescr, homedeptcode, homedeptdescr, jobtitlecode,
                jobtitledescr, positioneffective, poseffectend, payrollcompcode,
                jobfunctioncode, jobfuncdtiondescription, jobclass,
                jobclassdescr, primaryposition, supervisorid, last, first,
                middle,EARL):
    engine = get_engine(EARL)

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

        spvrID = fn_validate_supervisor(supervisorid[3:10], EARL)

        # Construct the pcn code from existing items?
        # func_area = left(homedeptcode,3)
        # hrdept/pcn_03 = homedeptcode[:3]
        # pcn_04 = job title code
        # hrdiv = business unit code
        # pcn_aggr = jobfunctioncode-businessunitcode-homedeptcode-jobtitlecode
        pcnaggr = payrollcompcode + "-" + businessunitcode + "-" \
                      + homedeptcode[:3] + "-" + jobtitlecode

        func_code = fn_validate_field(homedeptcode[:3],"func","func",
                    "func_table", "char", EARL)
        if func_code != '':
            print('Validated func_code = ' + homedeptcode[:3] + '\n')
        else:
            print('Invalid Function Code ' + homedeptcode[:3] + '\n')

            fn_write_log("Invalid Function  Code " + homedeptcode[:3] + '\n')
            scr.write('Invalid Function Code ' + homedeptcode[:3] + '\n');
            # raise ValueError(
            #     "Invalid Function  Code (HRPay) " + homedeptcode[:3] + '\n')

        #print('\n' + '----------------------')
        #print('\n' + pcnaggr)
        #print("Supervisor = " + str(spvrID) +'\n')

        ##############################################################
        # validate hrpay, values in this table should not change without
        # a project request as they affect a number of things
        ##############################################################
        hrpay_rslt = fn_validate_field(payrollcompcode,"hrpay","hrpay",
                            "hrpay_table", "char", EARL)
        if hrpay_rslt != '':
            #print('Validated HRPay Code = ' + str(hrpay_rslt) + '\n')
            scr.write('Valid HRPay Code ' + str(hrpay_rslt) + '\n');
        else:
            #print('Invalid Payroll Company Code ' + str(payrollcompcode) + '\n')
            scr.write('Invalid Payroll Company Code '+ str(payrollcompcode) +'\n');
            fn_write_log("Invalid Payroll Company Code " + str(payrollcompcode) + '\n')

        ##############################################################
        # New table in Informix - Worker Category
        # Not maintained in CX, so we will have to maintain it with
        # inserts and updates
        #############################################################
        print("Worker Cat Code")
        v_workercatcode = fn_validate_field(workercatcode,"work_cat_code",
                    "work_cat_code","cc_work_cat_table","char", EARL)
        if v_workercatcode == None or len(str(v_workercatcode)) == 0:
            q_ins_wc = '''
              INSERT INTO cc_work_cat_table (work_cat_code, work_cat_descr,
                active_date)
              VALUES (?,?,?)'''
            q_ins_wc_args = (workercatcode,workercatdescr,
                             datetime.now().strftime("%m/%d/%Y"))
              # print(q_ins_wc)
             # print(q_ins_wc_args)
            engine.execute(q_ins_wc, q_ins_wc_args)
            scr.write(q_ins_wc + '\n');
        else:
            q_upd_wc = '''
              UPDATE cc_work_cat_table set work_cat_descr = ?
              WHERE work_cat_code = ?'''

            q_upd_wc_args = (workercatdescr, workercatcode)
            # print(q_upd_wc)
            # print(q_upd_wc_args)
            engine.execute(q_upd_wc, q_upd_wc_args)
            scr.write(q_upd_wc + '\n');

            ##############################################################
            # To do....
            # Job Class Code, HRClass field in Job Rec
            # Need to add definitions as needed in hrclass_table
            ##############################################################
            # jobclass = 'GA'
            # jobclassdescr = 'Graduate Assistant'
            print("Job Class Code")
            if jobclass != "":
                print(jobclass)
                print(jobclassdescr)
                # Find out if class is in the hrclass table
                q_hrclass = '''
                  SELECT * 
                  FROM hrclass_table 
                  WHERE hrclass = "{0}"
                  AND inactive_date is null'''.format(jobclass)

                jclass = do_sql(q_hrclass, key=DEBUG, earl=EARL)
                row = jclass.fetchone()

                if row is None:
                    q_hrclass_ins = '''
                      INSERT INTO hrclass_table
                      (hrclass, txt, active_date, inactive_date)
                      VALUES(?, ?, ?, ?)'''
                    q_hrclass_ins_args = (jobclass, jobclassdescr,
                                          datetime.now().strftime("%m/%d/%Y"),
                                          None)
                    engine.execute(q_hrclass_ins, q_hrclass_ins_args)
                    scr.write(q_hrclass_ins + '\n');
                else:
                    print(row[1])
                    if row[1] != jobclassdescr:
                        q_hrclass_upd = '''
                          UPDATE hrclass_table
                          SET txt = ?
                          WHERE hrclass = ?'''
                        q_hrclass_upd_args = (jobclassdescr, jobclass)

                        engine.execute(q_hrclass_upd, q_hrclass_upd_args)
                        scr.write(q_hrclass_upd + '\n');
                    else:
                        #print("No change in HRClass Description")
                        scr.write('There were no change in HRClass description.\n');
                # If not, insert
                # Else do nothing
            else:
                print("No Job Class")
        ###############################################################
        # Use PCN Agg to find TPos FROM position rec
        ###############################################################
        print("Find Tpos")
        v_tpos = fn_validate_field(pcnaggr,"pcn_aggr","tpos_no",
                        "pos_table","char", EARL)
        print("v-tpos = " + str(v_tpos))

        if v_tpos == None or len(str(v_tpos)) == 0:
            q_ins_pos = '''
              INSERT INTO pos_table(pcn_aggr, pcn_01, pcn_02, pcn_03, pcn_04, 
                descr, ofc, func_area, supervisor_no, tenure_track, fte, 
                max_jobs, hrpay, active_date, prev_pos) 
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            q_ins_pos_args = (pcnaggr,payrollcompcode,businessunitcode,
                                func_code,jobtitlecode, jobtitledescr,
                                'OFC', func_code, supervisorid[3:9],
                                'TENURE', 0, 0, payrollcompcode,
                                datetime.now().strftime("%m/%d/%Y"),'')
            engine.execute(q_ins_pos, q_ins_pos_args)
            scr.write(q_ins_pos + '\n');
            # Need to return the tpos_no as it is created in the INSERT
            # test_pcn = "EXT-PROV-ENG-CHR"   #use this if not doing live insert
            # for test
            #print("New t_pos needed for = " + pcnaggr)
            # This select query works . 5/25/18
            q_get_tpos = '''
              SELECT tpos_no 
              FROM pos_table
              WHERE pcn_aggr = '{0}'
              '''.format(pcnaggr)
            # if tpos exists return the tpos number to find the job record
            sql_tpos = do_sql(q_get_tpos, key=DEBUG, earl=EARL)
            row = sql_tpos.fetchone()
            tpos_result = row[0]
            v_tpos = tpos_result
            print("New tpos = " + str(v_tpos))
            # print(q_ins_pos)
        else:
            #print("Validated t_pos = " + str(v_tpos))
            q_upd_pos = '''
              UPDATE pos_table SET pcn_aggr = ?, pcn_01 = ?, pcn_02 = ?, 
                pcn_03 = ?, pcn_04 = ?, descr = ?, ofc = ?, func_area = ?, 
                supervisor_no = ?, tenure_track = ?, fte = ?, max_jobs = ?, 
                hrpay = ?, active_date = ?, inactive_date = ? 
              WHERE tpos_no = ?'''
            q_upd_pos_args = (pcnaggr, jobfunctioncode, businessunitcode,
                              func_code, jobtitlecode, jobtitledescr,
                              'OFC', func_code, supervisorid[3:9],
                              'TENURE', 0, 0, payrollcompcode,
                              datetime.now().strftime("%m/%d/%Y"), None,
                              v_tpos)
            # print(q_upd_pos)
            # print(q_upd_pos_args)
            engine.execute(q_upd_pos, q_upd_pos_args)
            scr.write(q_upd_pos + '\n');

        ##############################################################
        # validate the position, division, department
        ##############################################################
        hrdivision = fn_validate_field(businessunitcode,"hrdiv","hrdiv",
                            "hrdiv_table", "char", EARL)
        if hrdivision == None or hrdivision == "":
            q_ins_div = '''
              INSERT INTO hrdiv_table(hrdiv, descr, beg_date, end_date) 
              VALUES(?, ?, ?, null)'''
            q_ins_div_args = (businessunitcode, businessunitdescr,
                                datetime.now().strftime("%m/%d/%Y"))
            # print("New HR Division = " + businessunitcode  + '\n')
            # print(q_ins_div + str(q_ins_div_args))
            engine.execute(q_ins_div, q_ins_div_args)
            scr.write(q_ins_div + '\n');
        else:
            # This query works 5/25/18
            q_upd_div = '''
                UPDATE hrdiv_table SET descr = ?, 
                          beg_date = ?
                WHERE hrdiv = ?'''
            q_upd_div_args = (businessunitdescr,
                          datetime.now().strftime("%m/%d/%Y"),
                          businessunitcode)
            print("Existing HR Division = " + hrdivision + '\n')
            # print(q_upd_div + str(q_upd_div_args))
            engine.execute(q_upd_div, q_upd_div_args)
            scr.write(q_upd_div + '\n');

        hrdepartment = fn_validate_field(homedeptcode[:3],"hrdept","hrdept",
                        "hrdept_table", "char", EARL)
        if hrdepartment==None or hrdepartment=="" or len(hrdepartment)==0:
            # This query works 5/25/18
            q_ins_dept = '''
              INSERT INTO hrdept_table(hrdept, hrdiv, descr, 
                                beg_date, end_date) 
              VALUES(?, ?, ?, ?, ?)'''
            q_ins_dept_args = (homedeptcode[:3], businessunitcode,
                               homedeptdescr,
                               datetime.now().strftime("%m/%d/%Y"),None)
            engine.execute(q_ins_dept, q_ins_dept_args)
            scr.write(q_ins_dept + '\n');
        else:
            q_upd_dept = '''
              UPDATE hrdept_table SET hrdiv = ?, descr = ?, 
                  beg_date = ? 
              WHERE hrdept = ?'''
            q_upd_dept_args = (businessunitcode, homedeptdescr,
                               datetime.now().strftime("%m/%d/%Y"), func_code)
            engine.execute(q_upd_dept, q_upd_dept_args)
            scr.write(q_upd_dept + '\n');
        ##############################################################
        # validate hrstat,
        # Per Meeting 6/22/18, Job Function Code redundant and unreliable
        # Skip this - Worker Category Code will suffice
        ##############################################################
        # v_job_function_code = fn_validate_field(jobfunctioncode,"hrstat",
        #                         "hrstat", "hrstat_table","char", EARL)
        # if v_job_function_code == None or len(v_job_function_code)==0:
        #     # Insert into hr_stat
        #     q_ins_stat = '''
        #       INSERT INTO hrstat_table(hrstat, txt, active_date, inactive_date)
        #       VALUES(?, ?, ?, null)'''
        #     q_ins_stat_args = (jobfunctioncode, jobfuncdtiondescription,
        #                        datetime.now().strftime("%m/%d/%Y"))
        #     engine.execute(q_ins_stat, q_ins_stat_args)
        #     scr.write(q_ins_stat + '\n');
        # else:
        #     # hrstat_rslt = row[0]
        #     # valid_hrstat = hrstat_rslt
        #     print("Existing Job Function Code = " + v_job_function_code)
        #     q_upd_stat = '''
        #       UPDATE hrstat_table SET txt = ?
        #       WHERE hrstat = ?'''
        #     q_upd_stat_args = (jobfuncdtiondescription, v_job_function_code)
        #     engine.execute(q_upd_stat, q_upd_stat_args)
        #     scr.write(q_upd_stat + '\n');
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
        print("Do Job Rec")
        q_get_job = '''
          SELECT job_no
          FROM job_rec
          WHERE tpos_no = {0}
          AND id = {1}
          AND end_date IS null
        '''.format(v_tpos,carthid,positioneffective)
        # Something in the formatting of the date is failing...
        # and beg_date = '{2}'
        # print(q_get_job)
        sql_job = do_sql(q_get_job, key=DEBUG, earl=EARL)
        jobrow = sql_job.fetchone()
        if jobrow is None:
            #print("Job Number not found in job rec")
            scr.write('Job Number not found in job rec\n');

            #  if no record, no duplicate
            #     insert
            # NOTE:  NEED TO ADD JOB CLASS CODE into HRCLASS field
            # Insert into job rec
            # Query works as of 5/29/18
            q_ins_job = '''
              INSERT INTO job_rec
              (tpos_no, descr, bjob_no, id, hrpay, supervisor_no, hrstat, 
              egp_type, hrdiv, hrdept, comp_beg_date, comp_end_date, beg_date, 
              end_date, active_ctrct, ctrct_stat, excl_srvc_hrs, excl_web_time, 
              job_title, title_rank, worker_ctgry, hrclass)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?, ?)'''
            q_ins_job_args = (v_tpos, jobtitledescr, 0, carthid,
                              payrollcompcode, spvrID, '',
                              'R', businessunitcode, func_code, None, None,
                              positioneffective, None, 'N', 'N/A', 'N', 'N',
                              jobtitledescr, rank, workercatcode, jobclass)
            #print(q_ins_job + str(q_ins_job_args))
            #print("New Job Record for " + last + ', id = ' + str(carthid))
            engine.execute(q_ins_job, q_ins_job_args)
            scr.write(q_ins_job + '\n');
            scr.write(
                'New Job Record for " + last + ', id = ' + str(carthid)' + '\n');

        else:
            # jobrow = sql_job.fetchone()
            #print('valid job found = ' + str(jobrow[0]))
            scr.write('Valid Job Found '  +  str(jobrow[0]) + '\n');
            #print('v_tpos = ' + str(v_tpos) )

            q_upd_job = ''' 
                UPDATE job_rec SET descr = ?, id = ?, hrpay = ?, 
                supervisor_no = ?, hrstat = ?, hrdiv = ?, hrdept = ?, 
                beg_date = ?, end_date = ?, job_title = ?, title_rank = ?, 
                worker_ctgry = ?, hrclass = ?
                WHERE job_no = ?'''
            q_upd_job_args = (jobtitledescr, carthid, payrollcompcode, spvrID,
                    '', businessunitcode, func_code, positioneffective,
                    None if poseffectend == '' else poseffectend,
                    jobtitledescr, rank, workercatcode, jobclass, jobrow[0])
            #print(q_upd_job)
            #print(q_upd_job_args)
            print("Update Job Record for " + last + ', id = ' + str(carthid))
            engine.execute(q_upd_job, q_upd_job_args)
            scr.write(q_upd_job + '\n');
            scr.write('Update Job Record for ' + last + ', id = ' + str(carthid) + '\n');


        ##############################################################
        # Question -  on first run, will we need to end date existing jobs that
        # are NOT listed in ADP?   How to determine which those are if there
        # is no match...Figure out in testing
        # May be able to query cc_adp_rec and compare that to the job_rec
        # table to find jobs NOT listed in ADP but still active in CX
        # Not certain we can end date them without further evaluation
        ##############################################################


        ##############################################################
        # TENURE - This will go into HREMP_REC...
        ##############################################################
        print("Tenure")
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
        q_get_emp_rec = '''
          SELECT id, home_tpos_no
          FROM hremp_rec
          WHERE id = {0}
                           '''.format(carthid)
        #print(q_get_emp_rec)
        sql_emp = do_sql(q_get_emp_rec, key=DEBUG, earl=EARL)
        row = sql_emp.fetchone()

        if row == None:
            #print("No Emp record")
            scr.write('No Employee record found in hremp_rec. \n');
            # This query works  5/25/18
            q_emp_insert = '''
              INSERT into hremp_rec (id, home_tpos_no, ss_first, ss_middle, 
              ss_last, ss_suffix, tenure, tenure_date, is_tenured, 
              is_tenure_track)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ? )'''
            q_emp_ins_args = (carthid, v_tpos, first,middle,last,"","","",
                        is_tenured,is_tenure_track)
            #print(q_emp_insert)
            #print(q_emp_ins_args)
            #print("Insert into hremp_rec")
            engine.execute(q_emp_insert, q_emp_ins_args)
            scr.write(q_emp_insert + '\n');
        else:
            #print('Found Emp Rec')
            scr.write('Found Employee a record in hremp_rec. \n');
            emp_rslt = row
            # print(emp_rslt)
            # this query words - 05/25/2018
            q_emp_upd = '''
              UPDATE hremp_rec SET home_tpos_no = ?, ss_first = ?, 
              ss_middle = ?, ss_last = ?, ss_suffix = ?, tenure = ?, 
              tenure_date = ?, is_tenured = ?, is_tenure_track = ?
              WHERE id = ?'''
            q_emp_upd_args = (v_tpos, first, middle, last, "", "", "",
                 is_tenured,is_tenure_track, carthid)
            #print(q_emp_upd)
            #print(q_emp_upd_args)
            #print("Update HREMP_REC")
            engine.execute(q_emp_upd, q_emp_upd_args)
            scr.write(q_emp_upd + '\n');

        ##############################################################
        # Faculty Qualifications - This will go into facqual_rec...
        # and qual_table - No longer part of Job Title
        # Probably not in scope as these titles do not affect pay
        ##############################################################

        return(1)
    except Exception as e:
        print(e)
        return(0)
##########################################################
# Functions
##########################################################
def fn_validate_supervisor(id, EARL):
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

