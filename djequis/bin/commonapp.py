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
import random

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

def main():
    # go to our storage directory on the server
    # os.chdir(settings.COMMONAPP_CSV_OUTPUT)
    # cnopts = pysftp.CnOpts()
    # cnopts.hostkeys = None
    # XTRNL_CONNECTION = {
    #    'host':settings.COMMONAPP_HOST,
    #    'username':settings.COMMONAPP_USER,
    #    'cnopts':cnopts
    # }
    # SFTP GET the Common App file
    # try:
    #     with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            #sftp.chdir("replace/")

    #         sftp.get(filename, preserve_mtime=True)
    #         sftp.close()
    # except Exception, e:
    #     SUBJECT = '[Common Application SFTP] {} failed'.format(key)
    #     BODY = 'Unable to GET upload to Common Application server.\n\n{}'.format(str(e))
    #     sendmail(
    #         settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
    #         SUBJECT, BODY
    #     )
    
    # set directory and filename
    filename=('{}carthage_applications.txt'.format(
        settings.COMMONAPP_CSV_OUTPUT
    ))
    # write out the .sql file
    scr = open("commonapp_output.sql", "a")

    # creating header in sql script
    scr.write('--------------------------------------------------------------------------------\n' )
    scr.write('-- COMMON APPLICATION - RESULTS IN TEMP TABLE \n' )
    scr.write('--------------------------------------------------------------------------------\n' )

    # Read file
    with open(filename, 'rb') as f:

        reader = csv.reader(f)
        #for row in reader:
            #print row[1]
        reader = csv.reader(f, delimiter=',')
        included_cols = [0, 1, 2, 3, 4, 5]

        for row in reader:
            content = list(row[i] for i in included_cols)
            print content
            print row[17]
            # Set apptmp_no counter to generate fake application number
            apptmp_no = random.randint(100000, 500000)

            """
            # queries from the applicant.cfc
            q_match = '''
                SELECT
                    id
                FROM
                    app_idtmp_rec
                WHERE
                    TRIM(cc_username) = '{0}'
                AND
                    cc_password = '{1}';
            ''' .format('ssmolik@wi.rr.com', 'thisisafakeapplication2017')
            print (q_match)
        
            sqlresult = do_sql(q_match, earl=EARL)
            for row in sqlresult:
                print ('ID: {0}'.format(row[0]))
        
            # Check for duplicate account for the login name provided
            q_matching_user = '''
                SELECT
                    id
                FROM
                    app_idtmp_rec
                WHERE
                    cc_username = ;
            '''
            """
            # Setting Common App variables to be used throughout script
            commonAppID = (row[0])
            startYear = (row[1])
            studentType = (row[2])
            if studentType == 'FY':
                studentType = 'FF'
            elif studentType == 'TR':
                studentType = 'UT'
            firstName = (row[3]) # max character length = 25
            middleName = (row[4]) # max character length = 25
            lastName = (row[5]) # max character length = 30
            emailAddress = (row[6]) # max character length = 60
            suffix = (row[7])
            preferredName = (row[8]) # max character length = 20
            formerLastName = (row[9]) # max character length = 50
            sex = (row[10])
            armedForcesStatus = (row[11])
            ssn = (row[12]) # max character length = 11
            #dateOfBirth = (row[13])
            dateOfBirth = datetime.datetime.strptime(row[13], '%m/%d/%Y').strftime('%Y-%m-%d')
            birthCity = (row[14])
            birthState = (row[15])
            birthCountry = (row[16])
            permanentAddress1 = (row[17]) # max character length = 60
            permanentAddressCity = (row[18]) # max character length = 60
            permanentAddressState = (row[19]) # max character length = 60
            permanentAddressZip = (row[20]) # max character length = 60
            permanentAddressCountry = (row[21]) # max character length = 60
            currentAddress1 = (row[22]) # max character length = 60
            currentAddress2 = (row[23]) # max character length = 60
            currentAddressCity = (row[24]) # max character length = 60
            currentAddressState = (row[25]) # max character length = 60
            currentAddressZip = (row[26]) # max character length = 60
            currentAddressCountry = (row[27]) # max character length = 60
            parent1Type = (row[28])
            parent1Title = (row[29])
            parent1FirstName = (row[30]) # max character length = 24
            parent1LastName = (row[31]) # max character length = 24
            parent1Suffix = (row[32])
            parent1Address1 = (row[33]) # max character length = 60
            parent1Address2 = (row[34]) # max character length = 60
            parent1AddressCity = (row[35]) # max character length = 60
            parent1AddressState = (row[36]) # max character length = 60
            parent1AddressZip = (row[37]) # max character length = 60
            parent1AddressCountry = (row[38]) # max character length = 60
            parent1Email = (row[39]) # max character length = 60
            parent1Phone = (row[40].replace('+1.', '')) # removes the +1. from phone number
            parent1Occupation = (row[41])
            parent1Employer = (row[42])
            parent1College1NameCeebCode = (row[43])
            parent1EducationLevel = (row[44])
            parent2Type = (row[45])
            parent2Title = (row[46])
            parent2FirstName = (row[47]) # max character length = 24
            parent2LastName = (row[48]) # max character length = 24
            parent2Suffix = (row[49])
            parent2Address1 = (row[50]) # max character length = 30
            parent2Address2 = (row[51]) # max character length = 30
            parent2AddressCity = (row[52]) # max character length = 30
            parent2AddressState = (row[53]) # max character length = 30
            parent2AddressZip = (row[54]) # max character length = 30
            parent2AddressCountry = (row[55]) # max character length = 30
            parent2Email = (row[56]) # max character length = 60
            parent2Phone = (row[57].replace('+1.', '')) # removes the +1. from phone number
            parent2Occupation = (row[58])
            parent2Employer = (row[59])
            parent2College1NameCeebCode = (row[60])
            parent2EducationLevel = (row[61])
            legalGuardianFirstName = (row[62]) # max character length = 24
            legalGuardianLastName = (row[63]) # max character length = 24
            legalGuardianFullName = (legalGuardianFirstName + ' ' + legalGuardianLastName)
            legalGuardianSuffix = (row[64])
            legalGuardianAddress1 = (row[65]) # max character length = 30
            legalGuardianAddress2 = (row[66]) # max character length = 30
            legalGuardianAddressCity = (row[67]) # max character length = 30
            legalGuardianAddressState = (row[68]) # max character length = 30
            legalGuardianAddressZip = (row[69]) # max character length = 30
            legalGuardianAddressCountry = (row[70]) # max character length = 30
            legalGuardianEmail = (row[71]) # max character length = 60
            legalGuardianPhone = (row[72].replace('+1.', '')) # removes the +1. from phone number
            legalGuardianOccupation = (row[73])
            legalGuardianEmployer = (row[74])
            legalGuardianCollege1NameCeebCode = (row[75])
            legalGuardianEducationLevel = (row[76])
            sibling1Relationship = (row[77])
            sibling1FirstName = (row[78]) # max character length = 15
            sibling1LastName = (row[79]) # max character length = 15
            sibling1FullName = (sibling1FirstName + ' ' + sibling1LastName)
            sibling1Age = (row[80])
            sibling1EducationLevel = (row[81])
            sibling1CollegeCeebCode = (row[82])
            sibling2Relationship = (row[83])
            sibling2FirstName = (row[84]) # max character length = 15
            sibling2LastName = (row[85]) # max character length = 15
            sibling2FullName = (sibling2FirstName + ' ' + sibling2LastName)
            sibling2Age = (row[86])
            sibling2CollegeCeebCode = (row[87])
            sibling2EducationLevel = (row[88])
            sibling3Relationship = (row[89])
            sibling3FirstName = (row[90]) # max character length = 15
            sibling3LastName = (row[91]) # max character length = 15
            sibling3FullName = (sibling3FirstName + ' ' + sibling3LastName)
            sibling3Age = (row[92])
            sibling3EducationLevel = (row[93])
            sibling3CollegeCeebCode = (row[94])
            sibling4Relationship = (row[95])
            sibling4FirstName = (row[96]) # max character length = 15
            sibling4LastName = (row[97]) # max character length = 15
            sibling4FullName = (sibling4FirstName + ' ' + sibling4LastName)
            sibling4Age = (row[98])
            sibling4EducationLevel = (row[99])
            sibling4CollegeCeebCode = (row[100])
            sibling5Relationship = (row[101])
            sibling5FirstName = (row[102]) # max character length = 15
            sibling5LastName = (row[103]) # max character length = 15
            sibling5FullName = (sibling5FirstName + ' ' + sibling5LastName)
            sibling5Age = (row[104])
            sibling5EducationLevel = (row[105])
            sibling5CollegeCeebCode = (row[106])
            entryDate = (row[107])
            #entryDate = datetime.datetime.strptime(row[107], '%m/%Y').strftime('%Y-%m-01')
            exitDate = (row[108])
            #exitDate = datetime.datetime.strptime(row[108], '%m/%Y').strftime('%Y-%m-01')
            graduationDate = (row[109])
            #graduationDate = datetime.datetime.strptime(row[109], '%m/%Y').strftime('%Y-%m-01')
            actCompositeDate = (row[110])
            major1 = (row[111])
            major2 = (row[112])
            major3 = (row[113])
            careerGoal = (row[114])
            activity1 = (row[115])
            activity2 = (row[116])
            activity3 = (row[117])
            activity4 = (row[118])
            activity5 = (row[119])
            extracurricularActivities = (row[120])
            hispanicLatino = (row[121])
            # removing space when there are multiple ethnic backgrounds
            background = (row[122].replace(' ', '')) 
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
                print ('Converted string: {0}'.format(converted))
                print ('Ethnic Code: {0}'.format(ethnic_code))
                print ('Ethnic Code List: {0}'.format(ethnic_code_list))

            americanIndianBackground = (row[123])
            americanIndianOther = (row[124])
            asianBackground = (row[125])
            eastAsiaOther = (row[126])
            southAsiaOther = (row[127])
            southeastAsiaOther = (row[128])
            africanBackground = (row[129])
            africanOther = (row[130])
            hawaiianBackground = (row[131])
            hawaiianOther = (row[132])
            whiteBackground = (row[133])
            whiteOther = (row[134])
            religiousPreference = (row[135])
            preferredPhone = (row[136])
            preferredPhoneNumber = (row[137].replace('+1.', '')) # removes the +1. from phone number
            permanentAddress2 = (row[138]) # max character length = 60
            preferredStartTerm = (row[139][18:])
            studentStatus = (row[140])
            if studentStatus == 'Full Time':
                studentStatus = 'TRAD'
            elif studentStatus == 'Part Time':
                studentStatus = 'TRAP'
            admissionPlan = (row[141])
            preferredResidence = (row[142])
            alternatePhoneNumber = (row[143].replace('+1.', '')) # removes the +1. from phone number
            alternatePhoneAvailable = (row[144])
            schoolLookupCeebCode = (row[145])
            schoolLookupCeebName = (row[146])
            schoolLookupAddress1 = (row[147])
            schoolLookupCity = (row[148])
            schoolLookupState = (row[149])
            schoolLookupZip = (row[150])
            relativesAttended = (row[151])
            relative1FirstName = (row[152]) # max character length = 24
            relative1LastName = (row[153]) # max character length = 24
            relative1FullName = (relative1FirstName + ' ' + relative1LastName)
            relative1GradYear1 = (row[154])
            relative2FirstName = (row[155]) # max character length = 24
            relative2LastName = (row[156]) # max character length = 24
            relative2FullName = (relative2FirstName + ' ' + relative2LastName)
            relative2GradYear1 = (row[157])
            relative3FirstName = (row[158]) # max character length = 24
            relative3LastName = (row[159]) # max character length = 24
            relative3FullName = (relative3FirstName + ' ' + relative3LastName)
            relative3GradYear1 = (row[160])
            relative4FirstName = (row[161]) # max character length = 24
            relative4LastName = (row[162]) # max character length = 24
            relative4FullName = (relative4FirstName + ' ' + relative4LastName)
            relative4GradYear1 = (row[163])
            relative5FirstName = (row[164]) # max character length = 24
            relative5LastName = (row[165]) # max character length = 24
            relative5FullName = (relative5FirstName + ' ' + relative5LastName)
            relative5GradYear1 = (row[166])
            numberOfSiblings = (row[167])
            hispanicLatinoOther = (row[168])
            hispanicLatinoBackground = (row[169])
            contactConsent = (row[170])
            ACTNumber = (row[171])
            ACTCompositeScore = (row[172])
            ACTEnglishScore = (row[173])
            ACTMathScore = (row[174])
            ACTReadingScore = (row[175])
            ACTScienceScore = (row[176])
            ACTWritingScore = (row[177])
            SATNumber = (row[178])
            SATMathScore = (row[179])
            SATRWScore = (row[180])
            SATEssayScore = (row[181])
            totalTestsTaken = (row[182])
            SATRWDate = (row[183])
            SATMathDate = (row[184])
            SATEssayDate = (row[185])
            feeWaiverCode = (row[186]) # max character length = 50
            permanentAddress3 = (row[187]) # max character length = 60
            currentAddress3 = (row[188]) # max character length = 60
            freshmanNursing = (row[189])
            if studentType == 'FF' and freshmanNursing == 'Y':
                studentType = 'FN'
            #######################################################################
            # Below are Transfer Student variables coming from Common App
            #######################################################################
            preferredStartTerm = (row[190][18:])
            admissionPlan = (row[191])
            transferStudentStatus = (row[192])
            if transferStudentStatus == 'Full Time':
                studentStatus = 'TRAD'
            elif transferStudentStatus == 'Part Time':
                studentStatus = 'TRAP'
            
            print ('Student Type: {0}'.format(studentType))
            print ('Student Status: {0}'.format(studentStatus))
            print ('Admission Plan: {0}'.format(admissionPlan))
            print ('Freshman Nursing: {0}'.format(freshmanNursing))
            print ('Contact Consent: {0}'.format(contactConsent))
            print ('Total Tests Taken: {0}'.format(totalTestsTaken))
            print ('Fee Waiver Code: {0}'.format(feeWaiverCode))
            now_date = (date.today())
            print ('Now Date: {0}'.format(now_date))
            purge_date = (now_date.replace(year = now_date.year + 2))
            print ('Purge Date: {0}'.format(purge_date))
            default_birthdate = (date(now_date.year - 18, 01, 01))
            print ('Default BirthDate: {0}'.format(default_birthdate))
            d_date = (datetime.datetime.now())
            now_time = (d_date.strftime("%H%M"))
            print ('Now Time: {0}'.format(now_time))
            temp_uuid = (uuid.uuid4())
            print ('UUID: {0}'.format(temp_uuid))
            # I added clean beg and clean end date here to show that variables
            # can be used to create them.
            mail_beg_date_year = 2017
            mail_beg_date_month = 05
            mail_beg_date_day = 24
            clean_beg_date = datetime.date(mail_beg_date_year, mail_beg_date_month, mail_beg_date_day)
            print ('Clean Beg Date: {0}'.format(clean_beg_date))
            mail_end_date_year = 2020
            mail_end_date_month = 05
            mail_end_date_day = 25
            clean_end_date = datetime.date(mail_end_date_year, mail_end_date_month, mail_end_date_day)
            print ('Clean End Date: {0}'.format(clean_end_date))

            scr.write('--------------------------------------------------------------------------------\n')
            scr.write('-- START INSERT NEW STUDENT APPLICATION for: ' + firstName + ' ' + lastName + "\n")
            scr.write('--------------------------------------------------------------------------------\n')
            # insert into apptmp_rec
            q_create_app = '''
                INSERT INTO apptmp_rec
                    (add_date, add_tm, app_source, stat, reason_txt)
                VALUES ("{0}", {1}, "WEBA", "P", "{2}");
            ''' .format(now_date, now_time, temp_uuid)
            print (q_create_app)
            scr.write(q_create_app+'\n');

            # Getting apptmp_no
            lookup_apptmp_no = '''
                SELECT
                    apptmp_no
                FROM
                    apptmp_rec
                WHERE
                    reason_txt = "{0}";
            ''' .format(temp_uuid)
            print (lookup_apptmp_no)
            scr.write(lookup_apptmp_no+'\n');

            #######################################################################
            # We might have an issue that we may have when we actually start to
            # interact with the database. This code caused the script to slow down to a crawl
            #######################################################################
    
            #sqlresult = do_sql(lookup_apptmp_no, earl=EARL)
            #for row in sqlresult:
                #apptmp_no = row[0]
                #print ('apptmp_no: {0}'.format(apptmp_no))

            # insert into app_idtmp_rec
            q_create_id = '''
                INSERT INTO app_idtmp_rec
                    (id, firstname, lastname, cc_username, cc_password, addr_line1,
                    addr_line2, city, st, zip, ctry, phone, aa, add_date, ofc_add_by,
                    upd_date, purge_date, prsp_no, name_sndx, correct_addr, decsd,
                    valid)
                VALUES ({0}, "{1}", "{2}", "{3}", {0}, "{4}", "{5}", "{6}", "{7}",
                    {8},"{9}","{10}","PERM","{11}","ADMS", "{12}","{12}","0","",
                    "Y","N","Y");
            ''' .format(apptmp_no, firstName, lastName, emailAddress,
                    permanentAddress1, permanentAddress2, permanentAddressCity,
                    permanentAddressState, permanentAddressZip, permanentAddressCountry,
                    preferredPhoneNumber, now_date, purge_date)
            print (q_create_id)
            print (apptmp_no)
            scr.write(q_create_id+'\n');

            # insert into app_sitetmp_rec
            q_create_site = '''
                INSERT INTO app_sitetmp_rec
                    (id, home, site, beg_date)
                VALUES ({0}, "Y", "CART", "{1}");
            ''' .format(apptmp_no, now_date)
            print (q_create_site)
            scr.write(q_create_site+'\n');

            # insert into app_admtmp_rec
            q_create_adm = '''
                INSERT INTO app_admtmp_rec
                    (id, primary_app, plan_enr_sess, plan_enr_yr, intend_hrs_enr,
                    trnsfr, cl, add_date, parent_contr, enrstat, rank, wisconsin_coven,
                    emailaddr, prog, subprog, upd_uid, add_uid, upd_date, act_choice,
                    stuint_wt, jics_candidate)
                VALUES ({0}, "Y", "{1}", {2}, "{3}", "N", "{4}", "{5}", "", "0.00",
                    "", "0", "{6}", "UNDG", "{7}", "0", "0", "", "", "0", "N");
            ''' .format(apptmp_no, preferredStartTerm, startYear, admissionPlan,
                        studentType, now_date, emailAddress, studentStatus)
            print (q_create_adm)
            scr.write(q_create_adm+'\n');

            # insert into app_proftmp_rec
            q_create_prof = '''
                INSERT INTO app_proftmp_rec
                    (id, birth_date, church_id, prof_last_upd_date)
                VALUES ({0}, "{1}", "{2}", "{3}");
            ''' .format(apptmp_no, dateOfBirth, religiousPreference, now_date)
            print (q_create_prof)
            scr.write(q_create_prof+'\n');

            # select alt_name from app_adretmp_rec
            test_adre = '''
                 SELECT
                     alt_name
                 FROM
                     app_adretmp_rec
                 WHERE
                     prim_id = {0}
                 AND
                     style = "P";
             ''' .format(apptmp_no)
            print (test_adre)
            scr.write(test_adre+'\n');

            # display result for alt_name
            # sqlresult = do_sql(test_adre, earl=EARL)
            # for row in sqlresult:
            #     alt_name = row[0]
            #     print ('Alt Name: {0}'.format(alt_name))

            # insert into app_adretmp_rec
            # q_create_site = '''
            #     INSERT INTO app_adretmp_rec
            #         (prim_id, style, alt_name)
            #     VALUES ({0},
            #             "P",
            #             '{1}'
            #             );
            # ''' .format(apptmp_no, alt_name)
            # print (q_create_site)
            
            # select app_aatmp_no from app_aatmp_rec (MAIL)
            # test_aa_mail = '''
            #     SELECT
            #         app_aatmp_no
            #     FROM
            #         app_aatmp_rec
            #     WHERE
            #         id = {0}
            #     AND
            #         aa = "MAIL";
            # ''' .format(apptmp_no)
            # print (test_aa_mail)
            # scr.write(test_aa_mail+'\n');

            # display result for app_aatmp_no
            # sqlresult = do_sql(test_aa_mail, earl=EARL)
            # for row in sqlresult:
            #     app_aatmp_no = row[0]
            #     print ('AAtemp No: {0}'.format(app_aatmp_no))

            # insert into app_aatmp_rec (MAIL)
            q_insert_aa_mail = '''
                INSERT INTO app_aatmp_rec
                    (line1,line2,city,st,zip,ctry,id,aa,beg_date,end_date)
                VALUES ("{0}", "{1}", "{2}", "{3}", {4}, "{5}", {6}, "MAIL",
                    "{7}", "{8}");
            ''' .format(currentAddress1, currentAddress2, currentAddressCity,
                    currentAddressState, currentAddressZip, currentAddressCountry,
                    apptmp_no, clean_beg_date, clean_end_date)
            print (q_insert_aa_mail)
            scr.write(q_insert_aa_mail+'\n');
        
            # select app_aatmp_no from app_aatmp_rec (BILL)
            # test_aa_bill = '''
            #     SELECT
            #         app_aatmp_no
            #     FROM
            #         app_aatmp_rec
            #     WHERE
            #         id = {0}
            #     AND
            #         aa = "BILL";
            # ''' .format(apptmp_no)
            # print (test_aa_bill)
            # scr.write(test_aa_bill+'\n');
        
            # insert into app_aatmp_rec (BILL)
            # q_insert_aa_bill = '''
            #     INSERT INTO app_aatmp_rec
            #         (line1,line2,city,st,zip,ctry,id,aa,beg_date,end_date)
            #     VALUES ("{0}", "{1}", "{2}", "{3}", {4}, "{5}", {6}, "BILL",
            #         "{7}", "{8}");
            # ''' .format(currentAddress1, currentAddress2, currentAddressCity,
            #             currentAddressState, currentAddressZip,
            #             currentAddressCountry, apptmp_no, clean_beg_date,
            #             clean_end_date)
            # print (q_insert_aa_bill)
            # scr.write(q_insert_aa_bill+'\n');
        
            # select app_aatmp_no from app_aatmp_rec (CELL)
            # test_aa_cell = '''
            #     SELECT
            #         app_aatmp_no
            #     FROM
            #         app_aatmp_rec
            #     WHERE
            #         id = {0}
            #     AND
            #         aa = "CELL";
            # ''' .format(apptmp_no)
            # print (test_aa_cell)
            # scr.write(test_aa_cell+'\n');
        
            # insert into app_aatmp_rec (CELL) *** add CELL for aa
            q_insert_aa_cell = '''
                INSERT INTO app_aatmp_rec
                    (id,aa,beg_date,phone)
                VALUES ({0}, "{1}", "{2}", "{3}");
            ''' .format(apptmp_no, alternatePhoneAvailable, now_date,
                        alternatePhoneNumber)
            print (q_insert_aa_cell)
            scr.write(q_insert_aa_cell+'\n');
            
            # queries from the library.cfc
            # insert into app_idtmp_rec
            q_create_school = '''
                INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                VALUES ({0}, {1}, "{2}", "{3}", "{4}", "{5}", "{6}", "{7}",
                    0, 0, 0, 0, 0, "{8}", "hs", "HS", "N");
            ''' .format(apptmp_no, schoolLookupCeebCode, schoolLookupCeebName,
                        schoolLookupCity, schoolLookupState, graduationDate,
                        entryDate, exitDate, schoolLookupZip)
            print (q_create_school)
            scr.write(q_create_school+'\n\n');
            
            # insert into app_edtmp_rec
            # There is some if logic that might need to be added
            q_text = '''
                INSERT INTO app_edtmp_rec
                    (id, tick, add_date, stat, resrc, txt, due_date)
                VALUES ({0}, "ADM", {1}, "C", "I20",
                        "Applicant expects to need an I-20", {1});
            ''' .format(apptmp_no, now_date)
            print (q_text)
            scr.write(q_text+'\n');

            if relative1FullName.strip():
                # insert into app_edtmp_rec
                q_alumni = "INSERT INTO app_edtmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip)\n VALUES\n ({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)" .format(apptmp_no, relative1FullName, relative1GradYear1)
                if relative2FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative2FullName, relative2GradYear1)
                if relative3FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative3FullName, relative3GradYear1)
                if relative4FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative4FullName, relative4GradYear1)
                if relative5FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative5FullName, relative5GradYear1)
                print (q_alumni)
                scr.write(q_alumni+'\n\n');
            else:  
                print ("Nothing to insert")
                scr.write('--There were no relatives for this application.\n\n');
            # Need to discuss the fields being captured for Siblings, Common App does not have any information about a Sibling if they did not attend college
            if sibling1FullName.strip():
                # insert into app_reltmp_rec
                q_sibing_name = "INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip, prim, addr_line2, suffix)\n VALUES ({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling1FullName, sibling1Age, sibling1CollegeCeebCode, sibling1EducationLevel)
                scr.write('\n');
                if sibling2FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling2FullName, sibling2Age, sibling2CollegeCeebCode, sibling2EducationLevel)
                if sibling3FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling3FullName, sibling3Age, sibling3CollegeCeebCode, sibling3EducationLevel)
                if sibling4FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling4FullName, sibling4Age, sibling4CollegeCeebCode, sibling4EducationLevel)
                if sibling5FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling5FullName, sibling5Age, sibling5CollegeCeebCode, sibling5EducationLevel)
                print (q_sibing_name)
                scr.write(q_sibing_name+'\n\n');
            else:  
                print ("There are not any siblings to insert.")
                scr.write('--There were no siblings for this application.\n\n');
            """
                addr_line1 = <cfqueryparam value="#arguments.form['#parent#_line1']#" CFSQLType="CF_SQL_VARCHAR" />,
                addr_line2 = <cfqueryparam value="#arguments.form['#parent#_line2']#" CFSQLType="CF_SQL_VARCHAR" />,
                city = <cfqueryparam value="#arguments.form['#parent#_city']#" CFSQLType="CF_SQL_VARCHAR" />,
                st = <cfqueryparam value="#arguments.form['#parent#_st']#" CFSQLType="CF_SQL_VARCHAR" />,
                zip = <cfqueryparam value="#arguments.form['#parent#_zip']#" CFSQLType="CF_SQL_VARCHAR" />,
                ctry = <cfqueryparam value="#arguments.form['#parent#_ctry']#" CFSQLType="CF_SQL_VARCHAR" />,
                college = <cfqueryparam value="#arguments.form['#parent#_college']#" CFSQLType="CF_SQL_VARCHAR" />,
                deg_earn = <cfqueryparam value="#arguments.form['#parent#_education']#" CFSQLType="CF_SQL_VARCHAR" />,
                title = <cfqueryparam value="#arguments.form['#parent#_prefix']#" CFSQLType="CF_SQL_VARCHAR" />,
                suffix = <cfqueryparam value="#arguments.form['#parent#_suffix']#" CFSQLType="CF_SQL_VARCHAR" />,
                email = <cfqueryparam value="#arguments.form['#parent#_email']#" CFSQLType="CF_SQL_VARCHAR" />,
                phone = <cfqueryparam value="#arguments.form['#parent#_phone']#" CFSQLType="CF_SQL_VARCHAR" />,
                work_ctc = <cfqueryparam value="#arguments.form['#parent#_permit_contact']#" CFSQLType="CF_SQL_VARCHAR" />,
                job = <cfqueryparam value="#arguments.form['#parent#_pos']#" CFSQLType="CF_SQL_VARCHAR" />,
                employer = <cfqueryparam value="#arguments.form['#parent#_bus']#" CFSQLType="CF_SQL_VARCHAR" />
            """
            # insert into partmp_rec
            if parent1Type == 'Father':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, f_first_name, f_last_name, f_zip)\n VALUES (0, {0}, \"{1}\", \"{2}\", 0);\n" .format(apptmp_no, parent1FirstName, parent1LastName)
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            elif parent1Type == 'Mother':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, m_first_name, m_last_name, m_zip)\n VALUES (0, {0}, \"{1}\", \"{2}\", 0);\n" .format(apptmp_no, parent1FirstName, parent1LastName)
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no Parent 1")
                scr.write('--There was no Parent 1 for this application.\n\n');

            if parent2Type == 'Mother':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, m_first_name, m_last_name, m_zip)\n VALUES (0, {0}, \"{1}\", \"{2}\", 0);\n" .format(apptmp_no, parent2FirstName, parent2LastName)
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            elif parent2Type == 'Father':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, f_first_name, f_last_name, f_zip)\n VALUES (0, {0}, \"{1}\", \"{2}\", 0);\n" .format(apptmp_no, parent2FirstName, parent2LastName)
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no Parent 2")
                scr.write('--There was no Parent 2 for this application.\n\n');

            if legalGuardianFullName.strip():
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, g_first_name, g_last_name, g_zip)\n VALUES (0, {0}, \"{1}\", \"{2}\", 0);\n" .format(apptmp_no, legalGuardianFirstName, legalGuardianLastName)
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no legal guardian.")
                scr.write('--There was no legal guardian for this application.\n\n');

            # Need to discuss with Mike to show him the activities and within the CommonApp tab Activities can help a college better understand your life outside of the classroom. Your activities may include arts, athletics, clubs, employment, personal commitments, and other pursuits. Do you have any activities that you wish to report?
            # insert into app_inttmp_rec
            if activity1.strip():
                insert_interests = "INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry, cclevel)\n VALUES ({0}, 0, \"{1}\", "", \"Y\");\n" .format(apptmp_no, activity1)
                if activity2.strip():
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity2)
                if activity3.strip():
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity3)
                if activity4.strip():
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity4)
                if activity5.strip():
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity5)
                print (insert_interests)
                scr.write(insert_interests+'\n');
            else:  
                print ("Zero interests")
                scr.write('--The was no activities for this application.\n\n');
            ## if list of converted > 1
            for eth_race in converted:
                # insert into app_mracetmp_rec
                insert_races = '''
                    INSERT INTO app_mracetmp_rec
                        (id, race)
                    VALUES ({0}, "{1}");\n
                ''' .format(apptmp_no, eth_race)
                print (insert_races)
                scr.write(insert_races+'\n');

            
            # remove ethinc_code just keep race
            # insert into app_proftmp_rec
            if ethnic_code == 'UN':
                q_optional_2 = "INSERT INTO app_proftmp_rec (id, ethnic_code, race, hispanic) VALUES ({0}, \"UN\", \"{1}\", \"{2}\")" .format(apptmp_no, eth_race, hispanicLatino)
                print (q_optional_2)
                scr.write(q_optional_2+'\n');
            elif ethnic_code == 'MU':
                q_optional_2 = "INSERT INTO app_proftmp_rec (id, ethnic_code, race, hispanic) VALUES ({0}, \"MU\", \"{1}\", \"{2}\")" .format(apptmp_no, eth_race, hispanicLatino)
                print (q_optional_2)
                scr.write(q_optional_2+'\n');
            else:
                q_optional_1 = '''
                INSERT INTO app_proftmp_rec (id, ethnic_code, race, hispanic)
                VALUES ({0}, \"{1}\", \"{2}\", \"{3}\");
            ''' .format(apptmp_no, eth_race, eth_race, hispanicLatino)
            print (q_optional_1)
            scr.write(q_optional_1+'\n');

            # creating Testing Scores array for ACT, SAT_New
            tests_array = []
            for test in totalTestsTaken.split(','):
                tests_array.append(test.strip())
                print(tests_array)

            for tests in tests_array:
                q_exam = "INSERT INTO app_examtmp_rec (id, ctgry, cmpl_date, self_rpt, site, score1, score2, score3, score4, score5, score6)\n"
                if tests == 'ACT' and ACTCompositeScore != '':
                    # insert into app_examtmp_rec
                    q_exam += " VALUES ({0}, \"ACT\", {1}, \"Y\", \"CART\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\")" .format(apptmp_no, actCompositeDate, ACTCompositeScore, ACTEnglishScore, ACTMathScore, ACTReadingScore, ACTScienceScore, ACTWritingScore)
                    print (q_exam)
                    scr.write(q_exam+'\n');
                if tests == 'SAT_New' and (SATRWScore != '' or SATMathScore != '' or SATEssayScore != ''):
                    q_exam += " VALUES ({0}, \"SAT\", \"{1}\", \"Y\", \"CART\", \"\", \"{2}\", \"{3}\", \"{4}\", \"\", \"\")" .format(apptmp_no, SATRWDate, SATRWScore, SATMathScore, SATEssayScore)
                    print (q_exam)
                    scr.write(q_exam+'\n');
            scr.write('--------------------------------------------------------------------------------\n')
            scr.write('-- END INSERT NEW STUDENT APPLICATION for: ' + firstName + ' ' + lastName + "\n")
            scr.write('--------------------------------------------------------------------------------\n\n')
        f.close()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
