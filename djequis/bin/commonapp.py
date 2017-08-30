import os
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import timedelta
import time
from time import gmtime, strftime
import argparse
import uuid
from sqlalchemy import text

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

EARL = settings.INFORMIX_EARL
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload Common Application data to CX
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
start_time = time.time()
def main():
    # Establish mySQL database connection
    cursor = connections['admissions_pce'].cursor()

    #########################################################################################
    # set directory and filename
    #########################################################################################
    filename=('{}carthage_applications.txt'.format(
        settings.COMMONAPP_CSV_OUTPUT
    ))

    # write out the .sql file
    scr = open("commonapp_output.sql", "a")

    # creating header in sql script
    scr.write('--------------------------------------------------------------------------------\n' )
    scr.write('-- COMMON APPLICATION - RESULTS IN TEMP TABLE \n' )
    scr.write('--------------------------------------------------------------------------------\n' )

    with open(filename, 'rb') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            print([col+'='+row[col] for col in reader.fieldnames])

            # create UUID
            temp_uuid = (uuid.uuid4())
            print ('UUID: {0}'.format(temp_uuid))

            scr.write('---------------------------------------------------------------------------------------------\n')
            scr.write('-- START INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('---------------------------------------------------------------------------------------------\n')

            if row["feeWaiverCode"] == '':
                paymentMethod = 'CREDIT'
                waiverCode = ''
            else:
                paymentMethod = 'WAIVER'
                waiverCode = row["feeWaiverCode"]

            print ('Payment Method: {0}'.format(paymentMethod))
            print ('Waiver Code: {0}'.format(waiverCode))

            # insert into apptmp_rec
            q_create_app = '''
            INSERT INTO apptmp_rec
            (add_date, add_tm, app_source, stat, reason_txt, payment_method, waiver_code)
            VALUES (TODAY, TO_CHAR(CURRENT, '%H%M'), "WEBA", "H", "{0}",
            "{1}", "{2}");
            ''' .format(temp_uuid, paymentMethod, waiverCode)
            print (q_create_app)
            scr.write(q_create_app+'\n');
            do_sql(q_create_app, earl=EARL)

            ##################################################################################
            # fetch id from apptmp_no which is used threw out queries
            #################################################################################
            lookup_apptmp_no = '''
            SELECT
                apptmp_no
            FROM
                apptmp_rec
            WHERE
                reason_txt = "{0}";
            ''' .format(temp_uuid)
            sqlresult = do_sql(lookup_apptmp_no, earl=EARL)
            print (lookup_apptmp_no)
            scr.write(lookup_apptmp_no+'\n');
            results = sqlresult.fetchone()
            # set apptmp_no
            apptmp_no = (results[0])
            print ('Apptmp No: {0}'.format(results[0]))
            
            ##################################################################################
            # fetch id from app_voucher on mySQL dB (admissions_pce).
            # insert into app_vouchers_users on mySQL dB
            ##################################################################################
            if row["feeWaiverCode"] != '':
                q_match = '''
                    SELECT id
                    FROM app_vouchers
                    WHERE NOW() < expiration
                    AND REPLACE(code,"-","") = "{0}"
                ''' .format(row["feeWaiverCode"].replace('-', ''))
                print (q_match)
                scr.write(q_match+'\n');
                cursor.execute(q_match)
                voucher_result = cursor.fetchone()
                voucher_id = (voucher_result[0])

                q_update_voucher = '''
                INSERT INTO app_voucher_users (voucher_id, app_id, submitted_on)
                VALUES ({0}, {1}, NOW())
                ''' .format(voucher_id, apptmp_no)
                print (q_update_voucher)
                scr.write(q_update_voucher+'\n');
                cursor.execute(q_update_voucher)
            print ("There were no waiver codes for this application")
            scr.write("--There were no waiver codes for this application"+'\n');

            q_create_id = '''
            INSERT INTO app_idtmp_rec
            (id, firstname, lastname, suffixname, cc_username, cc_password, addr_line1,
            addr_line2, city, st, zip, ctry, phone, ss_no, aa, add_date, ofc_add_by,
            upd_date, purge_date, prsp_no, name_sndx, correct_addr, decsd, valid)
            VALUES ({0}, "{1}", "{2}", "{3}", "{4}", "{0}", "{5}", "{6}", "{7}",
            "{8}", "{9}", "{10}", "{11}", {12}, "PERM", TODAY, "ADMS", TODAY,
            TODAY + 2 UNITS YEAR, "0", "", "Y", "N", "Y");
            ''' .format(apptmp_no, row["firstName"], row["lastName"],
            row["suffix"], row["emailAddress"], row["permanentAddress1"],
            row["permanentAddress2"], row["permanentAddressCity"],
            row["permanentAddressState"], row["permanentAddressZip"],
            row["permanentAddressCountry"],
            row["preferredPhoneNumber"].replace('+1.', ''), row["ssn"])
            print (q_create_id)
            scr.write(q_create_id+'\n');
            do_sql(q_create_id, earl=EARL)

            ##################################################################################
            # The Y/N value of contactConsent may seem a little backwards intuitively.
            # Y = The student has opted out meaning Carthage does NOT have permission to text
            # N = The student has opted in meaning Carthage does have permission to text
            #################################################################################
            if row["preferredPhone"] == 'Mobile':
                if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                    contactConsent = 'N'
                elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                    contactConsent = 'Y'
                q_insert_aa_cell = '''
                INSERT INTO app_aatmp_rec
                (id, aa, beg_date, phone, opt_out)
                VALUES ({0}, "CELL", TODAY, "{1}", "{2}");
                ''' .format(apptmp_no, row["preferredPhoneNumber"].replace('+1.', ''),
                row["contactConsent"])
                print (q_insert_aa_cell)
                scr.write(q_insert_aa_cell+'\n');
                do_sql(q_insert_aa_cell, earl=EARL)
            # not sure about the indent here, Also, this changed from and to or
            if row["alternatePhoneAvailable"] != '' and row["alternatePhoneAvailable"] != 'N':
                altType = 'CELL'
                if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                    contactConsent = 'N'
                elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                    contactConsent = 'Y'
                if row["alternatePhoneAvailable"] == 'Home':
                    altType = 'HOME'
                    # insert into app_aatmp_rec (CELL)
                q_insert_aa_cell = '''
                INSERT INTO app_aatmp_rec
                (id, aa, beg_date, phone, opt_out)
                VALUES ({0}, "{1}", TODAY, "{2}", "{3}");
                ''' .format(apptmp_no, altType, row["alternatePhoneNumber"].replace('+1.', ''),
                row["contactConsent"])
                print (q_insert_aa_cell)
                scr.write(q_insert_aa_cell+'\n');
                do_sql(q_insert_aa_cell, earl=EARL)

            q_create_site = '''
            INSERT INTO app_sitetmp_rec
            (id, home, site, beg_date)
            VALUES ({0}, "Y", "CART", TODAY);
            ''' .format(apptmp_no)
            print (q_create_site)
            scr.write(q_create_site+'\n');
            do_sql(q_create_site, earl=EARL)

            # determine the type of studentStatus and Hours Enrolled
            if row["studentStatus"] == 'Full Time' or row["transferStudentStatus"] == 'Full Time':
                studentStatus = 'TRAD'
                intendHoursEnrolled = 16
            elif row["studentStatus"] == 'Part Time' or row["transferStudentStatus"] == 'Part Time':
                studentStatus = 'TRAP'
                intendHoursEnrolled = 4

            # fetch preferredStartTerm from Common App data (Fall 2018, Spring 2018, J-Term 2018)
            preferredStartTerm = row["preferredStartTerm"]
            if len(row["transferPreferredStartTerm"]):
                preferredStartTerm = row["transferPreferredStartTerm"]
            # spliting preferredStartTerm
            planArray = preferredStartTerm.split(' ')
            # set planEnrollYear to Year 
            planEnrollYear = planArray[1]
            # create school session dict
            session = {
                'Fall': 'RA',
                'J-Term': 'RB',
                'Spring': 'RC'
            }
            # create planEnrollSession from value in dictionary
            planEnrollSession = session[planArray[0]]

            print ('Plan array: {0}'.format(planArray))
            print ('Plan enroll Year: {0}'.format(planEnrollYear))
            print ('Plan enroll Session: {0}'.format(planEnrollSession))
            print ('Student Type: {0}'.format(row["studentType"]))
            
            # determine the type of studentType
            if row["studentType"] == 'FY' and row["freshmanNursing"] == 'Yes':
                studentType = 'FN'
                transfer = 'N'
            elif row["studentType"] == 'FY':
                studentType = 'FF'
                transfer = 'N'
            elif row["studentType"] == 'TR' and row["transferFreshmanNursing"] == 'Yes':
                studentType = 'FN'
                transfer = 'Y'
            elif row["studentType"] == 'TR':
                studentType = 'UT'
                transfer = 'Y'
            print ('Freshman Nursing: {0}'.format(row["freshmanNursing"]))

            major1 = row["major1"].replace("ADM-MAJOR-", "").strip()
            if len(row["transferMajor1"]):
                major1 = row["transferMajor1"].replace("ADM-MAJOR-", "").strip()
            major2 = row["major2"].replace("ADM-MAJOR-", "").strip()
            if len(row["transferMajor2"]):
                major2 = row["transferMajor2"].replace("ADM-MAJOR-", "").strip()
            major3 = row["major3"].replace("ADM-MAJOR-", "").strip()
            if len(row["transferMajor3"]):
                major3 = row["transferMajor3"].replace("ADM-MAJOR-", "").strip()

            print ('Denomination Code: {0}'.format(row["religiousPreference"]))
            parent_marital = {
                'Married': 'M',
                'Separated': 'T',
                'Divorced': 'D',
                'Widowed': 'W',
                'Never Married': 'S',
                '': ''
            }

            if row["parent1Type"] == 'Father':
                parent1 = 'F'
            if row["parent1Type"] == 'Mother':
                parent1 = 'M'
            if row["parent2Type"] == 'Mother':
                parent2 = 'M'
            if row["parent2Type"] == 'Father':
                parent2 = 'F'

            liveWith = {
                'Both Parents': 'B',
                'Parent 1': parent1,
                'Parent 2': parent2,
                'Legal Guardian': 'G',
                'Other': 'O',
                'Ward of the Court/State': 'O' 
            }

            # create variables for the Religious Preference based on the dictionary
            try:
                live_with = liveWith[row["permanentHome"]]
                if live_with == 'O':
                    otherLivingSituation = row["otherLivingSituation"]
            except KeyError as e:
                live_with = 'O'

            # insert into app_admtmp_rec
            q_create_adm = '''
            INSERT INTO app_admtmp_rec
            (id, primary_app, plan_enr_sess, plan_enr_yr, intend_hrs_enr,
            trnsfr, cl, add_date, parent_contr, enrstat, rank, wisconsin_coven,
            emailaddr, prog, subprog, upd_date, act_choice, stuint_wt,
            jics_candidate, major, major2, major3, app_source, pref_name, felony,
            discipline, parnt_mtlstat, live_with, live_with_other, vet_ben)
            VALUES ({0}, "Y", "{1}", {2}, "{3}", "{4}", "{5}", TODAY, "0.00",
            "", "0", "", "{6}", "UNDG", "{7}", TODAY, "", "0", "N", "{8}",
            "{9}", "{10}", "C", "{11}", "{12}", "{13}", "{14}", "{15}", "{16}", {17});
            ''' .format(apptmp_no, planEnrollSession, planEnrollYear,
            intendHoursEnrolled, transfer, studentType, row["emailAddress"],
            studentStatus, major1, major2, major3, row["preferredName"],
            row["criminalHistory"], row["criminalHistoryExplanation"],
            row["schoolDiscipline"], row["parentsMaritalStatus"], live_with,
            otherLivingSituation)
            print (q_create_adm)
            scr.write(q_create_adm+'\n');
            do_sql(q_create_adm, earl=EARL)

            if row["alternateAddressAvailable"] == 'Y':
                q_insert_aa_mail = '''
                INSERT INTO app_aatmp_rec
                (line1, line2, city, st, zip, ctry, id, aa, beg_date)
                VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", {6}, "MAIL",
                TODAY);
                ''' .format(row["currentAddress1"], row["currentAddress2"],
                row["currentAddressCity"], row["currentAddressState"],
                row["currentAddressZip"], row["currentAddressCountry"],
                apptmp_no)
                print (q_insert_aa_mail)
                scr.write(q_insert_aa_mail);
                do_sql(q_insert_aa_mail, earl=EARL)
            else:
                print ("There were no alternate addresses for this application.")
                scr.write('--There were no alternate addresses for this application.\n\n');

            ##################################################################################
            # The Y/N value of contactConsent may seem a little backwards intuitively.
            # Y = The student has opted out meaning Carthage does NOT have permission to text
            # N = The student has opted in meaning Carthage does have permission to text
            #################################################################################
            # determine the type of contactConsent

            #########################################################################################
            # If there are any schools attended by a student that are not NULL it will insert records
            #########################################################################################
            if row["schoolLookupCeebCode"] != '' and row["schoolLookupCeebName"] != '':
                if row["graduationDate"] == '':
                    graduationDate = ''
                else: # formatting the graduationDate
                    graduationDate = datetime.datetime.strptime(row["graduationDate"], '%m/%Y').strftime('%Y-%m-01')
                if row["entryDate"] == '':
                    entryDate = ''
                else: # formatting the entryDate
                    entryDate = datetime.datetime.strptime(row["entryDate"], '%m/%Y').strftime('%Y-%m-01')
                if row["exitDate"] == '':
                    exitDate = ''
                else: # formatting the exitDate
                    exitDate = datetime.datetime.strptime(row["exitDate"], '%m/%Y').strftime('%Y-%m-01')

            # insert into app_idtmp_rec
                q_create_school = '''
                INSERT INTO app_edtmp_rec
                (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date, stu_id,
                sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry, acad_trans)
                VALUES ({0}, {1}, "{2}", "{3}", "{4}", TO_DATE("{5}", "%Y-%m-%d"),
                TO_DATE("{6}", "%Y-%m-%d"), TO_DATE("{7}", "%Y-%m-%d"), 0, 0, 0,
                0, 0, "{8}", "hs", "HS", "N");
            ''' .format(apptmp_no, row["schoolLookupCeebCode"], row["schoolLookupCeebName"],
                row["schoolLookupCity"], row["schoolLookupState"], graduationDate,
                entryDate, exitDate, row["schoolLookupZip"])
                print (q_create_school)
                scr.write(q_create_school);
                scr.write("--Executing create school qry");
                do_sql(q_create_school, earl=EARL)
                #hsdebug = do_sql(q_create_school, earl=EARL)
                #print ('HS Debug: {0}'.format(hsdebug))

            ##################################################################################
            # If there are any secondary schools attended by a student it will insert records
            ##################################################################################
            # insert into app_proftmp_rec
            if row["otherSchoolNumber"] != '' and int(row["otherSchoolNumber"]) > 0:
                for schoolNumber in range(2, int(row["otherSchoolNumber"])+1):
                    print ('Other School Number: {0}'.format(row["otherSchoolNumber"]))
                    print ('school num: {0}'.format(schoolNumber))
                    if row['secondarySchool'+str(schoolNumber)+'FromDate'] == '':
                        fromDate = ''
                    else: # formatting the fromDate
                        fromDate = datetime.datetime.strptime(row["fromDate"], '%m/%Y').strftime('%Y-%m-01')
                    if row['secondarySchool'+str(schoolNumber)+'ToDate'] == '':
                        toDate = ''
                    else: # formatting the toDate
                        toDate = datetime.datetime.strptime(row["toDate"], '%m/%Y').strftime('%Y-%m-01')

                    q_create_other_school = '''
                    INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                    VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                    TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "hs", "HS", "N");
                ''' .format(apptmp_no, row['secondarySchool'+str(schoolNumber)+'CeebCode'],
                    row['secondarySchool'+str(schoolNumber)+'CeebName'],
                    row['secondarySchool'+str(schoolNumber)+'City'],
                    row['secondarySchool'+str(schoolNumber)+'State'],
                    fromDate, toDate,
                    row['secondarySchool'+str(schoolNumber)+'Zip'])
                    print (q_create_other_school)
                    scr.write(q_create_other_school+'\n\n');
                    scr.write("--Executing other school qry"+'\n\n');
                    do_sql(q_create_other_school, earl=EARL)

            ##########################################################################################
            # If there are any secondary schools attended by a transfer student it will insert records
            ##########################################################################################
            # insert into app_proftmp_rec
            if row["transferSecondarySchoolsAttendedNumber"] != '' and int(row["transferSecondarySchoolsAttendedNumber"]) > 0:
                for schoolNumber in range(1, int(row["transferSecondarySchoolsAttendedNumber"])+1):
                    print ('Transfer Other School Number: {0}'.format(row["transferSecondarySchoolsAttendedNumber"]))
                    print ('school num: {0}'.format(schoolNumber))
                    if row['transferSecondarySchool'+str(schoolNumber)+'FromDate'] == '':
                        fromDate = ''
                    else: # formatting the fromDate
                        fromDate = datetime.datetime.strptime(row['transferSecondarySchool'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                    if row['transferSecondarySchool'+str(schoolNumber)+'ToDate'] == '':
                        toDate = ''
                    else: # formatting the toDate
                        toDate = datetime.datetime.strptime(row['transferSecondarySchool'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')

                    q_create_transfer_other_school = '''
                    INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                    VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                    TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "hs", "HS", "N");
                ''' .format(apptmp_no, row['transferSecondarySchool'+str(schoolNumber)+'CeebCode'],
                    row['transferSecondarySchool'+str(schoolNumber)+'CeebName'],
                    row['transferSecondarySchool'+str(schoolNumber)+'City'],
                    row['transferSecondarySchool'+str(schoolNumber)+'State'],
                    fromDate, toDate,
                    row['transferSecondarySchool'+str(schoolNumber)+'Zip'])
                    print (q_create_transfer_other_school)
                    scr.write(q_create_transfer_other_school+'\n\n');
                    scr.write("--Executing transfer other school qry"+'\n\n');
                    do_sql(q_create_transfer_other_school, earl=EARL)

            ##################################################################################
            # If there are any colleges attended by a student it will insert records
            ##################################################################################
            # insert into app_proftmp_rec
            if row["collegesAttendedNumber"] != '' and int(row["collegesAttendedNumber"]) > 0:
                for schoolNumber in range(1, int(row["collegesAttendedNumber"])+1):
                    print ('College School Number: {0}'.format(row["collegesAttendedNumber"]))
                    print ('school num: {0}'.format(schoolNumber))
                    if row['college'+str(schoolNumber)+'FromDate'] == '':
                        fromDate = ''
                    else: # formatting the fromDate
                        fromDate = datetime.datetime.strptime(row['college'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                    if row['college'+str(schoolNumber)+'ToDate'] == '':
                        toDate = ''
                    else: # formatting the toDate
                        toDate = datetime.datetime.strptime(row['college'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')

                    q_create_college_school = '''
                    INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                    VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                    TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "ac",
                    "COL", "N");
                ''' .format(apptmp_no, row['college'+str(schoolNumber)+'CeebCode'],
                    row['college'+str(schoolNumber)+'CeebName'],
                    row['college'+str(schoolNumber)+'City'],
                    row['college'+str(schoolNumber)+'State'],
                    fromDate, toDate,
                    row['college'+str(schoolNumber)+'Zip'])
                    print (q_create_college_school)
                    scr.write(q_create_college_school+'\n\n');
                    scr.write("--Executing Colleges attended qry"+'\n\n');
                    do_sql(q_create_college_school, earl=EARL)

            ##################################################################################
            # If there are any colleges attended by a transfer student it will insert records
            ##################################################################################
            # insert into app_proftmp_rec
            if row["transferCollegesAttendedNumber"] != '' and int(row["transferCollegesAttendedNumber"]) > 0:
                for schoolNumber in range(1, int(row["transferCollegesAttendedNumber"])+1):
                    print ('Transfer College School Number: {0}'.format(row["transferCollegesAttendedNumber"]))
                    print ('school num: {0}'.format(schoolNumber))
                    if row['transferCollege'+str(schoolNumber)+'FromDate'] == '':
                        fromDate = ''
                    else: # formatting the fromDate
                        fromDate = datetime.datetime.strptime(row['transferCollege'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                    if row['transferCollege'+str(schoolNumber)+'ToDate'] == '':
                        toDate = ''
                    else: # formatting the toDate
                        toDate = datetime.datetime.strptime(row['transferCollege'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')

                    q_create_transfer_college_school = '''
                    INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                    VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                    TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "ac",
                    "COL", "N");
                ''' .format(apptmp_no, row['transferCollege'+str(schoolNumber)+'CeebCode'],
                    row['transferCollege'+str(schoolNumber)+'CeebName'],
                    row['transferCollege'+str(schoolNumber)+'City'],
                    row['transferCollege'+str(schoolNumber)+'State'],
                    fromDate, toDate,
                    row['transferCollege'+str(schoolNumber)+'Zip'])
                    print (q_create_transfer_college_school)
                    scr.write(q_create_transfer_college_school+'\n\n');
                    scr.write("--Executing transfer colleges attended qry"+'\n\n');
                    do_sql(q_create_transfer_college_school, earl=EARL)

            ##################################################################################
            # If there are no relatives in the application then nothing is inserted
            ##################################################################################
            if row["relativesAttended"] == 'Yes':
                # set Relative Graduation Year
                relative1GradYear1 = row["relative1GradYear1"].strip()
                if len(row["transferRelative1GradYear1"]):
                    relative1GradYear1 = row["transferRelative1GradYear1"].strip()
                relative2GradYear1 = row["relative2GradYear1"].strip()
                if len(row["transferRelative2GradYear1"]):
                    relative2GradYear1 = row["transferRelative2GradYear1"].strip()
                relative3GradYear1 = row["relative3GradYear1"].strip()
                if len(row["transferRelative3GradYear1"]):
                    relative3GradYear1 = row["transferRelative3GradYear1"].strip()
                relative4GradYear1 = row["relative4GradYear1"].strip()
                if len(row["transferRelative4GradYear1"]):
                    relative4GradYear1 = row["transferRelative4GradYear1"].strip()
                relative5GradYear1 = row["relative5GradYear1"].strip()
                if len(row["transferRelative5GradYear1"]):
                    relative5GradYear1 = row["transferRelative5GradYear1"].strip()

                q_alumni = ""
                # insert relative1 if there are any coming in from Common App
                if row["relative1FirstName"].strip():
                    q_alumni = '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip)
                    VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                ''' .format(apptmp_no, row["relative1FirstName"] + ' ' + row["relative1LastName"],
                    row["relative1GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
                    do_sql(q_alumni, earl=EARL)

                # insert srelative1 if there are any coming in from Common App
                if row["relative2FirstName"].strip():
                    q_alumni = '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip)
                    VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                ''' .format(apptmp_no, row["relative2FirstName"] + ' ' + row["relative2LastName"],
                    row["relative2GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
                    do_sql(q_alumni, earl=EARL)

                # insert srelative1 if there are any coming in from Common App
                if row["relative3FirstName"].strip():
                    q_alumni =  '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip)
                    VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                ''' .format(apptmp_no, row["relative3FirstName"] + ' ' + row["relative3LastName"],
                    row["relative3GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
                    do_sql(q_alumni, earl=EARL)

                # insert srelative1 if there are any coming in from Common App
                if row["relative4FirstName"].strip():
                    q_alumni =  '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip)
                    VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                ''' .format(apptmp_no, row["relative4FirstName"] + ' ' + row["relative4LastName"],
                    row["relative4GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
                    do_sql(q_alumni, earl=EARL)

                # insert srelative1 if there are any coming in from Common App
                if row["relative5FirstName"].strip():
                    q_alumni =  '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip)
                    VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                ''' .format(apptmp_no, row["relative5FirstName"] + ' ' + row["relative5LastName"],
                    row["relative5GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
                    do_sql(q_alumni, earl=EARL)
            else:  
                print ("There were no relatives to insert")
                scr.write('--There were no relatives for this application.\n\n');

            ##################################################################################
            # If there are no siblings in the application then nothing is inserted
            ##################################################################################
            if row["numberOfSiblings"] > 0:
                # set dictionary for Sibling education level
                educationLevel = {
                    'None': 'None',
                    'Some grade school': 'Elem',
                    'Completed grade school': 'HS',
                    'Some secondary school': 'HS',
                    'Graduated from secondary school': 'HS',
                    'Some trade school or community college': 'Juco',
                    'Graduated from trade school or community college': 'Juco',
                    'Some college': 'Coll',
                    'Graduated from college': 'Bach',
                    'Graduate school': 'Mast'
                }
                # create variables for the Siblings education level based on the dictionary
                for k, v in educationLevel.items():
                    if row["sibling1EducationLevel"] == k:
                        sibling1EducationLevel = (v)
                    if row["sibling2EducationLevel"] == k:
                        sibling2EducationLevel = (v)
                    if row["sibling3EducationLevel"] == k:
                        sibling3EducationLevel = (v)
                    if row["sibling4EducationLevel"] == k:
                        sibling4EducationLevel = (v)
                    if row["sibling5EducationLevel"] == k:
                        sibling5EducationLevel = (v)

                # building insert query for Siblings Information
                if row["sibling1FirstName"].strip():
                    # insert sibling1 if there are any coming in from Common App
                    q_sibing_name = '''
                    INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                    phone_ext, aa, zip, prim, addr_line2, suffix)
                    VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                    "{4}");
                ''' .format(apptmp_no, row["sibling1FirstName"] + ' ' + row["sibling1LastName"],
                    row["sibling1Age"], row["sibling1CollegeCeebName"],
                    sibling1EducationLevel)
                    print (q_sibing_name)
                    scr.write(q_sibing_name+'\n\n');
                    do_sql(q_sibing_name, earl=EARL)

                    # insert sibling2 if there are any coming in from Common App
                    if row["sibling2FirstName"].strip():
                        q_sibing_name = '''
                        INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                        phone_ext, aa, zip, prim, addr_line2, suffix)
                        VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                        "{4}");
                    ''' .format(apptmp_no, row["sibling2FirstName"] + ' ' + row["sibling2LastName"],
                        row["sibling2Age"], row["sibling2CollegeCeebName"],
                        sibling2EducationLevel)
                        print (q_sibing_name)
                        scr.write(q_sibing_name+'\n\n');
                        do_sql(q_sibing_name, earl=EARL)

                    # insert sibling3 if there are any coming in from Common App
                    if row["sibling3FirstName"].strip():
                        q_sibing_name = '''
                        INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                        phone_ext, aa, zip, prim, addr_line2, suffix)
                        VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                        "{4}");
                    ''' .format(apptmp_no, row["sibling3FirstName"] + ' ' + row["sibling3LastName"],
                        row["sibling3Age"], row["sibling3CollegeCeebName"],
                        sibling3EducationLevel)
                        print (q_sibing_name)
                        scr.write(q_sibing_name+'\n\n');
                        do_sql(q_sibing_name, earl=EARL)

                    # insert sibling4 if there are any coming in from Common App
                    if row["sibling4FirstName"].strip():
                        q_sibing_name = '''
                        INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                        phone_ext, aa, zip, prim, addr_line2, suffix)
                        VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                        "{4}");
                    ''' .format(apptmp_no, row["sibling4FirstName"] + ' ' + row["sibling4LastName"],
                        row["sibling4Age"], row["sibling4CollegeCeebName"],
                        sibling4EducationLevel)
                        print (q_sibing_name)
                        scr.write(q_sibing_name+'\n\n');
                        do_sql(q_sibing_name, earl=EARL)

                    # insert sibling5 if there are any coming in from Common App
                    if row["sibling5FirstName"].strip():
                        q_sibing_name = '''
                        INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                        phone_ext, aa, zip, prim, addr_line2, suffix)
                        VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                        "{4}");
                    ''' .format(apptmp_no, row["sibling5FirstName"] + ' ' + row["sibling5LastName"],
                        row["sibling5Age"], row["sibling5CollegeCeebName"],
                        sibling5EducationLevel)
                        print (q_sibing_name)
                        scr.write(q_sibing_name+'\n\n');
                        do_sql(q_sibing_name, earl=EARL)
            else:  
                print ("There were no siblings to insert.")
                scr.write('--There were no siblings for this application.\n\n');

            fatherIndex = 1
            motherIndex = 2
            if row["parent1Type"] == 'Mother':
                fatherIndex = 2
                motherIndex = 1
            print ('fatherIndex: {0}'.format(fatherIndex))
            print ('motherIndex: {0}'.format(motherIndex))
            q_insert_partmp_rec = '''
                INSERT INTO partmp_rec (id, app_no, f_first_name, f_last_name,
                f_addr_line1, f_addr_line2, f_city, f_st, f_zip, f_ctry,
                f_college, f_deg_earn, f_title, f_suffix, f_email, f_phone,
                f_job, f_employer, m_first_name, m_last_name, m_addr_line1,
                m_addr_line2, m_city, m_st, m_zip, m_ctry, m_college,
                m_deg_earn, m_title, m_suffix, m_email, m_phone, m_job,
                m_employer, g_first_name, g_last_name, g_addr_line1, g_addr_line2,
                g_city, g_st, g_zip, g_ctry, g_college, g_deg_earn, g_title,
                g_suffix, g_email, g_phone, g_job, g_employer)
                VALUES ({0}, 0, "{1}", "{2}", "{3}", "{4}", "{5}", "{6}",
                "{7}", "{8}", "{9}", "{10}", "{11}", "{12}", "{13}", "{14}",
                "{15}", "{16}", "{17}", "{18}", "{19}", "{20}", "{21}", "{22}",
                "{23}", "{24}", "{25}", "{26}", "{27}", "{28}", "{29}", "{30}",
                "{31}", "{32}", "{33}", "{34}", "{35}", "{36}", "{37}", "{38}",
                "{39}", "{40}", "{41}", "{42}", "{43}", "{44}", "{45}", "{46}",
                "{47}", "{48}");
            ''' .format(apptmp_no,
                    row['parent'+str(fatherIndex)+'FirstName'],
                    row['parent'+str(fatherIndex)+'LastName'],
                    row['parent'+str(fatherIndex)+'Address1'],
                    row['parent'+str(fatherIndex)+'Address2'],
                    row['parent'+str(fatherIndex)+'AddressCity'],
                    row['parent'+str(fatherIndex)+'AddressState'],
                    row['parent'+str(fatherIndex)+'AddressZip'],
                    row['parent'+str(fatherIndex)+'AddressCountry'],
                    row['parent'+str(fatherIndex)+'College1NameCeebName'],
                    row['parent'+str(fatherIndex)+'College1Degree1'],
                    row['parent'+str(fatherIndex)+'Title'],
                    row['parent'+str(fatherIndex)+'Suffix'],
                    row['parent'+str(fatherIndex)+'Email'],
                    row['parent'+str(fatherIndex)+'Phone'].replace('+1.', ''),
                    row['parent'+str(fatherIndex)+'Occupation'],
                    row['parent'+str(fatherIndex)+'Employer'],
                    row['parent'+str(motherIndex)+'FirstName'],
                    row['parent'+str(motherIndex)+'LastName'],
                    row['parent'+str(motherIndex)+'Address1'],
                    row['parent'+str(motherIndex)+'Address2'],
                    row['parent'+str(motherIndex)+'AddressCity'],
                    row['parent'+str(motherIndex)+'AddressState'],
                    row['parent'+str(motherIndex)+'AddressZip'],
                    row['parent'+str(motherIndex)+'AddressCountry'],
                    row['parent'+str(motherIndex)+'College1NameCeebName'],
                    row['parent'+str(motherIndex)+'College1Degree1'],
                    row['parent'+str(motherIndex)+'Title'],
                    row['parent'+str(motherIndex)+'Suffix'],
                    row['parent'+str(motherIndex)+'Email'],
                    row['parent'+str(motherIndex)+'Phone'].replace('+1.', ''),
                    row['parent'+str(motherIndex)+'Occupation'],
                    row['parent'+str(motherIndex)+'Employer'],
                    row["legalGuardianFirstName"], row["legalGuardianLastName"],
                    row["legalGuardianAddress1"], row["legalGuardianAddress2"],
                    row["legalGuardianAddressCity"], row["legalGuardianAddressState"],
                    row["legalGuardianAddressZip"], row["legalGuardianAddressCountry"],
                    row["legalGuardianCollege1NameCeebName"],
                    row["legalGuardianCollege1Degree1"], row["legalGuardianTitle"],
                    row["legalGuardianSuffix"], row["legalGuardianEmail"],
                    row["legalGuardianPhone"].replace('+1.', ''),
                    row["legalGuardianOccupation"], row["legalGuardianEmployer"])
            print (q_insert_partmp_rec)
            scr.write(q_insert_partmp_rec+'\n');
            do_sql(q_insert_partmp_rec, earl=EARL)

            # setting activities variable
            activity1 = row["activity1"].replace("INTERESTS-INTEREST-", "").strip()
            if len(row["transferActivity1"].replace("INTERESTS-INTEREST-", "")):
                activity1 = row["transferActivity1"].replace("INTERESTS-INTEREST-", "").strip()
            activity2 = row["activity2"].replace("INTERESTS-INTEREST-", "").strip()
            if len(row["transferActivity2"].replace("INTERESTS-INTEREST-", "")):
                activity2 = row["transferActivity2"].replace("INTERESTS-INTEREST-", "").strip()
            activity3 = row["activity3"].replace("INTERESTS-INTEREST-", "").strip()
            if len(row["transferActivity3"].replace("INTERESTS-INTEREST-", "")):
                activity3 = row["transferActivity3"].replace("INTERESTS-INTEREST-", "").strip()
            activity4 = row["activity4"].replace("INTERESTS-INTEREST-", "").strip()
            if len(row["transferActivity4"].replace("INTERESTS-INTEREST-", "")):
                activity4 = row["transferActivity4"].replace("INTERESTS-INTEREST-", "").strip()
            activity5 = row["activity5"].replace("INTERESTS-INTEREST-", "").strip()
            if len(row["transferActivity5"].replace("INTERESTS-INTEREST-", "")):
                activity5 = row["transferActivity5"].replace("INTERESTS-INTEREST-", "").strip()

            # insert into app_inttmp_rec
            if activity1:
                insert_interests = '''
                INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                cclevel)
                VALUES ({0}, 0, "{1}", "", "Y");
            ''' .format(apptmp_no, activity1)
                print (insert_interests)
                scr.write(insert_interests+'\n');
                do_sql(insert_interests, earl=EARL)
            if activity2:
                insert_interests = '''
                INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                cclevel)
                VALUES ({0}, 0, "{1}", "", "Y");
            ''' .format(apptmp_no, activity2)
                print (insert_interests)
                scr.write(insert_interests+'\n');
                do_sql(insert_interests, earl=EARL)
            if activity3:
                insert_interests = '''
                INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                cclevel)
                VALUES ({0}, 0, "{1}", "", "Y");
            ''' .format(apptmp_no, activity3)
                print (insert_interests)
                scr.write(insert_interests+'\n');
                do_sql(insert_interests, earl=EARL)
            if activity4:
                insert_interests = '''
                INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                cclevel)
                VALUES ({0}, 0, "{1}", "", "Y");
            ''' .format(apptmp_no, activity4)
                print (insert_interests)
                scr.write(insert_interests+'\n');
                do_sql(insert_interests, earl=EARL)
            if activity5:
                insert_interests = '''
                INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                cclevel)
                VALUES ({0}, 0, "{1}", "", "Y");
            ''' .format(apptmp_no, activity5)
                print (insert_interests)
                scr.write(insert_interests+'\n');
                do_sql(insert_interests, earl=EARL)
            else:  
                print ("There were no activities for this application.")
                scr.write('--There were no activities for this application.\n\n');

            # removing space when there are multiple ethnic backgrounds
            background = (row["background"].replace(' ', '')) 
            # Creating array
            array_ethnic = background.split(',')
            print ('Ethnicity Background: {0}'.format(background))
            print ('Length of the string: {0}'.format (len(array_ethnic)))
            print ('Array: {0}'.format(array_ethnic))
            converted = []
            # Set dictionary
            ethnicity = {
                'N': 'AM',
                'A': 'AS',
                'B': 'BL',
                'P': 'IS',
                'W': 'WH'
            }
            # Loop through array comparing ethnicity(key) setting it to ethnicity(value)
            for eth in array_ethnic:
                print eth
                if eth == 'N':
                    converted.append(ethnicity[eth])
                elif eth == 'A':
                    converted.append(ethnicity[eth])
                elif eth == 'B':
                    converted.append(ethnicity[eth])
                elif eth == 'P':
                    converted.append(ethnicity[eth])
                elif eth == 'W':
                    converted.append(ethnicity[eth])
                if len(converted) == 1:
                   ethnic_code = converted[0]
                elif len(converted) == 0:
                    ethnic_code = 'UN'
                else:
                    ethnic_code = 'MU'
                # Creating list of ethnic backgrounds
                ethnic_code_list = ','.join(converted)
            print ('Ethnicity Code: {0}'.format(ethnic_code_list))
            print ('Number of Ethnicity Codes: {0}'.format(len(ethnic_code_list)))
            if len(converted) > 1:
                for eth_race in converted:
                    # insert into app_mracetmp_rec
                    insert_races = '''
                    INSERT INTO app_mracetmp_rec
                    (id, race)
                    VALUES ({0}, "{1}");
                    ''' .format(apptmp_no, eth_race)
                    print (insert_races)
                    scr.write(insert_races+'\n');
                    do_sql(insert_races, earl=EARL)
            else:
                print ("There was nothing to insert into the mracetmp table.")
                scr.write('--There was nothing to insert into the mracetmp table.\n\n');

            # formatting the dateOfBirth
            dateOfBirth = datetime.datetime.strptime(row["dateOfBirth"], '%m/%d/%Y').strftime('%Y-%m-%d')
            # Religious Denomination Codes
            print ('Denomination Code: {0}'.format(row["religiousPreference"]))
            denomination = {
                'BAP': 'BA',
                'CGR': 'CO',
                'HIN': 'HI',
                'HBR': 'JE',
                'LUT': 'LO',
                'MET': 'ME',
                'MEN': 'MN',
                'MUS': 'MU',
                'OTH': 'O',
                'PRB': 'PR',
                'CAT': 'RC',
                '': ''
            }
            # create variables for the Religious Preference based on the dictionary
            try:
                religiousPreference = denomination[row["religiousPreference"]]
            except KeyError as e:
                religiousPreference = 'O'

            # armedForcesStatus variables
            if row["armedForcesStatus"] == 'Currently_serving':
                armedForcesStatus = 'Y'
            elif row["armedForcesStatus"] == 'Previously_served':
                armedForcesStatus = 'Y'
            elif row["armedForcesStatus"] == 'Current_Dependent':
                armedForcesStatus = 'Y'
            else:
                armedForcesStatus = 'N'

            # insert into app_proftmp_rec
            if ethnic_code == 'UN':
                q_create_prof = '''
                INSERT INTO app_proftmp_rec (id, birth_date, church_id,
                prof_last_upd_date, sex, birthplace_city, birthplace_st,
                birthplace_ctry, visa_code, citz, res_st, res_cty, race,
                hispanic, denom_code, vet)
                VALUES ({0}, TO_DATE("{1}", "%Y-%m-%d"), 0, TODAY, "{2}", "{3}",
                "{4}", "{5}", "", "{6}", "", "", "UN", "{7}", "{8}", "{9}");
                ''' .format(apptmp_no, dateOfBirth, row["sex"], row["birthCity"],
                row["birthState"], row["birthCountry"], row["citizenships"],
                row["hispanicLatino"], religiousPreference, armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
                do_sql(q_create_prof, earl=EARL)
                #profdebug = do_sql(q_create_prof, earl=EARL)
                #print ('Prof Debug: {0}'.format(profdebug))
            elif ethnic_code == 'MU':
                q_create_prof = '''
                INSERT INTO app_proftmp_rec (id, birth_date, church_id,
                prof_last_upd_date, sex, birthplace_city, birthplace_st,
                birthplace_ctry, visa_code, citz, res_st, res_cty, race,
                hispanic, denom_code, vet)
                VALUES ({0}, TO_DATE("{1}", "%Y-%m-%d"), 0, TODAY, "{2}", "{3}",
                "{4}", "{5}", "", "{6}", "", "", "MU", "{7}", "{8}", "{9}");
                ''' .format(apptmp_no, dateOfBirth, row["sex"], row["birthCity"],
                row["birthState"], row["birthCountry"], row["citizenships"],
                row["hispanicLatino"], religiousPreference, armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
                do_sql(q_create_prof, earl=EARL)
                #profdebug = do_sql(q_create_prof, earl=EARL)
                #print ('Prof Debug: {0}'.format(profdebug))
            else:
                q_create_prof = '''
                INSERT INTO app_proftmp_rec (id, birth_date, church_id,
                prof_last_upd_date, sex, birthplace_city, birthplace_st,
                birthplace_ctry, visa_code, citz, res_st, res_cty, race,
                hispanic, denom_code, vet)
                VALUES ({0}, TO_DATE("{1}", "%Y-%m-%d"), 0, TODAY, "{2}", "{3}",
                "{4}", "{5}", "", "{6}", "", "", "{7}", "{8}", "{9}", "{10}");
                ''' .format(apptmp_no, dateOfBirth, row["sex"],
                row["birthCity"], row["birthState"], row["birthCountry"],
                row["citizenships"], ethnic_code_list, row["hispanicLatino"],
                religiousPreference, armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
                do_sql(q_create_prof, earl=EARL)
                #profdebug = do_sql(q_create_prof, earl=EARL)
                #print ('Prof Debug: {0}'.format(profdebug))


            # creating Testing Scores array for ACT, SAT_New
            tests_array = []
            for test in row["totalTestsTaken"].split(','):
                tests_array.append(test.strip())
                print(tests_array)

            if row["actCompositeDate"] == '':
                actCompositeDate = ''
            else: # formatting the actCompositeDate
                actCompositeDate = datetime.datetime.strptime(row["actCompositeDate"], '%m/%d/%Y').strftime('%Y-%m-%d')
            if row["SATRWDate"] == '':
                SATRWDate = ''
            else: # formatting the SATRWDate
                SATRWDate = datetime.datetime.strptime(row["SATRWDate"], '%m/%d/%Y').strftime('%Y-%m-%d')

            for tests in tests_array:
                if tests == 'ACT' and row["ACTCompositeScore"] != '':
                    # insert into app_examtmp_rec
                    q_exam = '''
                    INSERT INTO app_examtmp_rec (id, ctgry, cmpl_date, self_rpt,
                    site, score1, score2, score3, score4, score5, score6)
                    VALUES ({0}, "ACT", TO_DATE("{1}", "%Y-%m-%d"), "Y", "CART",
                    "{2}", "{3}", "{4}", "{5}", "{6}", "{7}")
                    ''' .format(apptmp_no, actCompositeDate, row["ACTCompositeScore"],
                    row["ACTEnglishScore"], row["ACTMathScore"],
                    row["ACTReadingScore"], row["ACTScienceScore"],
                    row["ACTWritingScore"])
                    print (q_exam)
                    scr.write(q_exam+'\n');
                    do_sql(q_exam, earl=EARL)
                if tests == 'SAT_New' and (row["SATRWScore"] != '' or row["SATMathScore"] != '' or row["SATEssayScore"] != ''):
                    q_exam = '''
                    INSERT INTO app_examtmp_rec (id, ctgry, cmpl_date, self_rpt,
                    site, score1, score2, score3, score4, score5, score6)
                    VALUES ({0}, "SAT", TO_DATE("{1}", "%Y-%m-%d"), "Y", "CART",
                    "", "{2}", "{3}", "{4}", "", "")
                    ''' .format(apptmp_no, SATRWDate, row["SATRWScore"],
                    row["SATMathScore"], row["SATEssayScore"])
                    print (q_exam)
                    scr.write(q_exam+'\n');
                    do_sql(q_exam, earl=EARL)

            scr.write('-------------------------------------------------------------------------------------------\n')
            scr.write('-- END INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('-------------------------------------------------------------------------------------------\n\n')
        
        print("--- %s seconds ---" % (time.time() - start_time))
        f.close()


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())