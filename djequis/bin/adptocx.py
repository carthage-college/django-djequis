import os
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
import uuid
from sqlalchemy import text
import shutil
import re
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

from djequis.core.utils import sendmail

from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djequis.adp.aarec import archive_address
#from djequis.adp.readadpfiles import finddifferences
from djequis.adp.cvidrec import process_cvid
from djequis.adp.jobrec import process_job
from djequis.adp.utilities import fn_validate_field, fn_insert_aa, \
    fn_update_aa, fn_end_date_aa
from djtools.fields import TODAY

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

#sFTP fetch (GET) downloads the file from ADP file from server
def file_download():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # External connection information for ADP Application server
    XTRNL_CONNECTION = {
       'host':settings.ADP_HOST,
       'username':settings.ADP_USER,
       'password':settings.ADP_PASS,
       'cnopts':cnopts
    }

    ############################################################################
    # sFTP GET downloads the CSV file from ADP server and saves in local directory.
    ############################################################################
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        sftp.chdir("adp/")
        # Remote Path is the ADP server and once logged in we fetch
        # directory listing
        remotepath = sftp.listdir()
        # Loop through remote path directory list
        for filename in remotepath:
            remotefile = filename
            # set local directory for which the ADP file will be downloaded to
            local_dir = ('{0}'.format(
                settings.ADP_CSV_OUTPUT
            ))
            localpath = local_dir + remotefile
            # GET file from sFTP server and download it to localpath
            sftp.get(remotefile, localpath)
            #############################################################
            # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
            # from sFTP (ADP) server
            #############################################################
            # sftp.remove(filename)
    sftp.close()

def main():
    # write out the .sql file
    scr = open("apdtocx_output.sql", "a")
    # set start_time in order to see how long script takes to execute
    start_time = time.time()
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to info
    handler = logging.FileHandler('{0}apdtocx.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # create error file handler and set level to error
    handler = logging.FileHandler('{0}apdtocx_error.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    ############################################################################
    # development server (bng), you would execute:
    # ==> python adptocx.py --database=train --test
    # production server (psm), you would execute:
    # ==> python adptocx.py --database=cars
    # without the --test argument
    ############################################################################
    # execute sftp code that needs to be executed in production only
    if not test:
        file_download()

    # set date and time to be added to the filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # set local directory for which the common app file will be downloaded to
    source_dir = ('{0}'.format(
        settings.ADP_CSV_OUTPUT
    ))

    # Defines file names and directory location
    new_adp_file = ('{0}ADPtoCX.csv'.format(
        settings.ADP_CSV_OUTPUT
    ))

    last_adp_file = ('{0}ADPtoCXLast.csv'.format(
        settings.ADP_CSV_OUTPUT
    ))

    adp_diff_file = ('{0}different.csv'.format(
        settings.ADP_CSV_OUTPUT
    ))

    # First remove yesterdays file of updates
    if os.path.isfile(adp_diff_file):
        os.remove(adp_diff_file)

    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        if database == 'cars':
            EARL = INFORMIX_EARL_PROD
        elif database == 'train':
            EARL = INFORMIX_EARL_TEST
        else:
            # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)

        #################################################################
        # STEP 1--
        # Read files and write out differences
        #################################################################

        # Need to delete the differences file to start fresh
        if os.path.isfile(adp_diff_file):
            os.remove(adp_diff_file)


        # Read in both files and compare
        # the codecs function prevents the header from ADP getting
        # into the comparison - needed because of extra characters in header
        with codecs.open(new_adp_file, 'r',
                         encoding='utf-8-sig') as t1, codecs.open(last_adp_file,
                'r', encoding='utf-8-sig') as t2:

            newfile = t1.readlines()
            oldfile = t2.readlines()

            # This uses sets to compare the two files
            # reterns additions or changes in new but not in original
            bigb = set(newfile) - set(oldfile)

            # Write to output file
            with open(adp_diff_file, 'wb') as file_out:
                # Write header row
                csvWriter = csv.writer(file_out)
                csvWriter.writerow(
                    ["file_number", "carth_id", "last_name", "first_name",
                     "middle_name", "salutation", "payroll_name",
                     "preferred_name", "birth_date", "gender", "marital_status",
                     "race", "race_descr", "ethnicity", "ethnicity_id_meth",
                     "personal_email", "primary_address1", "primary_address2",
                     "primary_address3", "primary_city", "primary_state_code",
                     "primary_state_descr", "primary_zip", "primary_county",
                     "primary_country", "primary_country_code",
                     "primary_legal_address", "home_phone", "mobile_phone",
                     "work_phone", "wc_work_phone", "wc_work_email",
                     "use_work_for_notification", "legal_address1",
                     "legal_address2", "legal_address3", "legal_city",
                     "legal_state_code", "legal_state_description", "legal_zip",
                     "legal_county", "legal_country", "legal_country_code",
                     "ssn", "hire_date", "hire_rehire_date", "rehire_date",
                     "pos_start_date", "pos_effective_date",
                     "pos_effective_end_date", "termination_date",
                     "position_status", "status_effective_date",
                     "status_eff_end_date", "adj_service_date", "archived",
                     "position_id", "primary_position", "payroll_comp_code",
                     "payroll_comp_name", "cip", "worker_cat_code",
                     "worker_cat_descr", "job_title_code", "job_title_descr",
                     "home_cost_code", "home_cost_descr", "job_class_code",
                     "job_class_descr", "job_description", "job_function_code",
                     "job_function_description", "room_number", "location_code",
                     "location_description", "leave_start_date",
                     "leave_return_date", "home_cost_number2", "payroll_code2",
                     "position_eff_date2", "position_end_date2",
                     "home_cost_number3", "payroll_code3", "position_eff_date3",
                     "position_end_date3", "home_cost_number4", "payroll_code4",
                     "position_eff_date4", "position_end_date4",
                     "home_dept_code", "home_dept_descr", "supervisor_id",
                     "supervisor_fname", "supervisor_lname","business_unit_code",
                     "business_unit_descr","reports_to_name","reports_to_pos_id",
                     "reports_to_assoc_id", "employee_assoc_id"])

                for line_no, line in enumerate(bigb):
                    x = line.split(',')
                    file_out.write(line)
                    # print('File = ' + x[0] + ', ID = ' + x[
                    #     1] + ', First = ' + x[3] + ', Last = ' + x[6])

            # close the files
            t1.close()
            t2.close()
            file_out.close()

        scr.write('---------------------------------------------------------\n')
        scr.write('-- CREATES APPLICATION FROM APD TO CX DATA \n')
        scr.write('---------------------------------------------------------\n')
        #################################################################
        # STEP 2--
        # Open differences file and start loop through records
        #################################################################
        with open(adp_diff_file, 'r') as f:
            d_reader = csv.DictReader(f, delimiter=',')
            for row in d_reader:
                # print([col + '=' + row[col] for col in d_reader.fieldnames])
                # print(row["File Number"])
                print('carthid = {0}, Fullname = {1}'.format(row["carth_id"],row["payroll_name"]))

                #################################################################
                # STEP 2a--
                # Write entire row to cc_adp_rec
                #################################################################


                q_cc_adp_rec = '''
                INSERT INTO cc_adp_rec
                (file_no, carthage_id, lastname, firstname, middlename, 
                salutation, fullname, pref_name, birth_date, gender, marital_status, race, 
                race_descr, hispanic, race_id_method, personal_email, 
                primary_addr_line1, primary_addr_line2, primary_addr_line3,
                primary_addr_city, primary_addr_st, primary_addr_state, primary_addr_zip, 
                primary_addr_county, primary_addr_country, primary_addr_country_code, 
                primary_addr_as_legal, home_phone, cell_phone, work_phone, 
                work_contact_phone, work_contact_email, work_contact_notification, 
                legal_addr_line1, legal_addr_line2, legal_addr_line3, 
                legal_addr_city, legal_addr_st, legal_addr_state, legal_addr_zip, 
                legal_addr_county, legal_addr_country, legal_addr_country_code,
                ssn, hire_date, hire_rehire_date, rehire_date, position_start_date, 
                position_effective_date, position_effective_end_date, 
                termination_date, position_status, status_effective_date,
                status_effective_end_date, adjusted_service_date, archived_employee,
                position_id, primary_position, payroll_company_code, payroll_company_name,
                cip_code, worker_category_code, worker_category_descr, job_title_code, 
                job_title_descr, home_cost_number_code, home_cost_number_descr, 
                job_class_code, job_class_descr, job_descr, job_function_code, 
                job_function_descr, room, bldg, bldg_name, leave_of_absence_start_date, 
                leave_of_absence_return_date, home_cost_number_2, payroll_company_code_2, 
                position_effective_date_2, position_end_date_2, home_cost_number_3, 
                payroll_company_code_3, position_effective_date_3, position_end_date_3, 
                home_cost_number_4, payroll_company_code_4, position_effective_date_4, 
                position_end_date_4, home_depart_num_code, home_depart_num_descr, 
              
                supervisor_id, supervisor_firstname, supervisor_lastname, 
                business_unit_code, business_unit_descr, reports_to_name,
                reports_to_position_id, reports_to_associate_id, 
                employee_associate_id, date_stamp)
                    VALUES 
                    ({0},{1},"{2}","{3}","{4}",
                    "{5}","{6}","{7}","{8}","{9}","{10}",
                "{11}","{12}","{13}","{14}",
                "{15}","{16}","{17}",
                "{18}","{19}","{20}","{21}",
                "{22}","{23}","{24}","{25}",
                "{26}","{27}","{28}","{29}",
                "{30}", "{31}","{32}",
                "{33}","{34}","{35}",
                "{36}","{37}","{38}","{39}",
                "{40}","{41}","{42}",
                "{43}","{44}","{45}","{46}","{47}",
                "{48}","{49}",
                "{50}", "{51}","{52}",
                "{53}","{54}","{55}",
                "{56}","{57}","{58}","{59}",
                "{60}","{61}","{62},"{63}"",
                "{64}","{65}","{66}",
                "{67}","{68}","{69}","{70}",
                "{71}",{72},"{73}","{74}","{75}",
                "{76}","{77}","{78}",
                "{79}","{80}","{81}",
                "{82}","{83}","{84}",
                "{85}","{86}","{87}",
                "{88}","{89}","{90}",
                "{91}","{92}","{93}",
                "{94}","{95}","{96}",
                "{97}","{98}","{99}","{100}");
                '''.format(row["file_number"], row["carth_id"], row["last_name"],
                           row["first_name"], row["middle_name"], row["salutation"],
                           row["payroll_name"], row["preferred_name"], row["birth_date"],
                           row["gender"], row["marital_status"], row["race"],
                           row["race_descr"], row["ethnicity"], row["ethnicity_id_meth"],
                           row["personal_email"], row["primary_address1"],
                           row["primary_address2"], row["primary_address1"],
                           row["primary_city"], row["primary_state_code"],
                           row["primary_state_descr"], row["primary_zip"],
                           row["primary_county"], row["primary_country"],
                           row["primary_country_code"], row["primary_legal_address"],
                           row["home_phone"], row["mobile_phone"], row["work_phone"],
                           row["wc_work_phone"], row["wc_work_email"],
                           row["use_work_for_notification"], row["legal_address1"],
                           row["legal_address2"], row["legal_address3"], row["legal_city"],
                           row["legal_state_code"], row["legal_state_description"],
                           row["legal_zip"], row["legal_county"], row["legal_country"],
                           row["legal_country_code"], row["ssn"], row["hire_date"],
                           row["hire_rehire_date"], row["rehire_date"], row["pos_start_date"],
                           row["pos_effective_date"], row["pos_effective_end_date"],
                           row["termination_date"], row["position_status"],
                           row["status_effective_date"], row["status_eff_end_date"],
                           row["adj_service_date"], row["archived"], row["position_id"],
                           row["primary_position"], row["payroll_comp_code"],
                           row["payroll_comp_name"], row["cip"], row["worker_cat_code"],
                           row["worker_cat_descr"], row["job_title_code"], row["job_title_descr"],
                           row["home_cost_code"], row["home_cost_descr"], row["job_class_code"],
                           row["job_class_descr"], row["job_description"], row["job_function_code"],
                           row["job_function_description"], row["room_number"], row["location_code"],
                           row["location_description"], row["leave_start_date"], row["leave_return_date"],
                           row["home_cost_number2"], row["payroll_code2"], row["position_eff_date2"],
                           row["position_end_date2"], row["home_cost_number3"], row["payroll_code3"],
                           row["position_eff_date3"], row["position_end_date3"], row["home_cost_number4"],
                           row["payroll_code4"], row["position_eff_date4"], row["position_end_date4"],
                           row["home_dept_code"], row["home_dept_descr"], row["supervisor_id"],
                           row["supervisor_fname"], row["supervisor_lname"], row["business_unit_code"],
                           row["business_unit_descr"], row["reports_to_name"], row["reports_to_pos_id"],
                           row["reports_to_assoc_id"], row["employee_assoc_id"], datetime.now().strftime("%Y-%m-%d"))
                # print(q_cc_adp_rec)
                scr.write(q_cc_adp_rec+'\n');
                logger.info("Inserted into adp_rec table");
                # do_sql(q_cc_adp_rec, key=DEBUG, earl=EARL)

                #################################################################
                # STEP 2b--
                # Do updates to id_rec
                # Note - we may have to deal with addresses separately from
                # basic demographic information
                #################################################################
                # If ADP File is missing the Carthage ID, we cannot process the record
                if row["carth_id"] == "":
                    print('No Carthage ID - abort this record and email HR')

                    # email HR if CarthID is missing
                    SUBJECT = 'No Carthage ID - abort this record and email HR'
                    BODY = 'No Carthage ID, process aborted. Name = {0}, ADP File = {1}'.format(row["payroll_name"],row["file_number"])
                    sendmail(settings.ADP_TO_EMAIL, settings.ADP_FROM_EMAIL,
                        BODY, SUBJECT
                    )
                    logger.error('There was no carthage ID in file, row skipped. Name = {0}, ADP File = {1}'.format(row["payroll_name"],row["file_number"]))
                # Exclude student employees from process, paycode DPW
                elif row["payroll_comp_code"] != 'DPW':



                    # Check to see if record exists in id_rec

                    results = fn_validate_field(row["carth_id"],"id","id",
                                                "id_rec","integer")

                    print("ID Validate result = " + str(results))

                    # q_select_id_rec = '''
                    # SELECT id_rec.id, id_rec.fullname
                    # FROM id_rec
                    # WHERE id_rec.id = {0}
                    # ''' .format(row["carth_id"])
                    # scr.write(q_select_id_rec+'\n');
                    # logger.info("Select from id_rec table");
                    # sqlresult = do_sql(q_select_id_rec, earl=EARL)
                    # results = sqlresult.fetchone()

                    if results == None:

                        fn_process_idrec(row["carth_id"], row["payroll_name"],
                                         row["last_name"], row["first_name"],
                                         row["middle_name"],
                                         row["primary_address1"],
                                         row["primary_address2"],
                                         row["primary_address1"],
                                         row["primary_city"],
                                         row["primary_state_code"],
                                         row["primary_zip"],
                                         row["primary_country"],
                                         row["ssn"], row["home_phone"],
                                         row["position_status"],
                                         row["pos_effective_date"])

                    #     # Insert or update as needed to ID_rec
                    #     q_insert_id_rec = '''
                    #     INSERT INTO id_rec
                    #         (fullname, lastname, firstname, middlename, addr_line1,
                    #         addr_line2, addr_line3, city, st, zip, ctry, AA, ss_no,
                    #         decsd)
                    #     VALUES({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},"PERM",
                    #     {11},"N")
                    #     ''' .format(row["payroll_name"], row["last_name"],
                    #                 row["first_name"], row["middle_name"],
                    #                 row["primary_address1"], row["primary_address2"],
                    #                 row["primary_address3"], row["primary_city"],
                    #                 row["primary_state_code"], row["primary_zip"],
                    #                 row["primary_country_code"], row["ssn"])
                    #     #print(q_insert_id_rec)
                    #     scr.write(q_insert_id_rec+'\n');
                    #     logger.info("Inserted into id_rec table");
                    #     #do_sql(q_insert_id_rec, key=DEBUG, earl=EARL)
                    # else:
                    #     q_update_id_rec = '''
                    #         update id_rec set fullname = "{0}",
                    #         lastname = "{1}", firstname = "{2}",
                    #         middlename = "{3}", ss_no = "{4}", decsd = "N",
                    #         add_date = "{5}", upd_date = "{6}", ofc_add_by = "HR"
                    #         where id = {7}
                    #     '''.format(row["payroll_name"],row["last_name"],
                    #                row["first_name"], row["middle_name"], row["ssn"],
                    #                row["hire_rehire_date"], row["pos_effective_date"],
                    #                row["carth_id"])
                    #     #print(q_update_id_rec)
                    #     scr.write(q_update_id_rec + '\n');
                    #     logger.info("Update id_rec table");
                    #     # do_sql(q_update_id_rec, key=DEBUG, earl=EARL)
                    #

                    #also need to deal with address changes
                    # Search for existing address record


                        # do_sql(q_update_id_rec_addr, key=DEBUG, earl=EARL)
                        #print('ID Rec Updated')
                        #print('Change in address - do change for aa_rec')

                        #########################################################
                        # Routine to deal with aa_rec
                        #########################################################

                        # Call to addresssubs.py
                        # this will see if address exists in aa_rec and do
                        # inserts or updates as needed
                        archive_address(row["carth_id"],row["payroll_name"],
                            row["primary_address1"],row["primary_address2"],
                            row["primary_address3"],row["primary_city"],
                            row["primary_state_code"], row["primary_zip"],
                            row["primary_country_code"])

                    #     q_check_aa_adr = '''
                    #         SELECT id, aa, aa_no, beg_date, line1, line2, line3,
                    #         city, st, zip, ctry
                    #         From aa_rec
                    #         Where id = {0}
                    #         and aa in ('PERM','PREV','SCND')
                    #         and end_date is null
                    #         '''.format(row["carth_id"])
                    #     sql_id_address = do_sql(q_check_aa_adr, earl=EARL)
                    #     addr_result = sql_id_address.fetchone()
                    #     #print(q_check_aa_adr)
                    #     #print("AA Rec Addr Result = " + str(addr_result))
                    #     # logger.info("Select address info from id_rec table");
                    #
                    #     #################################
                    #     #  Find the max start date of all PREV entries with a null end date
                    #     #################################
                    #
                    #     q_check_aa_date = '''
                    #         SELECT max(beg_date), ID, aa, line1, end_date
                    #         as date_end
                    #         From aa_rec
                    #         Where id = {0}
                    #         and aa = 'PREV'
                    #         and end_date is null
                    #         group by id, aa, end_date, line1
                    #         '''.format(row["carth_id"])
                    #     #print(q_check_aa_date)
                    #     # logger.info("Select address info from id_rec table");
                    #     sql_date = do_sql(q_check_aa_date, earl=EARL)
                    #     date_result = sql_date.fetchone()
                    #     # print date_result
                    #
                    #     #################################
                    #     # Define date variables
                    #     #################################
                    #     if date_result == None:  # No aa rec found
                    #         a1 = ""
                    #         max_date = datetime.now().strftime("%Y/%m/%d")
                    #     # Make sure dates don't overlap
                    #     else:
                    #         #print(date_result)
                    #         max_date = date.strftime(date_result[0], "%Y/%m/%d")
                    #         a1 = date_result[3]
                    #
                    #     #print("A1 = " + a1)
                    #     #print("Max date = " + str(max_date))
                    #     #print("Now = " + str(datetime.now()))
                    #
                    #     # Scenario 1
                    #     # This means that the ID_Rec address will change
                    #     # but nothing exists in aa_rec, so we will only insert as 'PREV'
                    #     if addr_result == None:  # No address in aa rec?
                    #         #print("No existing record in AA Rec - Insert only")
                    #         # call function to insert record
                    #         fnct_insert_aa(row["carth_id"],  row["payroll_name"],
                    #              row["primary_address1"], row["primary_address2"],
                    #              row["primary_address3"], row["primary_city"],
                    #              row["primary_state_code"],
                    #              row["primary_zip"], row["primary_country_code"], max_date)
                    #
                    #     # Scenario 2
                    #     # if record found in aa_rec, then we will need more options
                    #     # Find out if the record is an exact match with another address
                    #     # Question is, what is enough of a match to update rather than insert new?
                    #     # id, fullname, addr1, addr2, addr3, cty, st, zp, ctry
                    #     # (1003664, 'PREV', 158, datetime.date(2010, 2, 2),
                    #     # '15008 Lost Canyon Ct.#102', '', '', 'Woodbridge', 'VA', '22191', 'USA')
                    #     elif addr_result[4] == row["primary_address1"] \
                    #             and addr_result[9] == row["primary_zip"]:
                    #         # and addr_result[7] == cty \
                    #         # and addr_result[8] == st \
                    #         # and addr_result[10] == ctry:
                    #         # or addr_result[5] == addr2 \
                    #         # or addr_result[6] == addr3 \
                    #
                    #         #################################
                    #         # Match found then we are UPDATING only....
                    #         #################################
                    #         fnct_update_aa(addr_result[0], addr_result[1],
                    #                    addr_result[2], row["payroll_name"],
                    #                    addr_result[4], addr_result[5],
                    #                    addr_result[6], addr_result[7],
                    #                    addr_result[8], addr_result[9],
                    #                    addr_result[10], addr_result[3])
                    #
                    #         print(
                    #             "An Address exists and matches new data - Update with new")
                    #
                    #     # to avoid overlapping dates
                    #     # Scenario 3 - AA Rec exists but does not match new address.
                    #     # End old, insert new
                    #     else:
                    #         if max_date >= str(datetime.now()):
                    #             beg_date = max_date  # add one day...
                    #         else:
                    #             beg_date = datetime.now().strftime("%m/%d/%Y")
                    #
                    #         fn_end_date_aa(addr_result[0], addr_result[2],
                    #                     addr_result[4], row["payroll_name"],
                    #                     addr_result[3],
                    #                     datetime.now().strftime("%m/%d/%Y"))
                    #         fnct_insert_aa(row["carth_id"], row["payroll_name"],
                    #                   row["primary_address1"], row["primary_address2"],
                    #                   row["primary_address3"], row["primary_city"],
                    #                   row["primary_state_code"],
                    #                   row["primary_zip"],  row["primary_country_code"], beg_date)
                    #
                    #         # print(
                    #         #     "An Address exists but does not match - end current, insert new")
                    #
                    #
                    else:
                        #print("sql addr " + addr_result[1].strip() + " loop address = " + row["primary_address1"].strip())
                        print("Address matches, no changes needed")

                        # To be deleted....
                        # if addr1 = addr_line1 and addr2 = addr_line2 and
                        # addr3 = addr_line3
                        # and cty = city and st = state and zp = zip and ctry
                        # = country:
                        # bArchive = False
                        # bChange = False


                    if row["personal_email"] != '':
                        email_result = + fn_set_email2(row["personal_email"],
                                                       row["carth_id"])

                        print("Email = " + str(email_result))

                        # q_check_email = '''
                        #     SELECT aa_rec.aa, aa_rec.id, aa_rec.line1,
                        #     aa_rec.aa_no, aa_rec.beg_date
                        #     FROM aa_rec
                        #     WHERE aa_rec.id = {0}
                        #     AND aa_rec.aa = 'EML2'
                        #     AND aa_rec.end_date IS NULL
                        #     '''.format(row["carth_id"])
                        # print(q_check_email)
                        # # logger.info("Select email info from aa_rec table");
                        # sql_email = do_sql(q_check_email, earl=EARL)
                        # email_result = sql_email.fetchone()


                        # if email_result == row["personal_email"]:
                        #     print("no change")
                        # elif email_result != None and \
                        #         email_result != row["personal_email"]:
                        #     # End date current EML2
                        #     print("Existing email = " + email_result[0])
                        #     fn_end_date_aa(row["carth_id"], "EML2", email_result[0],
                        #                 row["payroll_name"],
                        #                 email_result[1],
                        #                 datetime.now().strftime("%Y-%m-%d"))
                        #     # insert new
                        #     fnct_insert_aa(row["carth_id"], row["payroll_name"],
                        #               row["personal_email"],"","","","","","",
                        #               datetime.now().strftime("%Y/%m/%d"))
                        #     print("New Email will be = " + row[
                        #         "personal_email"])
                        # else:
                        #     # Insert email into aa_rec
                        #     print("New Email will be = " + row["personal_email"])
                        #     fnct_insert_aa(row["carth_id"], row["payroll_name"],
                        #               row["personal_email"],"","","","","","",
                        #               datetime.now().strftime("%Y/%m/%d"))

                    else:
                        print("No email from ADP")

                    #Check to update phone in aa_rec

                    if row["mobile_phone"] != "":
                        cell = fn_set_cell_phone(row["mobile_phone"],
                                 row["carth_id"], row["payroll_name"])
                        print("Cell phone result: " + cell)
                    else:
                        print("No Cell")

                    #################################################################
                    # STEP 2c--
                    # Do updates to profile_rec
                    #################################################################
                    # Find out if record exists to determine update vs insert

                    prof_rslt = fn_validate_field(row["carth_id"],"id","id","profile_rec","integer")

                    # q_select_prof_rec = '''
                    #     SELECT profile_rec.id
                    #     FROM profile_rec
                    #     WHERE profile_rec.id = {0}
                    #     '''.format(row["carth_id"])
                    # scr.write(q_select_prof_rec + '\n');
                    # logger.info("Select from profile_rec table");
                    # sql_prof_rslt = do_sql(q_select_prof_rec, earl=EARL)
                    # prof_rslt = sql_prof_rslt.fetchone()
                    print("Prof Result = " + str(prof_rslt))

                    # create ethnicity dictionary
                    racecode = {
                        '1': 'WH',
                        '2': 'BL',
                        '4': 'AS',
                        '6': 'AP',
                        '9': 'MU'
                    }
                    race = racecode.get(row["race"])

                    ethnicity = {
                        'Not Hispanic or Latino': 'N',
                        'HISPANIC OR LATINO': 'Y'
                    }
                    ethnicity = ethnicity.get(row["ethnicity"])

                    if prof_rslt == None:
                        # Insert or update as needed to ID_rec
                        q_insert_prof_rec = '''
                            INSERT INTO profile_rec (id, ethnic_code, sex, 
                                race, hispanic, birth_date, prof_last_upd_date)
                                values ({0},{1},{2},{3}, "",{4},TODAY) 
                            '''.format(row["carth_id"], ethnicity,
                                       row["gender"], race,
                                       row["birth_date"])
                        print(q_insert_prof_rec)
                        scr.write(q_insert_prof_rec + '\n');
                        logger.info("Inserted into profile_rec table");
                        #do_sql(q_insert_prof_rec, key=DEBUG, earl=EARL)
                    else:
                        q_update_prof_rec = '''
                            UPDATE profile_rec SET sex = "{0}",
                            ethnic_code = "{1}", race = "{2}",
                            hispanic = "", birth_date = "{3}", 
                            prof_last_upd_date = TODAY
                            where id = {4}
                        '''.format(row["gender"], ethnicity, race,
                                   datetime.strftime(date(row["birth_date"]),"%Y/%m/%d"),
                                   row["carth_id"])
                        print(q_update_prof_rec)
                        scr.write(q_update_prof_rec + '\n');
                        logger.info("Update profile_rec table");
                        # do_sql(q_update_prof_rec, key=DEBUG, earl=EARL)

                    #################################################################
                    # STEP 2d--
                    # Do updates to cvid_rec
                    #################################################################

                    # Call to cvidrec.py
                    process_cvid(row["carth_id"], row["file_number"],
                                 row["ssn"], row["employee_assoc_id"])

                    # q_select_cvid_rec = '''
                    #    SELECT cvid_rec.cx_id
                    #    FROM cvid_rec
                    #    WHERE cvid_rec.cx_id = {0}
                    #    '''.format(row["carth_id"])
                    # print(q_select_cvid_rec)
                    # scr.write(q_select_cvid_rec + '\n');
                    # logger.info("Select from cvid_rec table");
                    # sql_cvid_rslt = do_sql(q_select_cvid_rec, earl=EARL)
                    # cvid_rslt = sql_cvid_rslt.fetchone()
                    #
                    # if cvid_rslt == None:
                    #     # Insert or update as needed to ID_rec
                    #     q_insert_cvid_rec = '''
                    #        INSERT INTO cvid_rec (old_id, old_id_num, adp_id,
                    #            ssn, cx_id, cx_id_char, adp_associate_id)
                    #            VALUES ("{0}",{0},"{1}","{2}",{0},"{0}","{3}")
                    #        '''.format(row["carth_id"], row["file_number"],
                    #                   row["ssn"], "adp_associate_id")
                    #     print(q_insert_cvid_rec)
                    #     scr.write(q_insert_cvid_rec + '\n');
                    #     logger.info("Inserted into cvid_rec table");
                    #     # do_sql(q_insert_cvid_rec, key=DEBUG, earl=EARL)
                    # else:
                    #     q_update_cvid_rec = '''
                    #        UPDATE cvid_rec SET old_id = "{0}", old_id_num = {0},
                    #        adp_id = "{1}", ssn = "{2}", cx_id = {0},
                    #        adp_associate_id = "{3}"
                    #        WHERE cx_id = {0}
                    #    '''.format(row["carth_id"], row["file_number"],
                    #             row["ssn"], "adp_associate_id")
                    #     print(q_update_cvid_rec)
                    #     scr.write(q_update_cvid_rec + '\n');
                    #     logger.info("Update cvid_rec table");
                        # do_sql(q_update_cvid_rec, key=DEBUG, earl=EARL)
                    #################################################################
                    # STEP 2e--
                    # Do updates to job_rec
                    #################################################################
                        # Must account for Division, Dept
                        # use PCN Codes to tie employee to job number
                        # validate a number of fields as needed
                        # add GL Func code to func_area in position table
                        # if there is a secondary job record, do the same..

                    # def process_job(carthid, workercatcode, workercatdescr,
                    #                 businessunitcode,
                    #                 businessunitdescr, homedeptcode,
                    #                 homedeptdescr, jobtitlecode,
                    #                 jobtitledescr, positionstart, poseffectend,
                    #                 payrollcompcode,
                    #                 jobfunctioncode, jobfuncdtiondescription,
                    #                 primaryposition,
                    #                 supervisorid, last, first, middle):

                    process_job(row["carth_id"], row["worker_cat_code"],
                                row["worker_cat_descr"], row["business_unit_code"],
                                row["business_unit_descr"], row["home_dept_code"],
                                row["home_dept_descr"], row["job_title_code"],
                                row["job_title_descr"], row["pos_start_date"],
                                row["pos_effective_end_date"], row["payroll_comp_code"],
                                row["job_function_code"],
                                row["job_function_description"],
                                row["primary_position"], row["supervisor_id"],
                                row["last_name"], row["first_name"],
                                row["middle_name"])


            # set destination directory for which the sql file will be archived to
            archived_destination = ('{0}apdtocx_output-{1}.sql'.format(
                settings.ADP_CSV_ARCHIVED, datetimestr
            ))
            # set name for the sqloutput file
            sqloutput = ('{0}/apdtocx_output.sql'.format(os.getcwd()))
            # Check to see if sql file exists, if not send Email
            if os.path.isfile("apdtocx_output.sql") != True:
                # there was no file found on the server
                SUBJECT = '[APD To CX Application] failed'
                BODY = "There was no .sql output file to move."
                sendmail(
                    settings.ADP_TO_EMAIL,settings.ADP_FROM_EMAIL,
                    BODY, SUBJECT
                )
                logger.error("There was no .sql output file to move.")
            else:
                # rename and move the file to the archive directory
                shutil.move(sqloutput, archived_destination)

            ######################################################################
            # The last step - move last to archive, rename new file to _last
            ######################################################################
            #adptocx_archive = ('{0}adptocxlast_{1}.csv'.format(settings.ADP_CSV_ARCHIVED,datetimestr))
            #shutil.move(last_adp_file, adptocx_archive)

            #adptocx_rename = ('{0}ADPtoCXLast.csv'.format(settings.ADP_CSV_OUTPUT))
            #shutil.move(new_adp_file,adptocx_rename)

    except Exception as e:
        print(e)

###################################################
# SQL Functions
###################################################
# def fnct_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, beg_date):
#     q_insert_aa = '''INSERT INTO aa_rec(id, aa, beg_date, peren, end_date,
#                          line1, line2, line3, city, st,
#                          zip, ctry, phone, phone_ext, ofc_add_by,
#                          cell_carrier, opt_out)
#                       VALUES
#                          ({0},{1},{2},{3},{4},
#                          {5},{6},{7},{8},{9},
#                          {10},{11},{12},{13},{14},
#                          {15},{16})
#                          '''.format(id, "PERM", beg_date, "N", "",
#                                     addr1, addr2, addr3, cty, st,
#                                     zp, ctry, "", "", "HR",
#                                     "", "")
#     #scr.write(q_insert_aa + '\n');
#     #logger.info("Inserted " + addr1 + "into aa_rec table for " + fullname + ", ID = " + id);
#     #sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
#     # insert_result = sql_aa_insert.fetchone(
#     #print(q_insert_aa)
#     print("Inserted " + addr1 + "into aa_rec table for " + fullname + ", ID = " + str(id))

# def fnct_update_aa(id, aa, aanum, fullname, add1, add2, add3, cty, st, zip, ctry, begdate):
#     #print("update aa completed")
#
#     q_update_aa = '''update aa_rec
#                       set line1 = "{4}",
#                       line2 = "{5}",
#                       line3 = "{6}",
#                       city = "{8}",
#                       st = "{9}",
#                       zip = "{10}",
#                       ctry = "{11}"
#                       where aa_no = {2}
#                       '''.format(id, aa, aanum ,fullname, add1, add2, add3,
#                                  begdate, cty, st, zip, ctry)
#     #logger.info("Updated " + addr1 + "in aa_rec table for " + fullname + ", ID = " + id);
#     # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
#     # insert_result = sql_aa_insert.fetchone(
#     #print(q_update_aa)
#     print("Updated " + add1 + "in aa_rec table for " + fullname + ", ID = " + str(id))
#
#
# def fn_end_date_aa(id, aa_num, addr1, fullname, begdate, enddate):
#         #print("end Date aa completed")
#
#     q_update_aa = '''update aa_rec
#                       set end_date = {4}
#                       where id = {0}
#                       and aa_no = {1}
#                       and beg_date = {3}
#                       '''.format(id, aa_num, fullname, begdate, enddate)
#     #logger.info("End dated " + addr1 + "in aa_rec table for " + fullname + ", ID = " + id);
#     # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
#     # insert_result = sql_aa_insert.fetchone(
#     #print(q_update_aa)
#     print("End dated " + addr1 + "in aa_rec table for " + fullname + ", ID = " + str(id))


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
