import os
import sys
import pysftp
import csv
import datetime
from datetime import date
#from datetime import timedelta
#import time
#from time import gmtime, strftime
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

    with open(filename, 'rb') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            print([col+'='+row[col] for col in reader.fieldnames])

            # set apptmp_no counter to generate fake application number
            apptmp_no = random.randint(100000, 500000)
            # create UUID
            temp_uuid = (uuid.uuid4())
            print ('UUID: {0}'.format(temp_uuid))

            scr.write('---------------------------------------------------------------------------------------------\n')
            scr.write('-- START INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('---------------------------------------------------------------------------------------------\n')

            # insert into apptmp_rec
            q_create_app = '''
                INSERT INTO apptmp_rec
                    (add_date, add_tm, app_source, stat, reason_txt)
                VALUES ("TODAY", TO_CHAR(CURRENT, '%H%M'), "WEBA", "H", "{0}");
            ''' .format(temp_uuid)
            print (q_create_app)
            scr.write(q_create_app+'\n');

            # fetch apptmp_no
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

            ##################################################################################
            # The Y/N value of contactConsent may seem a little backwards intuitively.
            # Y = The student has opted out meaning Carthage does NOT have permission to text
            # N = The student has opted in meaning Carthage does have permission to text
            #################################################################################
            if row["preferredPhone"] != '':
                if row["preferredPhone"] == 'Mobile':
                    if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                        contactConsent = 'N'
                    elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                        contactConsent = 'Y'
                    q_insert_aa_cell = '''
                        INSERT INTO app_aatmp_rec
                        (id,aa,beg_date,phone,opt_out)
                        VALUES ({0}, "CELL", "TODAY", "{1}", "{2}");
                    ''' .format(apptmp_no, row["preferredPhoneNumber"].replace('+1.', ''),
                                row["contactConsent"])
                    print (q_insert_aa_cell)
                    scr.write(q_insert_aa_cell+'\n');
                if row["alternatePhoneAvailable"] == 'Mobile':
                    q_create_id = '''
                        INSERT INTO app_idtmp_rec
                            (id, firstname, lastname, cc_username, cc_password,
                            addr_line1, addr_line2, city, st, zip, ctry, phone,
                            aa, add_date, ofc_add_by, upd_date, purge_date,
                            prsp_no, name_sndx, correct_addr, decsd, valid)
                        VALUES ({0}, "{1}", "{2}", "{3}", "{0}", "{4}", "{5}",
                            "{6}", "{7}", {8},"{9}","{10}","PERM","TODAY","ADMS",
                            "TODAY","TODAY + 2 UNITS YEAR","0","", "Y","N","Y");
                    ''' .format(apptmp_no, row["firstName"], row["lastName"],
                                row["emailAddress"],row["permanentAddress1"],
                                row["permanentAddress2"], row["permanentAddressCity"],
                            row["permanentAddressState"], row["permanentAddressZip"],
                            row["permanentAddressCountry"],
                            row["preferredPhoneNumber"].replace('+1.', ''))
                    print (q_create_id)
                    print (apptmp_no)
                    scr.write(q_create_id+'\n');
                else:
                    # insert into app_idtmp_rec
                    q_create_id = '''
                        INSERT INTO app_idtmp_rec
                            (id, firstname, lastname, cc_username, cc_password,
                            addr_line1, addr_line2, city, st, zip, ctry, phone,
                            aa, add_date, ofc_add_by, upd_date, purge_date,
                            prsp_no, name_sndx, correct_addr, decsd, valid)
                        VALUES ({0}, "{1}", "{2}", "{3}", "{0}", "{4}", "{5}",
                            "{6}", "{7}", "{8}","{9}","{10}","PERM","TODAY","ADMS",
                            "TODAY","TODAY + 2 UNITS YEAR","0","", "Y","N","Y");
                    ''' .format(apptmp_no, row["firstName"], row["lastName"],
                                row["emailAddress"],row["permanentAddress1"],
                                row["permanentAddress2"], row["permanentAddressCity"],
                            row["permanentAddressState"], row["permanentAddressZip"],
                            row["permanentAddressCountry"],
                            row["preferredPhoneNumber"].replace('+1.', ''))
                    print (q_create_id)
                    print (apptmp_no)
                    scr.write(q_create_id+'\n');
            
            q_create_site = '''
                INSERT INTO app_sitetmp_rec
                    (id, home, site, beg_date)
                VALUES ({0}, "Y", "CART", "TODAY");
            ''' .format(apptmp_no)
            print (q_create_site)
            scr.write(q_create_site+'\n');

            # determine the type of studentStatus and Hours Enrolled
            if row["studentStatus"] == 'Full Time' or row["transferStudentStatus"] == 'Full Time':
                studentStatus = 'TRAD'
                intendHoursEnrolled = 16
            elif row["studentStatus"] == 'Part Time' or row["transferStudentStatus"] == 'Part Time':
                studentStatus = 'TRAP'
                intendHoursEnrolled = 4

            # determine the type of preferredStartTerm
            if row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RA' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RA':
                preferredStartTerm = 'RA'
            elif row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RC' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RC':
                preferredStartTerm = 'RC'
            elif row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RB' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RB':
                preferredStartTerm = 'RB'

            # determine the type of studentType
            if row["studentType"] == 'FY':
                studentType = 'FF'
                transfer = 'N'
            elif row["studentType"] == 'TR':
                studentType = 'UT'
                transfer = 'Y'

            # insert into app_admtmp_rec
            q_create_adm = '''
                INSERT INTO app_admtmp_rec
                    (id, primary_app, plan_enr_sess, plan_enr_yr, intend_hrs_enr,
                    trnsfr, cl, add_date, parent_contr, enrstat, rank, wisconsin_coven,
                    emailaddr, prog, subprog, upd_date, act_choice, stuint_wt,
                    jics_candidate)
                VALUES ({0}, "Y", "{1}", {2}, "{3}", "{4}", "{5}", "TODAY", "0.00",
                    "", "0", "", "{6}", "UNDG", "{7}", "TODAY", "", "0", "N");
            ''' .format(apptmp_no, preferredStartTerm, row["startYear"],
                        intendHoursEnrolled, transfer, studentType,
                        row["emailAddress"], studentStatus)
            print (q_create_adm)
            scr.write(q_create_adm+'\n');

            if row["alternateAddressAvailable"] == 'Y':
                q_insert_aa_mail = '''
                    INSERT INTO app_aatmp_rec
                        (line1,line2,city,st,zip,ctry,id,aa)
                    VALUES ("{0}", "{1}", "{2}", "{3}", {4}, "{5}", {6}, "MAIL");
                ''' .format(row["currentAddress1"],row["currentAddress2"],
                        row["currentAddressCity"],row["currentAddressState"],
                        row["currentAddressZip"],row["currentAddressCountry"],
                        apptmp_no)
                print (q_insert_aa_mail)
                scr.write(q_insert_aa_mail+'\n');
            else:
                print ("There were no alternate addresses for this application.")
                scr.write('--There were no alternate addresses for this application.\n\n');

            ##################################################################################
            # The Y/N value of contactConsent may seem a little backwards intuitively.
            # Y = The student has opted out meaning Carthage does NOT have permission to text
            # N = The student has opted in meaning Carthage does have permission to text
            #################################################################################
            # determine the type of contactConsent
            if row["alternatePhoneNumber"] != '' and row["alternatePhoneNumber"] != 'N':
                if row["contactConsent"] == 'Y' or row["transferContactConsent"] == 'Y':
                    contactConsent = 'N'
                elif row["contactConsent"] == 'N' or row["transferContactConsent"] == 'N':
                    contactConsent = 'Y'
                if row["alternatePhoneAvailable"] == 'Mobile':
                    # insert into app_aatmp_rec (CELL)
                    q_insert_aa_cell = '''
                        INSERT INTO app_aatmp_rec
                            (id,aa,beg_date,phone,opt_out)
                        VALUES ({0}, "CELL", "TODAY", "{1}", "{2}");
                    ''' .format(apptmp_no, row["alternatePhoneNumber"].replace('+1.', ''),
                                row["contactConsent"])
                    print (q_insert_aa_cell)
                    scr.write(q_insert_aa_cell+'\n');
                else:
                    q_create_id = '''
                        INSERT INTO app_idtmp_rec
                            (id, firstname, lastname, cc_username, cc_password,
                            addr_line1, addr_line2, city, st, zip, ctry, phone,
                            aa, add_date, ofc_add_by, upd_date, purge_date,
                            prsp_no, name_sndx, correct_addr, decsd, valid)
                        VALUES ({0}, "{1}", "{2}", "{3}", "{0}", "{4}", "{5}",
                            "{6}", "{7}", "{8}","{9}","{10}","PERM","TODAY","ADMS",
                            "TODAY","TODAY + 2 UNITS YEAR","0","", "Y","N","Y");
                    ''' .format(apptmp_no, row["firstName"], row["lastName"],
                                row["emailAddress"],row["permanentAddress1"],
                                row["permanentAddress2"], row["permanentAddressCity"],
                            row["permanentAddressState"], row["permanentAddressZip"],
                            row["permanentAddressCountry"],
                            row["preferredPhoneNumber"].replace('+1.', ''))
                    print (q_create_id)
                    print (apptmp_no)
                    scr.write(q_create_id+'\n');

            # formatting the graduationDate
            if row["graduationDate"] == '':
                graduationDate = ''
            else:
                graduationDate = datetime.datetime.strptime(row["graduationDate"], '%m/%Y').strftime('%Y-%m-01')
            # formatting the entryDate
            if row["entryDate"] == '':
                entryDate = ''
            else:
                entryDate = datetime.datetime.strptime(row["entryDate"], '%m/%Y').strftime('%Y-%m-01')
            # formatting the exitDate
            if row["exitDate"] == '':
                exitDate = ''
            else:
                exitDate = datetime.datetime.strptime(row["exitDate"], '%m/%Y').strftime('%Y-%m-01')

            # insert into app_idtmp_rec
            q_create_school = '''
                INSERT INTO app_edtmp_rec
                    (id, ceeb, fullname, city, st, grad_date, enr_date, dep_date,
                    stu_id, sch_id, app_reltmp_no, rel_id, priority, zip, aa, ctgry,
                    acad_trans)
                VALUES ({0}, {1}, "{2}", "{3}", "{4}", "{5}", "{6}", "{7}",
                    0, 0, 0, 0, 0, "{8}", "hs", "HS", "N");
            ''' .format(apptmp_no,row["schoolLookupCeebCode"],row["schoolLookupCeebName"],
                    row["schoolLookupCity"], row["schoolLookupState"], graduationDate,
                    entryDate, exitDate, row["schoolLookupZip"])
            print (q_create_school)
            scr.write(q_create_school+'\n\n');

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

                # insert into realatives app_edtmp_rec
                if row["relative1FirstName"].strip():
                    q_alumni = "INSERT INTO app_edtmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip)\n VALUES\n ({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)" .format(apptmp_no, row["relative1FirstName"] + ' ' + row["relative1LastName"], row["relative1GradYear1"])
                    if row["relative2FirstName"].strip():
                        q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, row["relative2FirstName"] + ' ' + row["relative2LastName"], row["relative2GradYear1"])
                    if row["relative3FirstName"].strip():
                        q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, row["relative3FirstName"] + ' ' + row["relative3LastName"], row["relative3GradYear1"])
                    if row["relative4FirstName"].strip():
                        q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, row["relative4FirstName"] + ' ' + row["relative4LastName"], row["relative4GradYear1"])
                    if row["relative5FirstName"].strip():
                        q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, row["relative5FirstName"] + ' ' + row["relative5LastName"], row["relative5GradYear1"])
                    print (q_alumni)
                    scr.write(q_alumni+'\n\n');
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
                    # insert siblings into app_reltmp_rec
                    q_sibing_name = "INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip, prim, addr_line2, suffix)\n VALUES ({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, row["sibling1FirstName"] + ' ' + row["sibling1LastName"], row["sibling1Age"], row["sibling1CollegeCeebName"],sibling1EducationLevel)
                if row["sibling2FirstName"].strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, row["sibling2FirstName"] + ' ' + row["sibling2LastName"], row["sibling2Age"], row["sibling2CollegeCeebName"], sibling2EducationLevel)
                if row["sibling3FirstName"].strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, row["sibling3FirstName"] + ' ' + row["sibling3LastName"], row["sibling3Age"], row["sibling3CollegeCeebName"], sibling3EducationLevel)
                if row["sibling4FirstName"].strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, row["sibling4FirstName"] + ' ' + row["sibling4LastName"], row["sibling4Age"], row["sibling4CollegeCeebName"], sibling4EducationLevel)
                if row["sibling5FirstName"].strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, row["sibling5FirstName"] + ' ' + row["sibling5LastName"], row["sibling5Age"], row["sibling5CollegeCeebName"], sibling5EducationLevel)
                print (q_sibing_name)
                scr.write(q_sibing_name+'\n\n');
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

            # setting activities variable
            activity1 = row["activity1"].strip()
            if len(row["transferActivity1"]):
                activity1 = row["transferActivity1"].strip()
            activity2 = row["activity2"].strip()
            if len(row["transferActivity2"]):
                activity2 = row["transferActivity2"].strip()
            activity3 = row["activity3"].strip()
            if len(row["transferActivity3"]):
                activity3 = row["transferActivity3"].strip()
            activity4 = row["activity4"].strip()
            if len(row["transferActivity4"]):
                activity4 = row["transferActivity4"].strip()
            activity5 = row["activity5"].strip()
            if len(row["transferActivity5"]):
                activity5 = row["transferActivity5"].strip()

            # insert into app_inttmp_rec
            if activity1:
                insert_interests = "INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry, cclevel)\n VALUES ({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity1)
                if activity2:
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity2)
                if activity3:
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity3)
                if activity4:
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity4)
                if activity5:
                    insert_interests += ",({0}, 0, \"{1}\", "", \"Y\")\n" .format(apptmp_no, activity5)
                print (insert_interests)
                scr.write(insert_interests+'\n');
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

            for eth_race in converted:
                # insert into app_mracetmp_rec
                insert_races = '''
                    INSERT INTO app_mracetmp_rec
                        (id, race)
                    VALUES ({0}, "{1}");\n
                ''' .format(apptmp_no, eth_race)
                print (insert_races)
                scr.write(insert_races+'\n');

            # formatting the dateOfBirth
            dateOfBirth = datetime.datetime.strptime(row["dateOfBirth"], '%m/%d/%Y').strftime('%Y-%m-%d')

            # armedForcesStatus variables
            if row["armedForcesStatus"] == 'Currently_serving':
                armedForcesStatus = 'Y'
            elif row["armedForcesStatus"] == 'Previously_served':
                armedForcesStatus = 'Y'
            elif row["armedForcesStatus"] == 'Current_Dependent':
                armedForcesStatus = 'Unknown'
            else:
                armedForcesStatus = 'N'

            # insert into app_proftmp_rec
            if ethnic_code == 'UN':
                q_create_prof = "INSERT INTO app_proftmp_rec (id, birth_date, church_id, prof_last_upd_date, sex, birthplace_city, birthplace_st, birthplace_ctry, visa_code, citz, res_st, res_cty, race, hispanic, denom_code, vet) VALUES ({0}, \"{1}\", 0, \"TODAY\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"\", \"{6}\", \"\", \"\", \"UN\", \"{7}\", \"{8}\", \"{9}\")" .format(apptmp_no, dateOfBirth, row["sex"], row["birthCity"], row["birthState"], row["birthCountry"], row["citizenships"], row["hispanicLatino"], row["religiousPreference"], armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
            elif ethnic_code == 'MU':
                q_create_prof = "INSERT INTO app_proftmp_rec (id, birth_date, church_id, prof_last_upd_date, sex, birthplace_city, birthplace_st, birthplace_ctry, visa_code, citz, res_st, res_cty, race, hispanic, denom_code, vet) VALUES ({0}, \"{1}\", 0, \"TODAY\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"\", \"{6}\", \"\", \"\", \"MU\", \"{7}\", \"{8}\", \"{9}\")" .format(apptmp_no, dateOfBirth, row["sex"], row["birthCity"], row["birthState"], row["birthCountry"], row["citizenships"], row["hispanicLatino"], row["religiousPreference"], armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');
            else:
                q_create_prof = '''
                    INSERT INTO app_proftmp_rec (id, birth_date, church_id,
                    prof_last_upd_date, sex, birthplace_city, birthplace_st,
                    birthplace_ctry, visa_code, citz, res_st, res_cty, race,
                    hispanic, denom_code, vet)
                    VALUES ({0}, "{1}", 0, "TODAY", "{2}", "{3}", "{4}",
                    "{5}", "", "{6}", "", "", "{7}", "{8}", "{9}", "{10}");
                ''' .format(apptmp_no, dateOfBirth, row["sex"],
                        row["birthCity"], row["birthState"], row["birthCountry"],
                        row["citizenships"], eth_race, row["hispanicLatino"],
                        row["religiousPreference"], armedForcesStatus)
                print (q_create_prof)
                scr.write(q_create_prof+'\n');

            # creating Testing Scores array for ACT, SAT_New
            tests_array = []
            for test in row["totalTestsTaken"].split(','):
                tests_array.append(test.strip())
                print(tests_array)

            for tests in tests_array:
                q_exam = "INSERT INTO app_examtmp_rec (id, ctgry, cmpl_date, self_rpt, site, score1, score2, score3, score4, score5, score6)\n"
                if tests == 'ACT' and row["ACTCompositeScore"] != '':
                    # insert into app_examtmp_rec
                    q_exam += " VALUES ({0}, \"ACT\", {1}, \"Y\", \"CART\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\")" .format(apptmp_no, row["actCompositeDate"], row["ACTCompositeScore"], row["ACTEnglishScore"], row["ACTMathScore"], row["ACTReadingScore"], row["ACTScienceScore"], row["ACTWritingScore"])
                    print (q_exam)
                    scr.write(q_exam+'\n');
                if tests == 'SAT_New' and (row["SATRWScore"] != '' or row["SATMathScore"] != '' or row["SATEssayScore"] != ''):
                    q_exam += " VALUES ({0}, \"SAT\", \"{1}\", \"Y\", \"CART\", \"\", \"{2}\", \"{3}\", \"{4}\", \"\", \"\")" .format(apptmp_no, row["SATRWDate"], row["SATRWScore"], row["SATMathScore"], row["SATEssayScore"])
                    print (q_exam)
                    scr.write(q_exam+'\n');

            scr.write('-------------------------------------------------------------------------------------------\n')
            scr.write('-- END INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('-----------------------------------------------------------------------------------------\n\n')

        f.close()


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())