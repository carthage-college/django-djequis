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
from djzbar.utils.informix import get_engine
from djtools.fields import TODAY

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
###############################################################################
# hoping this is a failsafe to ensure when developing we are pointed at TRAIN
###############################################################################
response = raw_input("Are you pointed at the TRAIN database?")

if response == 'Y':
    # write out the .sql file
    scr = open("commonapp_output.sql", "a")
    # set start_time in order to see how long script takes to execute
    start_time = time.time()
    
        ###########################################################################
        # function is used to execute query for test scores (ACT, SAT)
        ###########################################################################
    def insertExam(id, ctgry, cmpl_date, score1, score2, score3, score4, score5, score6):
        #scr = open("commonapp_output.sql", "a")
        if cmpl_date != '':
            #######################################################################
            # creates examtmp record if there are any test scores
            #######################################################################
            q_exam = '''
            INSERT INTO app_examtmp_rec (id, ctgry, cmpl_date, self_rpt,
            site, score1, score2, score3, score4, score5, score6)
            VALUES ({0}, "{1}", TO_DATE("{2}", "%Y-%m-%d"), "Y", "CART",
                    "{3}", "{4}", "{5}", "{6}", "{7}", "{8}")
            ''' .format(id, ctgry, cmpl_date, score1, score2, score3, score4, score5,
                        score6)
            print (q_exam)
            scr.write(q_exam+'\n');
            do_sql(q_exam, key=DEBUG, earl=EARL)
    
    def main():
        # establish mySQL database connection
        cursor = connections['admissions_pce'].cursor()
        engine = get_engine(EARL)
    
        ###########################################################################
        # set directory and filename where to read from
        ###########################################################################
        filename=('{}carthage_applications.txt'.format(
            settings.COMMONAPP_CSV_OUTPUT
        ))
    
        scr.write('------------------------------------------------------------------------------------------------------------------\n')
        scr.write('-- CREATES APPLICATION FROM COMMON APPLICATION DATA \n')
        scr.write('------------------------------------------------------------------------------------------------------------------\n')
    
        # open file
        with open(filename, 'rb') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                # prints the records information for all fields
                print([col+'='+row[col] for col in reader.fieldnames])
    
                # create UUID
                temp_uuid = (uuid.uuid4())
                print ('UUID: {0}'.format(temp_uuid))
    
                ###################################################################
                # checks if waiver code is used which determines the payment method
                ###################################################################
                if row["feeWaiverCode"] == '':
                    paymentMethod = 'CREDIT'
                    waiverCode = ''
                else:
                    paymentMethod = 'WAIVER'
                    waiverCode = row["feeWaiverCode"]
    
                print ('Payment Method: {0}'.format(paymentMethod))
                print ('Waiver Code: {0}'.format(waiverCode))
    
                ###################################################################
                # creates apptmp record
                ###################################################################
                q_create_app = '''
                INSERT INTO apptmp_rec
                (add_date, add_tm, app_source, stat, reason_txt, payment_method, waiver_code)
                VALUES (TODAY, TO_CHAR(CURRENT, '%H%M'), "WEBA", "H", "{0}",
                "{1}", "{2}");
                ''' .format(temp_uuid, paymentMethod, waiverCode)
                print (q_create_app)
                scr.write(q_create_app+'\n');
                do_sql(q_create_app, key=DEBUG, earl=EARL)
    
                ###################################################################
                # fetch id from apptmp_no table
                ###################################################################
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
    
                ###################################################################
                # sets the apptmp_no variable which is used threw out the queries
                ###################################################################
                apptmp_no = (results[0])
                print ('Apptmp No: {0}'.format(results[0]))
    
                scr.write('------------------------------------------------------------------------------------------------------------------\n')
                scr.write('-- START INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + ' - ' + str(apptmp_no) +"\n")
                scr.write('------------------------------------------------------------------------------------------------------------------\n')
    
                ###################################################################
                # fetch id from app_voucher on mySQL dB (admissions_pce).
                # insert into app_vouchers_users on mySQL dB
                ###################################################################
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
                    # if no results are returned set voucher_id to zero
                    if voucher_result == None:
                        voucher_id = 0
                    else:
                        # if results are returned set voucher_id to result
                        voucher_id = (voucher_result[0])
                        ###################################################################
                        # inserts voucher id into app_voucher_users
                        ###################################################################
                        q_update_voucher = '''
                        INSERT INTO app_voucher_users (voucher_id, app_id, submitted_on)
                        VALUES ({0}, {1}, NOW())
                        ''' .format(voucher_id, apptmp_no)
                        print (q_update_voucher)
                        scr.write(q_update_voucher+'\n');
                        cursor.execute(q_update_voucher)
                print ("There were no waiver codes used for this application")
                scr.write("--There were no waiver codes used for this application"+'\n');
    
                ###################################################################
                # creates application temp record
                ###################################################################
                q_create_id = '''
                INSERT INTO app_idtmp_rec
                (id, firstname, lastname, suffixname, cc_username, cc_password,
                addr_line1, addr_line2, city, st, zip, ctry, phone, ss_no,
                middlename, aa, add_date, ofc_add_by, upd_date, purge_date,
                prsp_no, name_sndx, correct_addr, decsd, valid)
                VALUES ({0}, "{1}", "{2}", "{3}", "{4}", "{0}", "{5}", "{6}",
                "{7}", "{8}", "{9}", "{10}", "{11}", "{12}", "{13}", "PERM",
                TODAY, "ADMS", TODAY, TODAY + 2 UNITS YEAR, "0", "", "Y", "N",
                "Y");
                ''' .format(apptmp_no, row["firstName"], row["lastName"],
                row["suffix"], row["emailAddress"], row["permanentAddress1"],
                row["permanentAddress2"], row["permanentAddressCity"],
                row["permanentAddressState"], row["permanentAddressZip"],
                row["permanentAddressCountry"],
                row["preferredPhoneNumber"].replace('+1.', ''), row["ssn"],
                row["middleName"])
                print (q_create_id)
                scr.write(q_create_id+'\n');
                do_sql(q_create_id, key=DEBUG, earl=EARL)
    
                ##################################################################################
                # The Y/N value of contactConsent may seem a little backwards intuitively.
                # Y = The student has opted out meaning Carthage does NOT have permission to text
                # N = The student has opted in meaning Carthage does have permission to text
                #################################################################################
                ###################################################################
                # BEGIN - preferred phone for student
                ###################################################################
                if row["preferredPhone"] == 'Mobile':
                    if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                        contactConsent = 'N'
                    elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                        contactConsent = 'Y'
                    # Preferred Phone is a Mobile
                    q_insert_aa_cell = '''
                    INSERT INTO app_aatmp_rec
                    (id, aa, beg_date, phone, opt_out)
                    VALUES ({0}, "CELL", TODAY, "{1}", "{2}");
                    ''' .format(apptmp_no, row["preferredPhoneNumber"].replace('+1.', ''),
                    row["contactConsent"])
                    print (q_insert_aa_cell)
                    scr.write(q_insert_aa_cell+'\n');
                    do_sql(q_insert_aa_cell, key=DEBUG, earl=EARL)
    
                ###################################################################
                # BEGIN - alternate phone available for student
                ###################################################################
                if row["alternatePhoneAvailable"] != '' and row["alternatePhoneAvailable"] != 'N':
                    altType = 'CELL'
                    if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                        contactConsent = 'N'
                    elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                        contactConsent = 'Y'
                    if row["alternatePhoneAvailable"] == 'Home':
                        altType = 'HOME'
                    # Alternate Phone is available
                    q_insert_aa_cell = '''
                    INSERT INTO app_aatmp_rec
                    (id, aa, beg_date, phone, opt_out)
                    VALUES ({0}, "{1}", TODAY, "{2}", "{3}");
                    ''' .format(apptmp_no, altType, row["alternatePhoneNumber"].replace('+1.', ''),
                    row["contactConsent"])
                    print (q_insert_aa_cell)
                    scr.write(q_insert_aa_cell+'\n');
                    do_sql(q_insert_aa_cell, key=DEBUG, earl=EARL)
    
                ###################################################################
                # creates application site record
                ###################################################################
                q_create_site = '''
                INSERT INTO app_sitetmp_rec
                (id, home, site, beg_date)
                VALUES ({0}, "Y", "CART", TODAY);
                ''' .format(apptmp_no)
                print (q_create_site)
                scr.write(q_create_site+'\n');
                do_sql(q_create_site, key=DEBUG, earl=EARL)
    
                # determine the type of studentStatus and set studentStatus and Hours Enrolled
                if row["studentStatus"] == 'Full Time' or row["transferStudentStatus"] == 'Full Time':
                    studentStatus = 'TRAD'
                    intendHoursEnrolled = 16
                elif row["studentStatus"] == 'Part Time' or row["transferStudentStatus"] == 'Part Time':
                    studentStatus = 'TRAP'
                    intendHoursEnrolled = 4
    
                # fetch preferredStartTerm from Common App data ex.(Fall 2018, Spring 2018, J-Term 2018)
                preferredStartTerm = row["preferredStartTerm"]
                if len(row["transferPreferredStartTerm"]):
                    preferredStartTerm = row["transferPreferredStartTerm"]
                # spliting preferredStartTerm
                planArray = preferredStartTerm.split(' ')
                # set planEnrollYear to Year 
                planEnrollYear = planArray[1]
                # create school session dictionary
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
                # Any nursing majors (1, 2, 3) need to drive the studentType
                # determine the studentType
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
    
                # replacing first part of Common App code for major
                major1 = row["major1"].replace("ADM-MAJOR-", "").strip()
                if len(row["transferMajor1"]):
                    major1 = row["transferMajor1"].replace("ADM-MAJOR-", "").strip()
                major2 = row["major2"].replace("ADM-MAJOR-", "").strip()
                if len(row["transferMajor2"]):
                    major2 = row["transferMajor2"].replace("ADM-MAJOR-", "").strip()
                major3 = row["major3"].replace("ADM-MAJOR-", "").strip()
                if len(row["transferMajor3"]):
                    major3 = row["transferMajor3"].replace("ADM-MAJOR-", "").strip()
    
                # if and major is nursing then the class type is FN
                if major1 == 'NUR' or major2 == 'NUR' or major3 == 'NUR':
                    studentType = 'FN'
    
                # set armedForcesStatus variables
                if row["armedForcesStatus"] == 'Currently_serving':
                    armedForcesStatus = 'Y'
                elif row["armedForcesStatus"] == 'Previously_served':
                    armedForcesStatus = 'Y'
                elif row["armedForcesStatus"] == 'Current_Dependent':
                    armedForcesStatus = 'Y'
                else:
                    armedForcesStatus = 'N'
    
                # creating Parent Marital Status dictionary
                parentMtlStat = {
                    'Married': 'M',
                    'Separated': 'T',
                    'Divorced': 'D',
                    'Widowed': 'W',
                    'Never Married': 'S'
                }
                try:
                    parnt_mtlstat = parentMtlStat[row["parentsMaritalStatus"]]
                except KeyError as e:
                    parnt_mtlstat = 'O'
    
                # determine which Parent Type coming from Common App is Father or Mother
                if row["parent1Type"] == 'Father':
                    parent1 = 'F'
                if row["parent1Type"] == 'Mother':
                    parent1 = 'M'
                if row["parent2Type"] == 'Mother':
                    parent2 = 'M'
                if row["parent2Type"] == 'Father':
                    parent2 = 'F'
    
                # creating Living With dictionary
                liveWith = {
                    'Both Parents': 'B',
                    'Parent 1': parent1,
                    'Parent 2': parent2,
                    'Legal Guardian': 'G',
                    'Other': 'O',
                    'Ward of the Court/State': 'O' 
                }
                otherLivingSituation = ''
                # create variables for Lived with based on the dictionary
                try:
                    live_with = liveWith[row["permanentHome"]]
                    if live_with == 'O':
                        otherLivingSituation = row["otherLivingSituation"]
                except KeyError as e:
                    live_with = 'O'
    
                ###################################################################
                # creates admtmp record
                ###################################################################
                q_create_adm = '''
                INSERT INTO app_admtmp_rec
                (id, primary_app, plan_enr_sess, plan_enr_yr, intend_hrs_enr,
                trnsfr, cl, add_date, parent_contr, enrstat, rank, wisconsin_coven,
                emailaddr, prog, subprog, upd_date, act_choice, stuint_wt,
                jics_candidate, major, major2, major3, app_source, pref_name, felony,
                discipline, parnt_mtlstat, live_with, live_with_other, vet_ben)
                VALUES ({0}, "Y", "{1}", {2}, "{3}", "{4}", "{5}", TODAY, "0.00",
                "", "0", "", "{6}", "UNDG", "{7}", TODAY, "", "0", "N", "{8}",
                "{9}", "{10}", "C", "{11}", "{12}", "{13}", "{14}", "{15}", "{16}",
                "{17}");
                ''' .format(apptmp_no, planEnrollSession, planEnrollYear,
                intendHoursEnrolled, transfer, studentType, row["emailAddress"],
                studentStatus, major1, major2, major3, row["preferredName"],
                row["criminalHistory"], row["schoolDiscipline"], parnt_mtlstat,
                live_with, otherLivingSituation, armedForcesStatus)
                print (q_create_adm)
                scr.write(q_create_adm+'\n');
                do_sql(q_create_adm, key=DEBUG, earl=EARL)
    
                # Email the contents of Criminal and Disiplinary to Adminssions
                # This is something we need to visit in v2.0
    
                # If there is Criminal or Displinary reasons they will be added
                if row["criminalHistory"] != '' or row["schoolDiscipline"] != '':
                    if row["criminalHistory"] == 'Y':
                        reasontxt = row["criminalHistoryExplanation"]
                        resource = 'FELONY'
                        
                        q_insertText = '''
                        INSERT INTO app_ectctmp_rec
                        (id, tick, add_date, resrc, stat, txt)
                        VALUES (?, ?, ?, ?, ?, ?);
                        '''
                        print (q_insertText)
                        scr.write(q_insertText+'\n');
                        engine.execute(q_insertText,
                            [apptmp_no, "ADM", TODAY, resource, "C", reasontxt]
                        )
                    if row["schoolDiscipline"] == 'Y':
                        reasontxt = row["disciplinaryViolationExplanation"]
                        resource = 'DISMISS'
    
                        q_insertText = '''
                        INSERT INTO app_ectctmp_rec
                        (id, tick, add_date, resrc, stat, txt)
                        VALUES (?, ?, ?, ?, ?, ?);
                        '''
                        print (q_insertText)
                        scr.write(q_insertText+'\n');
                        engine.execute(
                            q_insertText,
                            [apptmp_no, "ADM", TODAY, resource, "C", reasontxt]
                        )
    
    
                ###################################################################
                # BEGIN - alternate address for student
                ###################################################################
                if row["alternateAddressAvailable"] == 'Y':
                    ###############################################################
                    # creates aatmp record if alternate address is Y
                    ###############################################################
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
                    do_sql(q_insert_aa_mail, key=DEBUG, earl=EARL)
                else:
                    print ("There were no alternate addresses for this application.")
                    scr.write('--There were no alternate addresses for this application.\n\n');
    
                ###################################################################
                # BEGIN - school(s) attended for a student
                ###################################################################
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
    
                    ###############################################################
                    # creates edtmp record attended by the student
                    ###############################################################
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
                    scr.write("--Executing create school qry"+'\n\n');
                    do_sql(q_create_school, key=DEBUG, earl=EARL)
    
                ###################################################################
                # BEGIN - other school(s) attended for a student
                ###################################################################
                if row["otherSchoolNumber"] != '' and int(row["otherSchoolNumber"]) > 0:
                    for schoolNumber in range(2, int(row["otherSchoolNumber"])+1):
                        print ('Other School Number: {0}'.format(row["otherSchoolNumber"]))
                        print ('school num: {0}'.format(schoolNumber))
                        
                        # check to see that there is a CeebCode coming from Common App
                        if row['secondarySchool'+str(schoolNumber)+'CeebCode'] == '':
                            secondarySchoolCeebCode = 0
                        else:
                            secondarySchoolCeebCode = row['secondarySchool'+str(schoolNumber)+'CeebCode']
                            
                        if row['secondarySchool'+str(schoolNumber)+'FromDate'] == '':
                            fromDate = ''
                        else: # formatting the fromDate
                            fromDate = datetime.datetime.strptime(row['secondarySchool'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                        if row['secondarySchool'+str(schoolNumber)+'ToDate'] == '':
                            toDate = ''
                        else: # formatting the toDate
                            toDate = datetime.datetime.strptime(row['secondarySchool'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')
    
                        ###########################################################
                        # creates edtmp record if there are any secondary schools
                        ###########################################################
                        q_create_other_school = '''
                        INSERT INTO app_edtmp_rec
                        (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                        stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                        acad_trans)
                        VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                        TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "hs", "HS", "N");
                    ''' .format(apptmp_no, secondarySchoolCeebCode,
                        row['secondarySchool'+str(schoolNumber)+'CeebName'],
                        row['secondarySchool'+str(schoolNumber)+'City'],
                        row['secondarySchool'+str(schoolNumber)+'State'],
                        fromDate, toDate,
                        row['secondarySchool'+str(schoolNumber)+'Zip'])
                        print (q_create_other_school)
                        scr.write(q_create_other_school+'\n\n');
                        scr.write("--Executing other school qry"+'\n\n');
                        do_sql(q_create_other_school, key=DEBUG, earl=EARL)
                else:
                    print ("There were no other schools attended to insert")
                    scr.write("--There were no other schools attended for this application."+'\n\n');
    
                ###################################################################
                # BEGIN - secondary school(s) attended for a transfer student
                ###################################################################
                if row["transferSecondarySchoolsAttendedNumber"] != '' and int(row["transferSecondarySchoolsAttendedNumber"]) > 0:
                    for schoolNumber in range(1, int(row["transferSecondarySchoolsAttendedNumber"])+1):
                        print ('Transfer Other School Number: {0}'.format(row["transferSecondarySchoolsAttendedNumber"]))
                        print ('school num: {0}'.format(schoolNumber))
                        
                        # check to see that there is a CeebCode coming from Common App
                        if row['transferSecondarySchool'+str(schoolNumber)+'CeebCode'] == '':
                            transferSecondarySchoolCeebCode = 0
                        else:
                            transferSecondarySchoolCeebCode = row['transferSecondarySchool'+str(schoolNumber)+'CeebCode']
                            
                        if row['transferSecondarySchool'+str(schoolNumber)+'FromDate'] == '':
                            fromDate = ''
                        else: # formatting the fromDate
                            fromDate = datetime.datetime.strptime(row['transferSecondarySchool'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                        if row['transferSecondarySchool'+str(schoolNumber)+'ToDate'] == '':
                            toDate = ''
                        else: # formatting the toDate
                            toDate = datetime.datetime.strptime(row['transferSecondarySchool'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')
                        ###########################################################
                        # creates edtmp record if there are any secondary schools
                        # for a transfer students
                        ###########################################################
                        q_create_transfer_other_school = '''
                        INSERT INTO app_edtmp_rec
                        (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                        stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                        acad_trans)
                        VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                        TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "hs", "HS", "N");
                    ''' .format(apptmp_no, transferSecondarySchoolCeebCode,
                        row['transferSecondarySchool'+str(schoolNumber)+'CeebName'],
                        row['transferSecondarySchool'+str(schoolNumber)+'City'],
                        row['transferSecondarySchool'+str(schoolNumber)+'State'],
                        fromDate, toDate,
                        row['transferSecondarySchool'+str(schoolNumber)+'Zip'])
                        print (q_create_transfer_other_school)
                        scr.write(q_create_transfer_other_school+'\n\n');
                        scr.write("--Executing transfer other school qry"+'\n\n');
                        do_sql(q_create_transfer_other_school, key=DEBUG, earl=EARL)
                else:
                    print ("There were no transfer secondary schools attended to insert")
                    scr.write('--There were no transfer secondary schools attended for this application.\n\n');
    
               ####################################################################
                # BEGIN - college(s) attended for a student
                ###################################################################
                if row["collegesAttendedNumber"] != '' and int(row["collegesAttendedNumber"]) > 0:
                    for schoolNumber in range(1, int(row["collegesAttendedNumber"])+1):
                        print ('College School Number: {0}'.format(row["collegesAttendedNumber"]))
                        print ('school num: {0}'.format(schoolNumber))
    
                        # check to see that there is a CeebCode coming from Common App
                        if row['college'+str(schoolNumber)+'CeebCode'] == '':
                            collegeCeebCode = 0
                        else:
                            collegeCeebCode = row['college'+str(schoolNumber)+'CeebCode']
    
                        # check to see if FromDate is empty if not set to From Date coming from Common App
                        if row['college'+str(schoolNumber)+'FromDate'] == '':
                            fromDate = ''
                        else: # formatting the fromDate
                            fromDate = datetime.datetime.strptime(row['college'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                        if row['college'+str(schoolNumber)+'ToDate'] == '':
                            toDate = ''
                        else: # formatting the toDate
                            toDate = datetime.datetime.strptime(row['college'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')
                        ###########################################################
                        # creates edtmp record if there are any colleges attended
                        ###########################################################
                        q_create_college_school = '''
                        INSERT INTO app_edtmp_rec
                        (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                        stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa,
                        ctgry, acad_trans)
                        VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                        TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "ac",
                        "COL", "N");
                    ''' .format(apptmp_no, collegeCeebCode,
                        row['college'+str(schoolNumber)+'CeebName'],
                        row['college'+str(schoolNumber)+'City'],
                        row['college'+str(schoolNumber)+'State'],
                        fromDate, toDate,
                        row['college'+str(schoolNumber)+'Zip'])
                        print (q_create_college_school)
                        scr.write(q_create_college_school+'\n\n');
                        do_sql(q_create_college_school, key=DEBUG, earl=EARL)
                else:
                    print ("There were no colleges attended to insert")
                    scr.write('--There were no colleges attended for this application.\n\n');
                ###################################################################
                # BEGIN - college(s) attended for a transfer student
                ###################################################################
                if row["transferCollegesAttendedNumber"] != '' and int(row["transferCollegesAttendedNumber"]) > 0:
                    for schoolNumber in range(1, int(row["transferCollegesAttendedNumber"])+1):
                        print ('Transfer College School Number: {0}'.format(row["transferCollegesAttendedNumber"]))
                        print ('school num: {0}'.format(schoolNumber))
    
                        # check to see that there is a CeebCode coming from Common App
                        if row['transferCollege'+str(schoolNumber)+'CeebCode'] == '':
                            transferCollegeCeebCode = 0
                        else:
                            transferCollegeCeebCode = row['transferCollege'+str(schoolNumber)+'CeebCode']
    
                        if row['transferCollege'+str(schoolNumber)+'FromDate'] == '':
                            fromDate = ''
                        else: # formatting the fromDate
                            fromDate = datetime.datetime.strptime(row['transferCollege'+str(schoolNumber)+'FromDate'], '%m/%Y').strftime('%Y-%m-01')
                        if row['transferCollege'+str(schoolNumber)+'ToDate'] == '':
                            toDate = ''
                        else: # formatting the toDate
                            toDate = datetime.datetime.strptime(row['transferCollege'+str(schoolNumber)+'ToDate'], '%m/%Y').strftime('%Y-%m-01')
    
                       ###########################################################
                        # creates edtmp record if there are any colleges for a
                        # transfer student
                        ###########################################################
                        q_create_transfer_college_school = '''
                        INSERT INTO app_edtmp_rec
                        (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                        stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                        acad_trans)
                        VALUES ({0}, {1}, "{2}", "{3}", "{4}", "", TO_DATE("{5}", "%Y-%m-%d"),
                        TO_DATE("{6}", "%Y-%m-%d"), 0, 0, 0, 0, 0, "{7}", "ac",
                        "COL", "N");
                    ''' .format(apptmp_no, transferCollegeCeebCode,
                        row['transferCollege'+str(schoolNumber)+'CeebName'],
                        row['transferCollege'+str(schoolNumber)+'City'],
                        row['transferCollege'+str(schoolNumber)+'State'],
                        fromDate, toDate,
                        row['transferCollege'+str(schoolNumber)+'Zip'])
                        print (q_create_transfer_college_school)
                        scr.write(q_create_transfer_college_school+'\n\n');
                        do_sql(q_create_transfer_college_school, key=DEBUG, earl=EARL)
                else:
                    print ("There were no transfercolleges attended to insert")
                    scr.write('--There were no transfercolleges attended for this application.\n\n');
    
                ###################################################################
                # BEGIN - relatives attended Carthage
                ###################################################################
                if row["relativesAttended"] == 'Yes':
                    for relativeNumber in range (1, 5 +1):
                        if row['relative'+str(relativeNumber)+'FirstName'] != '':
                            relativeGradYear = row['relative'+str(relativeNumber)+'GradYear1']
                            if len(row['transferRelative'+str(relativeNumber)+'GradYear1']):
                                relativeGradYear = row['transferRelative'+str(relativeNumber)+'GradYear1']
                            if relativeGradYear == '':
                                relativeGradYear = 0
                            #######################################################
                            # creates reltmp record if there are any relatives
                            #######################################################
                            q_alumni = '''
                            INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                            phone_ext, aa, zip)
                            VALUES ({0}, 0, 5, "{1}", {2}, "ALUM", 0);
                        ''' .format(apptmp_no, row['relative'+str(relativeNumber)+'FirstName'] + ' ' + row['relative'+str(relativeNumber)+'LastName'],
                            relativeGradYear)
                            print (q_alumni)
                            scr.write(q_alumni+'\n\n');
                            do_sql(q_alumni, key=DEBUG, earl=EARL)
                else:
                    print ("There were no relatives (ALUMI) for this application.")
                    scr.write('--There were no relatives (ALUMI) for this application.\n\n');
    
                ###################################################################
                # BEGIN - siblings **if there are no siblings then nothing is inserted
                ###################################################################
                if row["numberOfSiblings"] > 0:
                    # set dictionary for sibling education level
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
                    for siblingNumber in range (1, 5 +1):
                        if row['sibling'+str(siblingNumber)+'FirstName'] != '':
                            #######################################################
                            # creates reltmp record if there are any siblings
                            #######################################################
                            q_sibing_name = '''
                            INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname,
                            phone_ext, aa, zip, prim, addr_line2, suffix)
                            VALUES ({0}, 0, "SIB", "{1}", "{2}", "SBSB", 0, "Y", "{3}",
                            "{4}");
                        ''' .format(apptmp_no, row['sibling'+str(siblingNumber)+'FirstName'] + ' ' + row['sibling'+str(siblingNumber)+'LastName'],
                            row["sibling1Age"], row["sibling1CollegeCeebName"],
                            educationLevel[row['sibling'+str(siblingNumber)+'EducationLevel']])
                            print (q_sibing_name)
                            scr.write(q_sibing_name+'\n\n');
                            do_sql(q_sibing_name, key=DEBUG, earl=EARL)
                else:  
                    print ("There were no siblings to insert.")
                    scr.write('--There were no siblings for this application.\n\n');
    
                ###################################################################
                # BEGIN - parent(s), legal guardian
                ###################################################################
                fatherIndex = 1
                motherIndex = 2
                if row["parent1Type"] == 'Mother':
                    fatherIndex = 2
                    motherIndex = 1
                print ('fatherIndex: {0}'.format(fatherIndex))
                print ('motherIndex: {0}'.format(motherIndex))
                #######################################################
                # creates partmp record if there are any parents
                #######################################################
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
                do_sql(q_insert_partmp_rec, key=DEBUG, earl=EARL)
    
                ###################################################################
                # BEGIN - activities
                ###################################################################
                if row["activity1"] != '' or row["transferActivity1"] != '':
                    for activityNumber in range (1, 5 +1):
                        # replacing first part of Common App code for activity
                        activity = row['activity'+str(activityNumber)].replace("INTERESTS-INTEREST-", "")
                        if len(row['transferActivity'+str(activityNumber)].replace("INTERESTS-INTEREST-", "")):
                            activity = row['transferActivity'+str(activityNumber)].replace("INTERESTS-INTEREST-", "")
                        if activity:
                            #######################################################
                            # creates inttmp record if there are any activities
                            #######################################################
                            insert_interests = '''
                            INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry,
                            cclevel)
                            VALUES ({0}, 0, "{1}", "", "Y");
                        ''' .format(apptmp_no, activity)
                            print (insert_interests)
                            scr.write(insert_interests+'\n');
                            do_sql(insert_interests, key=DEBUG, earl=EARL)
                else:
                    print ("There were no activities for this application.")
                    scr.write('--There were no activities for this application.\n\n');
    
                ###################################################################
                # BEGIN - ethnic backgrounds
                ###################################################################
                # removing space when there are multiple ethnic backgrounds
                background = (row["background"].replace(' ', '')) 
                # Creating array
                array_ethnic = background.split(',')
                print ('Ethnicity Background: {0}'.format(background))
                print ('Length of the string: {0}'.format (len(array_ethnic)))
                print ('Array: {0}'.format(array_ethnic))
                converted = []
                # create ethnicity dictionary
                ethnicity = {
                    'N': 'AM',
                    'A': 'AS',
                    'B': 'BL',
                    'P': 'IS',
                    'W': 'WH'
                }
                # Loop through array comparing ethnicity(key) setting it to ethnicity(value)
                for eth in array_ethnic:
                    try:
                        converted.append(ethnicity[eth])
                    except:
                        pass
                # setting ethnic_code
                if len(converted) == 1:
                    ethnic_code = converted[0]
                elif len(converted) == 0:
                    ethnic_code = 'UN'
                else:
                    ethnic_code = 'MU'
    
                if len(converted) > 1:
                    for eth_race in converted:
                        ############################################################
                        # creates mracetmp record if there are multiple ethnic codes
                        ############################################################
                        insert_races = '''
                        INSERT INTO app_mracetmp_rec
                        (id, race)
                        VALUES ({0}, "{1}");
                        ''' .format(apptmp_no, eth_race)
                        print (insert_races)
                        scr.write(insert_races+'\n');
                        do_sql(insert_races, key=DEBUG, earl=EARL)
                else:
                    print ("There was nothing to insert into the mracetmp table.")
                    scr.write('--There was nothing to insert into the mracetmp table.\n\n');
    
                # formatting the dateOfBirth
                dateOfBirth = datetime.datetime.strptime(row["dateOfBirth"], '%m/%d/%Y').strftime('%Y-%m-%d')
    
                # create religious denomination codes dictionary
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
                # create variables for the religious preference based on the dictionary
                try:
                    religiousPreference = denomination[row["religiousPreference"]]
                except KeyError as e:
                    religiousPreference = 'O'
                ####################################################################
                # creates proftmp record
                ####################################################################
                q_create_prof = '''
                INSERT INTO app_proftmp_rec (id, birth_date, church_id,
                prof_last_upd_date, sex, birthplace_city, birthplace_st,
                birthplace_ctry, visa_code, citz, res_st, res_cty, race,
                hispanic, denom_code, vet)
                VALUES ({0}, TO_DATE("{1}", "%Y-%m-%d"), 0, TODAY, "{2}", "{3}",
                "{4}", "{5}", "", "{6}", "", "", "{7}", "{8}", "{9}", "{10}");
                ''' .format(apptmp_no, dateOfBirth, row["sex"], row["birthCity"],
                row["birthState"], row["birthCountry"], row["citizenships"],
                ethnic_code, row["hispanicLatino"],
                religiousPreference, armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
                do_sql(q_create_prof, key=DEBUG, earl=EARL)
    
                ####################################################################
                # BEGIN - testing scores
                # testing scores array for ACT, SAT_New
                # insertExam function at the top of script creates insert statement
                ####################################################################
                if row["totalTestsTaken"] != '':
                    userTests = row["totalTestsTaken"].split(',')
                    for test in userTests:
                        if test.strip() == 'ACT' and row["actCompositeDate"] != '':
                            cmpl_date = datetime.datetime.strptime(row["actCompositeDate"], '%m/%d/%Y').strftime('%Y-%m-%d')
                            insertExam(apptmp_no, 'ACT', cmpl_date, row["actCompositeScore"],
                                row["actEnglishScore"], row["actMathScore"],
                                row["actReadingScore"], row["actScienceScore"],
                                row["actWritingScore"])
                        elif test.strip() == 'SAT_New' and row["satRWDate"] != '':
                            cmpl_date = datetime.datetime.strptime(row["satRWDate"], '%m/%d/%Y').strftime('%Y-%m-%d')
                            insertExam(apptmp_no, 'SAT', cmpl_date, '', row["satRWScore"],
                                row["satMathScore"], row["satEssayScore"], '', '')
                else:
                    print ("There were no tests to insert into the app_examtmp_rec table.")
                    scr.write('--There were no tests for this application.\n\n');
    
                scr.write('-------------------------------------------------------------------------------------------\n')
                scr.write('-- END INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
                scr.write('-------------------------------------------------------------------------------------------\n\n')
    
            # output of how long it takes to run script
            print("--- %s seconds ---" % (time.time() - start_time))
    
            # close file
            f.close()

    if __name__ == "__main__":
        args = parser.parse_args()
        test = args.test
    
        sys.exit(main())
else:
    print ("Update the setting.py file by commenting out the production connection.")

