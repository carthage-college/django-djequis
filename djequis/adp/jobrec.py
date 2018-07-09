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
# import logging
# from logging.handlers import SMTPHandler


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
from djequis.adp.utilities import fn_validate_field, fn_write_log, \
    fn_write_error, fn_needs_upate

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
                jobtitledescr, positioneffective, terminationdate, payrollcompcode,
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

        # There are records with no job number.   Nothing to validate against.
        # If Jobtitle_code is empty, end the process with an invalid data message

        print("Job Title Code = " + jobtitlecode + ", " + jobtitledescr
              + ", " + terminationdate + "------------------")
        if jobtitlecode is None:
            print("Missing Job Title Code for " + last + "," + first + " ID = "  + carthid)
            raise ValueError("Missing Job Title Code for " + last + "," + first + " ID = "  + carthid)
        elif jobtitlecode == '':
            print("Missing Job Title Code for " + last + "," + first + " ID = "  + carthid)
            raise ValueError("Missing Job Title Code for " + last + "," + first + " ID = "  + carthid)

        # There is a supervisor flag in ADP.   But it may not be valid to use
        # for validation at this point.  Just note.
        spvrID = fn_validate_supervisor(supervisorid[3:10], EARL)

        # Construct the pcn code from existing items?
        # func_area = left(homedeptcode,3)
        # hrdept/pcn_03 = homedeptcode[:3]
        # pcn_04 = job title code
        # hrdiv = business unit code
        # pcn_aggr = jobfunctioncode-businessunitcode-homedeptcode-jobtitlecode
        pcnaggr = payrollcompcode + "-" + businessunitcode[:4] + "-" \
                      + homedeptcode[:3] + "-" + jobtitlecode

        print(pcnaggr)

        func_code = fn_validate_field(homedeptcode[:3],"func","func",
                    "func_table", "char", EARL)
        if func_code != '':
            scr.write("Valid func_code")
            # print('Validated func_code = ' + homedeptcode[:3] + '\n')
        else:
            print('Invalid Function Code ' + homedeptcode[:3] + '\n')

            fn_write_error("Error in jobrec.py - Invalid Function Code " +
                           homedeptcode[:3] + '\n')
            scr.write('Error in jobrec.py - Invalid Function Code ' +
                      homedeptcode[:3] + '\n');
            # raise ValueError(
            #     "Invalid Function  Code (HRPay) " + homedeptcode[:3] + '\n')

        #print('\n' + '----------------------')
        #print('\n' + pcnaggr)
        print("Supervisor = " + str(spvrID) +'\n')

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
            scr.write('Error in jobrec.py - Invalid Payroll Company Code '+
                      str(payrollcompcode) +'\n');
            fn_write_error("Error in jobrec.py - Invalid Payroll Company Code " +
                           str(payrollcompcode) + '\n')

        ##############################################################
        # New table in Informix - Worker Category
        # Not maintained in CX, so we will have to maintain it with
        # inserts and updates
        #############################################################
        # print("Worker Cat Code")
        v_work_cat_update = fn_needs_upate(workercatcode, workercatdescr,
                                           "work_cat_code", "work_cat_descr",
                                           "cc_work_cat_table", "char", EARL)

        if v_work_cat_update == None or len(str(v_work_cat_update)) == 0:
            q_ins_wc = '''
              INSERT INTO cc_work_cat_table (work_cat_code, work_cat_descr,
                active_date)
              VALUES (?,?,?)'''
            q_ins_wc_args = (workercatcode,workercatdescr,
                             datetime.now().strftime("%m/%d/%Y"))
              # print(q_ins_wc)
             # print(q_ins_wc_args)
            engine.execute(q_ins_wc, q_ins_wc_args)
            fn_write_log("Inserted into cc_work_cat_table, code = " + workercatcode)
            scr.write(q_ins_wc + '\n');
        else:
            'Exists but no match'
            if v_work_cat_update[1] != workercatdescr:
                q_upd_wc = '''
                      UPDATE cc_work_cat_table set work_cat_descr = ?
                      WHERE work_cat_code = ?'''
                q_upd_wc_args = (workercatdescr, workercatcode)
                # print(q_upd_wc)
                # print(q_upd_wc_args)
                engine.execute(q_upd_wc, q_upd_wc_args)
                fn_write_log("Updated cc_work_cat_table, code = " + workercatcode)
                scr.write(q_upd_wc + '\n');

            ##############################################################
            # To do....
            # Job Class Code, HRClass field in Job Rec
            # Need to add definitions as needed in hrclass_table
            ##############################################################
            # jobclass = 'GA'
            # jobclassdescr = 'Graduate Assistant'
            # print("Job Class Code")

            if jobclass.strip() != "" and jobclass is not None:
                # print(jobclass)
                # print(jobclassdescr)
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
                    fn_write_log("Inserted into hrclass_table, code = " + jobclass)
                    scr.write(q_hrclass_ins + '\n');
                else:
                    # print(row[1])
                    if row[1] != jobclassdescr:
                        q_hrclass_upd = '''
                          UPDATE hrclass_table
                          SET txt = ?
                          WHERE hrclass = ?'''
                        q_hrclass_upd_args = (jobclassdescr, jobclass)

                        engine.execute(q_hrclass_upd, q_hrclass_upd_args)
                        fn_write_log("Updated hrclass_table, code = " + jobclass)
                        scr.write(q_hrclass_upd + '\n');
                    else:
                        #print("No change in HRClass Description")
                        scr.write('There were no change in HRClass description.\n');
                # If not, insert
                # Else do nothing
            else:
                print("No Job Class")


        ##############################################################
        # validate the position, division, department
        ##############################################################

        # print("Business Unit Code = " + businessunitcode[:4])

        hrdivision = fn_needs_upate(businessunitcode[:4], businessunitdescr,
                     "hrdiv", "descr", "hrdiv_table", "char", EARL)
        if hrdivision is None:
            q_ins_div = '''
               INSERT INTO hrdiv_table(hrdiv, descr, beg_date, end_date) 
               VALUES(?, ?, ?, null)'''
            q_ins_div_args = (businessunitcode[:4], businessunitdescr,
                              datetime.now().strftime("%m/%d/%Y"))
            # print("New HR Division = " + businessunitcode[:4]  + '\n')
            # print(q_ins_div + str(q_ins_div_args))
            fn_write_log(
                "Inserted into hrdiv_table, code = " + businessunitcode[:4])
            engine.execute(q_ins_div, q_ins_div_args)
            scr.write(q_ins_div + '\n');
        elif hrdivision == "":
            q_ins_div = '''
              INSERT INTO hrdiv_table(hrdiv, descr, beg_date, end_date) 
              VALUES(?, ?, ?, null)'''
            q_ins_div_args = (businessunitcode[:4], businessunitdescr,
                                datetime.now().strftime("%m/%d/%Y"))
            # print("New HR Division = " + businessunitcode[:4]  + '\n')
            # print(q_ins_div + str(q_ins_div_args))
            fn_write_log("Inserted into hrdiv_table, code = " + businessunitcode[:4])
            engine.execute(q_ins_div, q_ins_div_args)
            scr.write(q_ins_div + '\n');
        else:
            if hrdivision[1] != businessunitdescr:
                # This query works 5/25/18
                q_upd_div = '''
                    UPDATE hrdiv_table SET descr = ?, 
                              beg_date = ?
                    WHERE hrdiv = ?'''
                q_upd_div_args = (businessunitdescr,
                              datetime.now().strftime("%m/%d/%Y"),
                              businessunitcode[:4])
                print("Existing HR Division = " + hrdivision[0] + '\n')
                # print(q_upd_div + str(q_upd_div_args))
                fn_write_log("Updated hrdiv_table, code = " + businessunitcode[:4])
                engine.execute(q_upd_div, q_upd_div_args)
                scr.write(q_upd_div + '\n');

        # print("Home Department Code = " +  homedeptcode)

        hrdepartment = fn_needs_upate(homedeptcode[:3], homedeptdescr,
                      "hrdept", "descr", "hrdept_table", "char", EARL)
        if hrdepartment==None or hrdepartment=="" or len(hrdepartment)==0:
            # This query works 5/25/18
            q_ins_dept = '''
              INSERT INTO hrdept_table(hrdept, hrdiv, descr, 
                                beg_date, end_date) 
              VALUES(?, ?, ?, ?, ?)'''
            q_ins_dept_args = (homedeptcode[:3], businessunitcode[:4],
                               homedeptdescr,
                               datetime.now().strftime("%m/%d/%Y"),None)
            engine.execute(q_ins_dept, q_ins_dept_args)
            fn_write_log("Inserted into hrdept_table, code = " + homedeptcode[:3])
            scr.write(q_ins_dept + '\n');
        else:
            if hrdepartment[1] !=  homedeptdescr:
                q_upd_dept = '''
                  UPDATE hrdept_table SET hrdiv = ?, descr = ?, 
                      beg_date = ? 
                  WHERE hrdept = ?'''
                q_upd_dept_args = (businessunitcode[:4], homedeptdescr,
                                   datetime.now().strftime("%m/%d/%Y"), func_code)
                engine.execute(q_upd_dept, q_upd_dept_args)
                fn_write_log("Updated hrdept_table, code = " + homedeptcode[:3])
                scr.write(q_upd_dept + '\n');


        ###############################################################
        # Use PCN Agg to find TPos FROM position rec
        ###############################################################
        print("Find Tpos")
        # v_tpos = fn_validate_field(pcnaggr,"pcn_aggr","tpos_no",
        #                 "pos_table","char", EARL)

        v_pos = '''
                  SELECT tpos_no, descr, func_area, hrpay 
                  FROM pos_table
                  WHERE pcn_aggr = '{0}'
                      '''.format(pcnaggr)
        sql_vtpos = do_sql(v_pos, key=DEBUG, earl=EARL)
        # print(sql_vtpos)
        row = sql_vtpos.fetchone()

        if row == None:
            q_ins_pos = '''
              INSERT INTO pos_table(pcn_aggr, pcn_01, pcn_02, pcn_03, pcn_04, 
                descr, ofc, func_area, supervisor_no, tenure_track, fte, 
                max_jobs, hrpay, active_date, prev_pos) 
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            q_ins_pos_args = (pcnaggr,payrollcompcode,businessunitcode[:4],
                                func_code,jobtitlecode, jobtitledescr,
                                'OFC', func_code, None,
                                '', 0, 0, payrollcompcode,
                                datetime.now().strftime("%m/%d/%Y"),'')
            # print(q_ins_pos)
            # print(q_ins_pos_args)
            engine.execute(q_ins_pos, q_ins_pos_args)
            fn_write_log("Inserted into pos_table, code = " + pcnaggr)
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
            v_tpos = row[0]
            print("v-tpos = " + str(v_tpos))
            # print("Position query =  " + str(row))
            print("Existing values =" + row[1] + ", " + row[2] + ", " + row[3])
            # print(jobtitledescr.strip() == row[1])

            if row[1] != jobtitledescr or row[2] != func_code or row[3] != payrollcompcode:
                print("Validated t_pos = " + str(v_tpos))
                q_upd_pos = '''
                  UPDATE pos_table SET pcn_aggr = ?, pcn_01 = ?, pcn_02 = ?, 
                    pcn_03 = ?, pcn_04 = ?, descr = ?, ofc = ?, func_area = ?, 
                    supervisor_no = ?, tenure_track = ?, fte = ?, max_jobs = ?, 
                    hrpay = ?, active_date = ?, inactive_date = ? 
                  WHERE tpos_no = ?'''
                q_upd_pos_args = (pcnaggr, payrollcompcode, businessunitcode[:4],
                                  func_code, jobtitlecode, jobtitledescr,
                                  'OFC', func_code, None,
                                  'TENURE', 0, 0, payrollcompcode,
                                  datetime.now().strftime("%m/%d/%Y"), None,
                                  v_tpos)
                # print(q_upd_pos)
                # print(q_upd_pos_args)
                fn_write_log("Updated pos_table, code = " + pcnaggr)
                engine.execute(q_upd_pos, q_upd_pos_args)
                scr.write(q_upd_pos + '\n')

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
        print("Primary Position = " + primaryposition + " " + terminationdate)
        if primaryposition == 'Yes':
            rank = 1
        elif primaryposition == 'No':
            rank = 2
        # elif terminationdate.strip != '':
        #     rank = ''
        # print("Rank = " + str(rank) +'\n')

        # ##############################################################
        # If job rec exists in job_rec -update, else insert
        # ##############################################################
        print("Do Job Rec")


        # Need to add a check here for same job, different department.
        # If department changes, then the  previous job (PCN AGGR) needs an
        # end date - it is in essence a new job
        # select job_no from job_rec where id = id and end_date is null
        # and hrdept <> homedeptcode[:3]
        # If found, end date

        q_check_exst_job = '''
        select job_rec.tpos_no, pos_table.pcn_aggr, job_no
        from job_rec, pos_table
        where job_rec.tpos_no = pos_table.tpos_no
        and job_rec.title_rank =  1
        and job_rec.id = {0}
        and job_rec.end_date is null
        '''.format(carthid)
        # print(q_check_exst_job)
        sql_exst_job = do_sql(q_check_exst_job, key=DEBUG, earl=EARL)
        exst_row = sql_exst_job.fetchone()
        if exst_row is None:
            print("No Existing primary jobs")
        else:
            if exst_row[1] != pcnaggr:
                # print(pcnaggr)
                # print(exst_row[1])
                q_end_job = '''update job_rec set end_date = ?
                  where id = ? and job_no = ?
                  '''
                q_end_job_args = (datetime.now().strftime("%m/%d/%Y"), carthid, exst_row[2])
                # print(q_end_job)
                # print(q_end_job_args)
                engine.execute(q_end_job, q_end_job_args)




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
            print("Job Number not found in job rec")
            scr.write('Job Number not found in job rec' + '\n');

            #  if no record, no duplicate
            #     insert
            # NOTE:  NEED TO ADD JOB CLASS CODE into HRCLASS field
            # Insert into job rec
            # Query works as of 5/29/18
            print("Rank = " + str(rank))
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
                              'R', businessunitcode[:4], func_code, None, None,
                              positioneffective, None, 'N', 'N/A', 'N', 'N',
                              jobtitledescr, rank, workercatcode, jobclass)
            # print(q_ins_job + str(q_ins_job_args))
            print("New Job Record for " + last + ', id = ' + str(carthid))
            engine.execute(q_ins_job, q_ins_job_args)
            fn_write_log("Inserted into job_rec, tpos = " + str(v_tpos)
                         + " Description = " + jobtitledescr + " ID = " + str(carthid))
            scr.write(q_ins_job + '\n');
            # scr.write(
            #     'New Job Record for " + last + ', id = ' + str(carthid)' + '\n');

        else:
            # jobrow = sql_job.fetchone()
            print('valid job found = ' + str(jobrow[0]))
            scr.write('Valid Job Found '  +  str(jobrow[0]) + '\n');
            #print('v_tpos = ' + str(v_tpos) )


            q_upd_job = ''' 
                UPDATE job_rec SET descr = ?, id = ?, hrpay = ?, 
                supervisor_no = ?, hrstat = ?, hrdiv = ?, hrdept = ?, 
                beg_date = ?, end_date = ?, job_title = ?, worker_ctgry = ?, hrclass = ?
                WHERE job_no = ?'''
            q_upd_job_args = (jobtitledescr, carthid, payrollcompcode, spvrID,
                    '', businessunitcode[:4], func_code, positioneffective,
                    None if terminationdate == '' else terminationdate,
                    jobtitledescr, workercatcode, jobclass, jobrow[0])
            # print(q_upd_job)
            # print(q_upd_job_args)
            print("Update Job Record for " + last + ', id = ' + str(carthid))
            engine.execute(q_upd_job, q_upd_job_args)
            fn_write_log("Updated job_rec, tpos = " + str(v_tpos)
                         + " Description = " + jobtitledescr + " ID = " + str(carthid))
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
        # print("Tenure")
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
            scr.write('No Employee record found in hremp_rec. ' + '\n');
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
            fn_write_log("Inserted into hremp_rec, home_tpos_no = " + str(v_tpos) + " ID = " + str(carthid))
            scr.write(q_emp_insert + '\n');
        else:
            print('Found Emp Rec')
            scr.write('Found Employee a record in hremp_rec.' + '\n');
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
            print("Update HREMP_REC")
            engine.execute(q_emp_upd, q_emp_upd_args)
            fn_write_log("Updated hremp_rec, home_tpos_no = " + str(v_tpos) + " ID = " + str(carthid))
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
    try:
        if id < 1 or id is None or id == "":
            return 0
        else:
            # Since hrstat is not going to be valid, all I can do
            # is make sure the supervisor exists
            q_val_super = '''SELECT id FROM id_rec WHERE id = {0}
                                                   '''.format(id)
            # print(q_val_super)
            # print("ID = " + str(id))
            sql_val_super = do_sql(q_val_super, key=DEBUG, earl=EARL)
            row = sql_val_super.fetchone()

            if row == None:
                # Not found
                return(0)
            else:
                return (id)
                # Not Eligible
                # if row[0] == 'No':
                #     return(0)
                # elif row[0].strip() == 'OTH':
                #     return(0)
                # elif row[0].strip() == 'LV':
                #     return(0)
                # elif row[0].strip() == 'SA':
                #     return(0)
                # elif row[0].strip() == 'STU':
                #     return(0)
                # elif row[0].strip() == 'PDG':
                #     return(0)
                # elif row[0].strip() == 'STD':
                #     return(0)
                # Valid as Supervisor
                # else:

    except ValueError as e:
        fn_write_log("Value error in jobrec.py.  Err = " + e.message)

    except Exception as e:
        print(e)
        fn_write_error("Error in jobrec.py. Err = " + e.message)
        return(0)

