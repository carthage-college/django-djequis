import os
import sys
import pysftp
import csv
import codecs
import warnings
from datetime import datetime
import codecs
import time
from time import strftime
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler

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
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY

# Imports for additional modules and functions written as part of this project
from djequis.adp.idrec import fn_process_idrec
from djequis.adp.aarec import fn_archive_address, fn_insert_aa, \
    fn_update_aa, fn_end_date_aa, fn_set_email, fn_set_cell_phone, \
    fn_set_schl_rec
from djequis.adp.cvidrec import fn_process_cvid
from djequis.adp.jobrec import fn_process_job
from djequis.adp.utilities import fn_validate_field, fn_convert_date, \
    fn_format_phone, fn_write_log, fn_write_error, fn_clear_logger
from djequis.adp.profilerec import fn_process_profile_rec
from djequis.adp.adp_ftp import file_download
from djequis.adp.secondjob import fn_process_second_job

# normally set as 'debug" in SETTINGS
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

# This is a hack to get rid of a warning message paramico, cryptography
warnings.filterwarnings(action='ignore',module='.*paramiko.*')

#sFTP fetch (GET) downloads the file from ADP file from server
def file_download():
    print("Get ADP File")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # cnopts.hostkeys = settings.ADP_HOSTKEY
    # External connection information for ADP Application server
    XTRNL_CONNECTION = {
       'host':settings.ADP_HOST,
       'username':settings.ADP_USER,
       'password':settings.ADP_PASS,
       'cnopts':cnopts
    }

    ##########################################################################
    # sFTP GET downloads the CSV file from ADP server and saves
    # in local directory.
    ##########################################################################
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        print("Enter download")
        try:
            print('Connection Established')
            sftp.chdir("adp/")
            # Remote Path is the ADP server and once logged in we fetch
            # directory listing
            remotepath = sftp.listdir()
            # Loop through remote path directory list
            print("Remote Path = " + str(remotepath))
            for filename in remotepath:
                remotefile = filename
                print("Remote File = " + str(remotefile))
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
        except Exception as e:
            print("Error in cc_adp_rec.py, " + e.message)
        # fn_write_error("Error in cc_adp_rec.py, adptocx.csv not found ",
    sftp.close()


# write out the .sql file
# scr = open("apdtocx_output.sql", "a")

def main():
    # set start_time in order to see how long script takes to execute
    start_time = time.time()

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python cc_adp_rec.py --database=train --test
    # production server (psm), you would execute:
    # ==> python cc_adp_rec.py --database=cars
    # without the --test argument
    ##########################################################################

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
        if database == 'train':
            EARL = INFORMIX_EARL_TEST
        elif database == 'sandbox':
            EARL = INFORMIX_EARL_SANDBOX
        else:
        # this will raise an error when we call get_engine()
        # below but the argument parser should have taken
        # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)

        #################################################################
        # STEP 0--
        # Pull the file from the ADP FTP site
        # execute sftp code that needs to be executed in production only
        #################################################################
        # if not test:
        print("Down load file")
        file_download()
        print("file downloaded")

        #################################################################
        # STEP 1--
        # Get the most recent rows from the cc_adp_rec table and write them
        # to a csv file to locate Read files and write out differences
        #################################################################
        cxview = "adptocxview.csv"

        csv.register_dialect('myDialect',
                             quoting=csv.QUOTE_ALL,
                             skipinitialspace=True)
        with open(cxview, 'wb') as file_out:
            # Write header row
            csvWriter = csv.writer(file_out, dialect='myDialect')
            csvWriter.writerow(
                ["File Number","Carthage ID #","Last Name","First Name",
                 "Middle Name","Salutation","Payroll Name","Preferred Name",
                 "Birth Date","Gender","Marital Status Code","Race Code",
                 "Race Description","Ethnicity","Ethnicity/Race ID Method",
                 "Personal Contact: Personal Email",
                 "Primary Address: Address Line 1",
                 "Primary Address: Address Line 2",
                 "Primary Address: Address Line 3","Primary Address: City",
                 "Primary Address: State / Territory Code",
                 "Primary Address: State / Territory Description",
                 "Primary Address: Zip / Postal Code",
                 "Primary Address: County","Primary Address: Country",
                 "Primary Address: Country Code",
                 "Primary Address: Use as Legal / Preferred Address",
                 "Personal Contact: Home Phone",
                 "Personal Contact: Personal Mobile",
                 "Work Phone","Work Contact: Work Phone",
                 "Work Contact: Work Email",
                 "Work Contact: Use Work Email for Notification",
                 "Legal / Preferred Address: Address Line 1",
                 "Legal / Preferred Address: Address Line 2",
                 "Legal / Preferred Address: Address Line 3",
                 "Legal / Preferred Address: City",
                 "Legal / Preferred Address: State / Territory Code",
                 "Legal / Preferred Address: State / Territory Description",
                 "Legal / Preferred Address: Zip / Postal Code",
                 "Legal / Preferred Address: County",
                 "Legal / Preferred Address: Country",
                 "Legal / Preferred Address: Country Code",
                 "Tax ID (SSN)","Hire Date","Hire Date/Rehire Date",
                 "Rehire Date","Position Start Date","Position Effective Date",
                 "Position Effective End Date","Termination Date",
                 "Position Status","Status Effective Date",
                 "Status Effective End Date","Adjusted Service Date",
                 "Archived Employee","Position ID","Primary Position",
                 "Payroll Company Code","Payroll Company Name","CIP Code",
                 "Worker Category Code","Worker Category Description",
                 "Job Title Code","Job Title Description",
                 "Home Cost Number Code","Home Cost Number Description",
                 "Job Class Code","Job Class Description","Job Description",
                 "Job Function Code","Job Function Description","Room Number",
                 "Location Code","Location Description",
                 "Leave of Absence Start Date","Leave of Absence Return Date",
                 "Home Department Code","Home Department Description",
                 "Supervisor ID","Supervisor First Name",
                 "Supervisor Last Name","Business Unit Code",
                 "Business Unit Description","Reports To Name",
                 "Reports To Position ID","Reports To Associate ID",
                 "Associate ID","This is a Management position",
                 "Supervisor Position","Directory Job Title"])
        file_out.close()

        # # This select statement should only return the most recent records
        # # But it must be formatted to precisely match the adp file for
        # # row by row comparison
        # cx_view_sql = '''SELECT
        #     file_no, carthage_id, lastname, firstname, middlename, salutation,
        #     fullname, pref_name, to_char(birth_date, '%m/%d/%Y') birth_date,
        #     CASE
        #         WHEN gender = 'F' THEN 'Female'
        #         WHEN gender = 'M' THEN 'Male'
        #         ELSE ''
        #         END as gender,
        #     marital_status,
        #     CASE
        #         WHEN race = 'WH' THEN '1'
        #         WHEN race = 'BL' THEN '2'
        #         WHEN race = 'AS' THEN '4'
        #         WHEN race = 'AM' THEN '5'
        #         WHEN race = 'AP' THEN '6'
        #         WHEN race = 'MU' THEN '9'
        #         ELSE ''
        #         END as RaceCode,
        #     CASE
        #             WHEN race = 'WH'
        #                 THEN 'White'
        #             WHEN race = 'BL'
        #                 THEN 'Black or African American'
        #             WHEN race = 'AS'
        #                 THEN 'Asian'
        #             WHEN race = 'AM'
        #                 THEN 'American Indian or Alaska Native'
        #             WHEN race = 'AP'
        #                 THEN 'Native Hawaiian or Other Pacific Islander'
        #             WHEN race = 'MU'
        #                 THEN 'Two or more races'
        #             ELSE ''
        #             END as race_descr,
        #     CASE
        #         when hispanic = 'Y' THEN 'Hispanic or Latino'
        #         when hispanic = 'N' THEN 'Not Hispanic or Latino'
        #         ELSE ''
        #         END
        #     hispanic,
        #     race_id_method, personal_email, primary_addr_line1,
        #     primary_addr_line2, primary_addr_line3, primary_addr_city,
        #     primary_addr_st, primary_addr_state, primary_addr_zip,
        #     primary_addr_county, primary_addr_country,
        #     primary_addr_country_code,
        #     CASE
        #         when primary_addr_as_legal = 'Y' THEN 'Yes'
        #         when primary_addr_as_legal = 'N' THEN 'No'
        #         ELSE ''
        #         END
        #     primary_addr_as_legal,
        #     CASE
        #         WHEN trim(home_phone) != ''
        #         THEN '('||SUBSTR(home_phone, 1, 3)||') '||SUBSTR(home_phone, 5, 3)||'-'||SUBSTR(home_phone, 9, 4)
        #         ELSE ''
        #         END home_phone,
        #     CASE
        #         WHEN trim(cell_phone) != ''
        #         THEN '('||SUBSTR(cell_phone, 1, 3)||') '||SUBSTR(cell_phone, 5, 3)||'-'||SUBSTR(cell_phone, 9, 4)
        #         ELSE ''
        #         END cell_phone,
        #     CASE
        #         WHEN trim(work_phone) != ''
        #         THEN '('||SUBSTR(work_phone, 1, 3)||') '||SUBSTR(work_phone, 5, 3)||'-'||SUBSTR(work_phone, 9, 4)
        #         ELSE ''
        #         END work_phone,
        #     CASE
        #         WHEN trim(work_contact_phone) != ''
        #         THEN '('||SUBSTR(work_contact_phone, 1, 3)||') '||SUBSTR(work_contact_phone, 5, 3)||'-'||SUBSTR(work_contact_phone, 9, 4)
        #         ELSE ''
        #         END work_contact_phone,
        #     work_contact_email,
        # 	CASE
	    #     	WHEN work_contact_notification = 'Y' THEN 'Yes'
		#         WHEN work_contact_notification = 'N' THEN 'No'
		#         ELSE ''
		#         END work_contact_notification,
		#     legal_addr_line1, legal_addr_line2,
        #     legal_addr_line3, legal_addr_city, legal_addr_st, legal_addr_state,
        #     legal_addr_zip, legal_addr_county, legal_addr_country,
        #     legal_addr_country_code, ssn,
        #     to_char(hire_date, '%m/%d/%Y') hire_date,
        #     to_char(hire_rehire_date, '%m/%d/%Y') hire_rehire_date,
        #     to_char(rehire_date, '%m/%d/%Y') rehire_date,
        #     to_char(position_start_date, '%m/%d/%Y') position_start_date,
        #     to_char(position_effective_date, '%m/%d/%Y') position_effective_date,
        #     to_char(position_effective_end_date, '%m/%d/%Y') position_effective_end_date,
        #     to_char(termination_date, '%m/%d/%Y') terimination_date,
        #     position_status,
        #     to_char(status_effective_date, '%m/%d/%Y') status_effective_date,
        #     to_char(status_effective_end_date, '%m/%d/%Y') status_effective_end_date,
        #     to_char(adjusted_service_date, '%m/%d/%Y') adjusted_service_date,
        #     archived_employee,
        #     position_id, primary_position, payroll_company_code,
        #     payroll_company_name, cip_code, worker_category_code,
        #     worker_category_descr, job_title_code, job_title_descr,
        #     home_cost_number_code, home_cost_number_descr,
        #     job_class_code, job_class_descr, job_descr, job_function_code,
        #     job_function_descr, room, bldg,
        #    	CASE
        #         WHEN bldg = '1' THEN 'Lentz Hall'
        #         WHEN bldg = '2' THEN 'Clausen Center'
        #         WHEN bldg = '3' THEN 'Straz Center'
        #         WHEN bldg = '4' THEN 'Hedberg Library'
        #         WHEN bldg = '5' THEN 'Johnson Arts Center'
        #         WHEN bldg = '6' THEN 'Todd Wehr Center'
        #         WHEN bldg = '7' THEN 'Tarble Athletic & Recreation Center'
        #         WHEN bldg = '11' THEN 'Madrigrano Hall'
        #         WHEN bldg = '13' THEN 'Tarble Hall'
        #         WHEN bldg = '15' THEN 'Siebert Chapel'
        #         WHEN bldg = '16' THEN 'Arena'
        #         ELSE ''
        #         END
        #     bldg_name,
        #     to_char(leave_of_absence_start_date, '%m/%d/%Y') leave_of_absence_start_date,
        #     to_char(leave_of_absence_return_date, '%m/%d/%Y') leave_of_absence_return_date,
        #     home_depart_num_code, home_depart_num_descr,
        #     supervisor_id, supervisor_firstname, supervisor_lastname,
        #     business_unit_code, business_unit_descr, reports_to_name,
        #     reports_to_position_id, reports_to_associate_id, employee_associate_id,
        #     management_position, supervisor_flag, long_title
        # FROM
        # cc_adp_rec
        # where (termination_date > TODAY - 30 or termination_date is null)
	    # AND date_stamp in
        #     (select datestamp from
        #         (select file_no, carthage_id, fullname, job_title_code, position_status,
        #         payroll_company_code||"-"||left(home_depart_num_code,3)||"-"||business_unit_code||"-"||job_title_code as pcn_aggr,
        #         hire_date, position_effective_date, termination_date,
        #         worker_category_code,  job_function_code, payroll_company_code,
        #         home_depart_num_code, business_unit_code,
        #         max(date_stamp) as datestamp
        #         from cc_adp_rec
        #         group by file_no, carthage_id, job_title_code, position_status,
        #         fullname, hire_date, position_effective_date,
        #         worker_category_code, job_function_code, payroll_company_code,
        #         business_unit_code, home_depart_num_code,
        #         termination_date
        #         order by fullname, position_effective_date desc
        #         ))
        # '''

        # print(last_adp_file)
        # data_result = engine.execute(cx_view_sql)
        #
        # ret = list(data_result.fetchall())
        #
        # with open(last_adp_file, 'a') as file_out:
        #     # with open("carthage_students.txt", 'a') as file_out:
        #     csvWriter = csv.writer(file_out, delimiter=',', dialect='myDialect')
        #     # encoded_rows = encode_rows_to_utf8(ret)
        #     for row in ret:
        #         csvWriter.writerow(row)
        # file_out.close()

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
            # returns additions or changes in new but not in original
            bigb = set(newfile) - set(oldfile)

            # Write differences to output file
            with open(adp_diff_file, 'wb') as file_out:
                # Write header row
                csvWriter = csv.writer(file_out)
                csvWriter.writerow(
                    ["file_number", "carth_id", "last_name", "first_name",
                     "middle_name", "salutation", "payroll_name",
                     "preferred_name", "birth_date", "gender",
                     "marital_status", "race", "race_descr", "ethnicity",
                     "ethnicity_id_meth", "personal_email",
                     "primary_address1", "primary_address2",
                     "primary_address3", "primary_city", "primary_state_code",
                     "primary_state_descr", "primary_zip", "primary_county",
                     "primary_country", "primary_country_code",
                     "primary_legal_address", "home_phone", "mobile_phone",
                     "work_phone", "wc_work_phone", "wc_work_email",
                     "use_work_for_notification", "legal_address1",
                     "legal_address2", "legal_address3", "legal_city",
                     "legal_state_code", "legal_state_description",
                     "legal_zip", "legal_county", "legal_country",
                     "legal_country_code", "ssn", "hire_date",
                     "hire_rehire_date", "rehire_date","pos_start_date",
                     "pos_effective_date", "pos_effective_end_date",
                     "termination_date", "position_status",
                     "status_effective_date", "status_eff_end_date",
                     "adj_service_date", "archived", "position_id",
                     "primary_position", "payroll_comp_code",
                     "payroll_comp_name", "cip", "worker_cat_code",
                     "worker_cat_descr", "job_title_code", "job_title_descr",
                     "home_cost_code", "home_cost_descr", "job_class_code",
                     "job_class_descr", "job_description", "job_function_code",
                     "job_function_description", "room_number",
                     "location_code", "location_description",
                     "leave_start_date", "leave_return_date",
                     "home_dept_code", "home_dept_descr", "supervisor_id",
                     "supervisor_fname", "supervisor_lname",
                     "business_unit_code", "business_unit_descr",
                     "reports_to_name","reports_to_pos_id",
                     "reports_to_assoc_id", "employee_assoc_id",
                     "management_position", "supervisor_flag", "long_title"])

                for line_no, line in enumerate(bigb):
                    x = line.split(',')
                    file_out.write(line)
                    # print('File = ' + x[0] + ', ID = ' + x[
                    #     1] + ', First = ' + x[3] + ', Last = ' + x[6])

            # close the files
            t1.close()
            t2.close()
            file_out.close()

        # scr.write('-------------------------------------------------------\n')
        # scr.write('-- CREATES APPLICATION FROM APD TO CX DATA \n')
        # scr.write('-------------------------------------------------------\n')
        #################################################################
        # STEP 2--
        # Open differences file and start loop through records
        #################################################################
        with open(adp_diff_file, 'r') as f:
            d_reader = csv.DictReader(f, delimiter=',')

            adpcount = 0
            ccadpcount = 0
            idcount = 0
            cvidcount = 0
            emailcount = 0
            phonecount = 0
            jobcount = 0
            profilecount = 0
            secondjobcount = 0

            for row in d_reader:
                print('--------------------------------------------------')
                print('carthid = {0}, Fullname = {1}'.format(row["carth_id"],
                                                         row["payroll_name"]))
                # print("Use as legal {0}".format(row["primary_legal_address"]))
                ethnic_code = {
                    'Not Hispanic or Latino': 'N',
                    'Hispanic or Latino': 'Y'
                }

                is_hispanic = ethnic_code.get(row["ethnicity"])
                if is_hispanic is None:
                    is_hispanic = ""
                # else:
                # print("Is Hispanic = " + str(is_hispanic))

                racecode = {
                    '1': 'WH',
                    '2': 'BL',
                    '4': 'AS',
                    '5': 'AM',
                    '6': 'AP',
                    '9': 'MU'
                }

                race = racecode.get(row["race"])
                if race is None:
                    race = ""
                # print("Race = " + str(race))

                # else:
                ##############################################################
                # STEP 2a--
                # Write entire row to cc_adp_rec table
                ##############################################################

                # Make sure we are not inserting the same record with no
                # change in cx.



                try:
                    q_cc_adp_rec = ("INSERT INTO cc_adp_rec (file_no, \
                    carthage_id, lastname, firstname, middlename, \
                    salutation, fullname, pref_name, birth_date, gender, \
                    marital_status, race, \
                    race_descr, hispanic, race_id_method, personal_email, \
                    primary_addr_line1, primary_addr_line2, \
                    primary_addr_line3, primary_addr_city, primary_addr_st, \
                    primary_addr_state, primary_addr_zip, \
                    primary_addr_county, primary_addr_country, \
                    primary_addr_country_code, primary_addr_as_legal, \
                    home_phone, cell_phone, work_phone, \
                    work_contact_phone, work_contact_email, \
                    work_contact_notification, \
                    legal_addr_line1, legal_addr_line2, legal_addr_line3, \
                    legal_addr_city, legal_addr_st, legal_addr_state, \
                    legal_addr_zip, legal_addr_county, legal_addr_country, \
                    legal_addr_country_code, ssn, hire_date, \
                    hire_rehire_date, rehire_date, position_start_date, \
                    position_effective_date, position_effective_end_date, \
                    termination_date, position_status, status_effective_date, \
                    status_effective_end_date, adjusted_service_date, \
                    archived_employee, position_id, primary_position, \
                    payroll_company_code, payroll_company_name, \
                    cip_code, worker_category_code, worker_category_descr, \
                    job_title_code, job_title_descr, home_cost_number_code, \
                    home_cost_number_descr, job_class_code, job_class_descr, \
                    job_descr, job_function_code, \
                    job_function_descr, room, bldg, bldg_name, \
                    leave_of_absence_start_date, \
                    leave_of_absence_return_date, \
                    home_depart_num_code, home_depart_num_descr, \
                    supervisor_id, supervisor_firstname, supervisor_lastname, \
                    business_unit_code, business_unit_descr, reports_to_name, \
                    reports_to_position_id, reports_to_associate_id, \
                    employee_associate_id, management_position, \
                    supervisor_flag, long_title, date_stamp) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,  \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
                    cc_adp_args = (row["file_number"], row["carth_id"],
                    row["last_name"],
                    row["first_name"], row["middle_name"], row["salutation"],
                    row["payroll_name"], row["preferred_name"],
                    fn_convert_date(row["birth_date"]), (row["gender"][:1]),
                    row["marital_status"], race,
                    row["race_descr"], is_hispanic,
                    row["ethnicity_id_meth"], row["personal_email"],
                    row["primary_address1"], row["primary_address2"],
                    row["primary_address3"], row["primary_city"],
                    row["primary_state_code"], row["primary_state_descr"],
                    row["primary_zip"], row["primary_county"],
                    row["primary_country"], row["primary_country_code"],
                    (row["primary_legal_address"][:1]),
                    fn_format_phone(row["home_phone"]),
                    fn_format_phone(row["mobile_phone"]),
                    fn_format_phone(row["work_phone"]),
                    fn_format_phone(row["wc_work_phone"]),
                    row["wc_work_email"],
                    (row["use_work_for_notification"][:1]),
                    row["legal_address1"],
                    row["legal_address2"], row["legal_address3"],
                    row["legal_city"], row["legal_state_code"],
                    row["legal_state_description"], row["legal_zip"],
                    row["legal_county"], row["legal_country"],
                    row["legal_country_code"], row["ssn"],
                    row["hire_date"],
                    fn_convert_date(row["hire_rehire_date"]),
                    fn_convert_date(row["rehire_date"]),
                    fn_convert_date(row["pos_start_date"]),
                    fn_convert_date(row["pos_effective_date"]),
                    fn_convert_date(row["pos_effective_end_date"]),
                    fn_convert_date(row["termination_date"]),
                    row["position_status"],
                    fn_convert_date(row["status_effective_date"]),
                    fn_convert_date(row["status_eff_end_date"]),
                    fn_convert_date(row["adj_service_date"]),
                    row["archived"], row["position_id"],
                    row["primary_position"], row["payroll_comp_code"],
                    row["payroll_comp_name"], row["cip"],
                    row["worker_cat_code"], row["worker_cat_descr"],
                    row["job_title_code"], row["job_title_descr"],
                    row["home_cost_code"], row["home_cost_descr"],
                    row["job_class_code"], row["job_class_descr"],
                    row["job_description"], row["job_function_code"],
                    row["job_function_description"], row["room_number"],
                    row["location_code"], row["location_description"],
                    fn_convert_date(row["leave_start_date"]),
                    fn_convert_date(row["leave_return_date"]),
                    row["home_dept_code"], row["home_dept_descr"],
                    row["supervisor_id"], row["supervisor_fname"],
                    row["supervisor_lname"], row["business_unit_code"].zfill(3),
                    row["business_unit_descr"], row["reports_to_name"],
                    row["reports_to_pos_id"], row["reports_to_assoc_id"],
                    row["employee_assoc_id"], row["management_position"],
                    row["supervisor_flag"], row["long_title"],
                    datetime.now())
                    # print(q_cc_adp_rec)
                    # print(cc_adp_args)
                    engine.execute(q_cc_adp_rec, cc_adp_args)
                    # ccadpcount =+ 1
                    # scr.write(q_cc_adp_rec + '\n' + str(cc_adp_args) + '\n');
                    # fn_write_log("Inserted data into cc_adp_rec table for "
                    #              + row["payroll_name"] + " ID = "
                    #              + row["carth_id"]);

                    # ccadpcount = ccadpcount + 1
                except Exception as e:
                    fn_write_error("Error in adptcx.py while inserting into"
                                   " cc_adp_rec.  Error = " + e.message)
                    continue
                    # print(e)



            # set destination directory for which the sql file
            # will be archived to
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
                # sendmail(
                #     settings.ADP_TO_EMAIL,settings.ADP_FROM_EMAIL,
                #     BODY, SUBJECT
                # )
                fn_write_log("There was no .sql output file to move.")
            else:
                # rename and move the file to the archive directory
                shutil.move(sqloutput, archived_destination)

            ##################################################################
            # The last step - move last to archive, rename new file to _last
            ##################################################################
            if not test:

                adptocx_archive = ('{0}adptocxlast_{1}.csv'.format(settings.ADP_CSV_ARCHIVED,datetimestr))
                shutil.move(last_adp_file, adptocx_archive)

                adptocx_rename = ('{0}ADPtoCXLast.csv'.format(settings.ADP_CSV_OUTPUT))
                shutil.move(new_adp_file, adptocx_rename)

            print("---------------------------------------------------------")
            print("ADP Count = " + str(adpcount))
            # print("CCADP Count = " + str(ccadpcount))
            # print("ID Count = " + str(idcount))
            # print("CVID Count = " + str(cvidcount))
            # print("Email Count = " + str(emailcount))
            # print("CELL Count = " + str(phonecount))
            # print("Job Count = " + str(jobcount))
            # print("Profile Count = " + str(profilecount))
            # print("Job2 Count = " + str(secondjobcount))

    except Exception as e:
        fn_write_error("Error in cc_adp_rec.py, Error = " + e.message)
        print(e)
    # finally:
    #     logging.shutdown()


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

    if database != 'cars' and database != 'train' and database != 'sandbox':
        print "database must be: 'cars' or 'train' or 'sandbox'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())
