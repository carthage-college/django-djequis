import os
import sys
import pysftp
import csv
import datetime
from datetime import date
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
#from djequis.adp.readadpfiles import finddifferences
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
        with open(new_adp_file) as fin1:
            with open(last_adp_file) as fin2:
                # Process input files
                read1 = csv.reader(fin1)
                read2 = csv.reader(fin2)

                # Skip headers
                read1.next()
                read2.next()
                diff_rows = (row1 for row1, row2 in zip(read1, read2) if
                             row1 != row2)

            # Open output file
            with open(adp_diff_file, 'w') as fout:
                csvWriter = csv.writer(fout, delimiter=',')
                # Write the output file header
                csvWriter.writerow(["FileNumber", "CarthID", "LastName",
                    "FirstName", "MiddleName", "Salutation", "PayrollName",
                    "PreferredName", "BirthDate", "Gender", "MaritalStatus",
                    "Race", "RaceDescr", "Ethnicity", "EthnicityIDMeth",
                    "PersonalEmail", "PrimaryAddress1", "PrimaryAddress2",
                    "PrimaryAddress3", "PrimaryCity", "PrimaryStateCode",
                    "PrimaryStateDescr", "PrimaryZip", "PrimaryCounty",
                    "PrimaryCountry", "PrimaryCountryCode", "PrimaryLegalAddress",
                    "HomePhone", "MobilePhone", "WorkPhone", "WCWorkPhone",
                    "WCWorkEmail", "UseWorkforNotification", "LegalAddress1",
                    "LegalAddress2", "LegalAddress3", "LegalCity", "LegalStateCode",
                    "LegalStateDescription", "LegalZip", "LegalCounty", "LegalCountry",
                    "LegalCountryCode", "SSN", "HireDate", "Hire_RehireDate",
                    "RehireDate", "PosStartDate", "PosEffectiveDate", "PosEffectiveEndDate",
                    "TerminationDate", "PositionStatus", "StatusEffectiveDate",
                    "StatusEffEndDate", "AdjServiceDate", "Archived", "PositionID",
                    "PrimaryPosition", "PayrollCompCode", "PayrollCompName", "CIP",
                    "WorkerCatCode", "WorkerCatDescr", "JobTitleCode", "JobTitleDescr",
                    "HomeCostCode", "HomeCostDescr", "JobClassCode", "JobClassDescr",
                    "JobDescription", "JobFunctionCode", "JobFunctionDescription",
                    "RoomNumber", "LocationCode",  "LocationDescription",
                    "LeaveStartDate",  "LeaveReturnDate", "HomeCostNumber2",
                    "PayrollCode2", "PositionEffDate2",  "PositionEndDate2",
                    "HomeCostNumber3",  "PayrollCode3", "PositionEffDate3",
                    "PositionEndDate3", "HomeCostNumber4", "PayrollCode4",
                    "PositionEffDate4",  "PositionEndDate4", "HomeDeptCode",
                    "HomeDeptDescr", "SupervisorID", "SupervisorFName",
                    "SupervisorLName"])
                writer = csv.writer(fout)
                # Write the output file
                writer.writerows(diff_rows)
        # Close opened files
        fin1.close()
        fin2.close()
        fout.close()

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
                supervisor_id, supervisor_firstname, supervisor_lastname, date_stamp)
                VALUES 
                ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},
                {11},{12},{13},{14},{15},{16},{17},{18},{19},{20},
                {21},{22},{23},{24},{25},{26},{27},{28},{29},{30},
                {31},{32},{33},{34},{35},{36},{37},{38},{39},{40},
                {41},{42},{43},{44},{45},{46},{47},{48},{49},{50},
                {51},{52},{53},{54},{55},{56},{57},{58},{59},{60},
                {61},{62},{63},{64},{65},{66},{67},{68},{69},{70},
                {71},{72},{73},{74},{75},{76},{77},{78},{79},{80},
                {81},{82},{83},{84},{85},{86},{87},{88},{89},{90},
                {91},{92},{93},TODAY);
                '''.format(row["FileNumber"], row["CarthID"], row["LastName"],
                row["FirstName"], row["MiddleName"], row["Salutation"],
                row["PayrollName"], row["PreferredName"], row["BirthDate"],
                row["Gender"], row["MaritalStatus"], row["Race"], row["RaceDescr"],
                row["Ethnicity"], row["EthnicityIDMeth"], row["PersonalEmail"],
                row["PrimaryAddress1"], row["PrimaryAddress2"], row["PrimaryAddress3"],
                row["PrimaryCity"], row["PrimaryStateCode"], row["PrimaryStateDescr"],
                row["PrimaryZip"], row["PrimaryCounty"], row["PrimaryCountry"],
                row["PrimaryCountryCode"], row["PrimaryLegalAddress"], row["HomePhone"],
                row["MobilePhone"], row["WorkPhone"], row["WCWorkPhone"], row["WCWorkEmail"],
                row["UseWorkforNotification"], row["LegalAddress1"], row["LegalAddress2"],
                row["LegalAddress3"], row["LegalCity"], row["LegalStateCode"],
                row["LegalStateDescription"], row["LegalZip"], row["LegalCounty"],
                row["LegalCountry"], row["LegalCountryCode"], row["SSN"], row["HireDate"],
                row["Hire_RehireDate"], row["RehireDate"], row["PosStartDate"],
                row["PosEffectiveDate"], row["PosEffectiveEndDate"], row["TerminationDate"],
                row["PositionStatus"], row["StatusEffectiveDate"], row["StatusEffEndDate"],
                row["AdjServiceDate"], row["Archived"], row["PositionID"], row["PrimaryPosition"],
                row["PayrollCompCode"], row["PayrollCompName"], row["CIP"], row["WorkerCatCode"],
                row["WorkerCatDescr"], row["JobTitleCode"], row["JobTitleDescr"], row["HomeCostCode"],
                row["HomeCostDescr"], row["JobClassCode"], row["JobClassDescr"],
                row["JobDescription"], row["JobFunctionCode"],
                row["JobFunctionDescription"], row["RoomNumber"], row["LocationCode"],
                row["LocationDescription"], row["LeaveStartDate"], row["LeaveReturnDate"],
                row["HomeCostNumber2"], row["PayrollCode2"], row["PositionEffDate2"],
                row["PositionEndDate2"], row["HomeCostNumber3"], row["PayrollCode3"],
                row["PositionEffDate3"], row["PositionEndDate3"], row["HomeCostNumber4"],
                row["PayrollCode4"], row["PositionEffDate4"], row["PositionEndDate4"],
                row["HomeDeptCode"], row["HomeDeptDescr"], row["SupervisorID"],
                row["SupervisorFName"], row["SupervisorLName"])
                print(q_cc_adp_rec)
                scr.write(q_cc_adp_rec+'\n');
                logger.info("Inserted into adp_rec table"+'\r\n');
                # do_sql(q_cc_adp_rec, key=DEBUG, earl=EARL)

                #################################################################
                # STEP 2b--
                # Do updates to id_rec
                #################################################################

                # Insert or update as needed to ID_rec
                q_insert_id_rec = '''
                INSERT INTO id_rec
                    (fullname, lastname, firstname, middlename, addr_line1,
                    addr_line2, addr_line3, city, st, zip, ctry, AA, ss_no,
                    Decsd)
                VALUES({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},"PERM")
                ''' .format(row["PayrollName"], row["LastName"], row["FirstName"],
                            row["MiddleName"], row["PrimaryAddress1"], row["PrimaryAddress2"],
                            row["PrimaryAddress3"], row["PrimaryCity"],
                row["PrimaryStateCode"], row["PrimaryZip"], row["PrimaryCountryCode"],
                row["SSN"], "")
                print(q_insert_id_rec)
                scr.write(q_insert_id_rec+'\n');
                logger.info("Inserted into id_rec table"+'\r\n');
                # do_sql(q_insert_id_rec, key=DEBUG, earl=EARL)
                # sql = sql & " upd_date, ofc_add_by, correct_addr, prev_name_id, " \
                #             "inquiry_no"
                # sql = sql & ") values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                    #also need to deal with address changes
                    # sAddrChg = CheckAddress(ID, FullName, Addr1, Addr2, Addr3,
                    # City, State, Zip, Ctry)
                    # If sAddrChg = "True" Then Update_Addr()

                if row["PersonalEmail"] != '':
                    # Insert email into aa_rec
                    q_insert_aa_rec = '''
                    INSERT INTO aa_rec
                        (id, aa, beg_date, "line1)
                        VALUES ({0}, "EML2", TODAY, "{1}");
                    ''' .format(row["CarthID"], row["PersonalEmail"])
                    print(q_insert_aa_rec)
                    scr.write(q_insert_aa_rec+'\n');
                    logger.info("Inserted into aa_rec table"+'\r\n');
                    #do_sql(q_insert_aa_cell, key=DEBUG, earl=EARL)
                # else:
                #     print("No email from ADP")
                #
                #Check to update phone in aa_rec
    
                #################################################################
                # STEP 2c--
                # Do updates to profile_rec
                #################################################################
    
    
                #################################################################
                # STEP 2d--
                # Do updates to cvid_rec
                #################################################################
    
    
                #################################################################
                # STEP 2e--
                # Do updates to job_rec
                #################################################################
                    # Must account for Division, Dept
                    # use PCN Codes to tie employee to job number
                    # validate a number of fields as needed
                    # add GL Func code to func_area in position table
                    # if there is a secondary job record, do the same..

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

    except Exception as e:
        print(e)


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
