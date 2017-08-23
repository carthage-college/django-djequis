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

            # Set apptmp_no counter to generate fake application number
            apptmp_no = random.randint(100000, 500000)
            # Creating the UUID
            temp_uuid = (uuid.uuid4())
            print ('UUID: {0}'.format(temp_uuid))

            scr.write('--------------------------------------------------------------------------------\n')
            scr.write('-- START INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('--------------------------------------------------------------------------------\n')

            # insert into apptmp_rec
            q_create_app = '''
                INSERT INTO apptmp_rec
                    (add_date, add_tm, app_source, stat, reason_txt)
                VALUES ("TODAY", TO_CHAR(CURRENT, '%H%M'), "WEBA", "H", "{0}");
            ''' .format(temp_uuid)
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

            # Determine the type of studentStatus and Hours Enrolled
            if row["studentStatus"] == 'Full Time' or row["transferStudentStatus"] == 'Full Time':
                studentStatus = 'TRAD'
                intendHoursEnrolled = 16
            elif row["studentStatus"] == 'Part Time' or row["transferStudentStatus"] == 'Part Time':
                studentStatus = 'TRAP'
                intendHoursEnrolled = 4

            # Determine the type of preferredStartTerm
            if row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RA' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RA':
                preferredStartTerm = 'RA'
            elif row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RC' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RC':
                preferredStartTerm = 'RC'
            elif row["preferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RB' or row["transferPreferredStartTerm"] == 'ADM-PLAN_ENR_SESS-RB':
                preferredStartTerm = 'RB'

            # Determine the type of studentType
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
            # Determine the type of contactConsent
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

            # Setting Relative First Name
            relative1FirstName = row["relative1FirstName"] or row["transferRelative1FirstName"]
            relative2FirstName = row["relative1FirstName"] or row["transferRelative2FirstName"]
            relative3FirstName = row["relative3FirstName"] or row["transferRelative3FirstName"]
            relative4FirstName = row["relative1FirstName"] or row["transferRelative4FirstName"]
            relative5FirstName = row["relative5FirstName"] or row["transferRelative5FirstName"]
            # Setting Relative Last Name
            relative1LastName = row["relative1LastName"] or row["transferRelative1LastName"]
            relative2LastName = row["relative2LastName"] or row["transferRelative2LastName"]
            relative3LastName = row["relative3LastName"] or row["transferRelative3LastName"]
            relative4LastName = row["relative4LastName"] or row["transferRelative4LastName"]
            relative5LastName = row["relative5LastName"] or row["transferRelative5LastName"]
            # Setting Relative Full Name
            relative1FullName = (relative1FirstName + ' ' + relative1LastName)
            relative2FullName = (relative2FirstName + ' ' + relative2LastName)
            relative3FullName = (relative3FirstName + ' ' + relative3LastName)
            relative4FullName = (relative4FirstName + ' ' + relative4LastName)
            relative5FullName = (relative5FirstName + ' ' + relative5LastName)
            # Setting Relative Graduation Year
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

            if relative1FullName.strip():
                # insert into app_edtmp_rec
                q_alumni = "INSERT INTO app_edtmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip)\n VALUES\n ({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)" .format(apptmp_no, relative1FullName, row["relative1GradYear1"])
                if relative2FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative2FullName, row["relative2GradYear1"])
                if relative3FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative3FullName, row["relative3GradYear1"])
                if relative4FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative4FullName, row["relative4GradYear1"])
                if relative5FullName.strip():
                    q_alumni += ",({0}, 0, 5, \"{1}\", {2}, \"ALUM\", 0)\n" .format(apptmp_no, relative5FullName, row["relative5GradYear1"])
                print (q_alumni)
            else:  
                print ("Nothing to insert")
                scr.write('--There were no relatives for this application.\n\n');

            # Setting Sibling First Name
            sibling1FirstName = row["sibling1FirstName"]
            sibling2FirstName = row["sibling2FirstName"]
            sibling3FirstName = row["sibling3FirstName"]
            sibling4FirstName = row["sibling4FirstName"]
            sibling5FirstName = row["sibling5FirstName"]
            # Setting Sibling Last Name
            sibling1LastName = row["sibling1LastName"]
            sibling2LastName = row["sibling2LastName"]
            sibling3LastName = row["sibling3LastName"]
            sibling4LastName = row["sibling4LastName"]
            sibling5LastName = row["sibling5LastName"]
            # Setting Sibling Full Name
            sibling1FullName = (sibling1FirstName + ' ' + sibling1LastName)
            sibling2FullName = (sibling2FirstName + ' ' + sibling2LastName)
            sibling3FullName = (sibling3FirstName + ' ' + sibling3LastName)
            sibling4FullName = (sibling4FirstName + ' ' + sibling4LastName)
            sibling5FullName = (sibling5FirstName + ' ' + sibling5LastName)

            # Set dictionary for Sibling education level
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
            if sibling1FullName.strip():
                # insert into app_reltmp_rec
                q_sibing_name = "INSERT INTO app_reltmp_rec (id, rel_id, rel, fullname, phone_ext, aa, zip, prim, addr_line2, suffix)\n VALUES ({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", {3}, \"{4}\")\n" .format(apptmp_no, sibling1FullName, row["sibling1Age"], row["sibling1CollegeCeebName"],sibling1EducationLevel)
                if sibling2FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, sibling2FullName, row["sibling2Age"], row["sibling2CollegeCeebName"], sibling2EducationLevel)
                if sibling3FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, sibling3FullName, row["sibling3Age"], row["sibling3CollegeCeebName"], sibling3EducationLevel)
                if sibling4FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, sibling4FullName, row["sibling4Age"], row["sibling4CollegeCeebName"], sibling4EducationLevel)
                if sibling5FullName.strip():
                    q_sibing_name += ",({0}, 0, \"SIB\", \"{1}\", {2}, \"SBSB\", 0, \"Y\", \"{3}\", \"{4}\")\n" .format(apptmp_no, sibling5FullName, row["sibling5Age"], row["sibling5CollegeCeebName"], sibling5EducationLevel)
                print (q_sibing_name)
                scr.write(q_sibing_name+'\n\n');
            else:  
                print ("There are not any siblings to insert.")
                scr.write('--There were no siblings for this application.\n\n');

            # insert into partmp_rec
            if row["parent1Type"] == 'Father':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, f_first_name, f_last_name, f_addr_line1, f_addr_line2, f_city, f_st, f_zip, f_ctry, f_college, f_deg_earn, f_title, f_suffix, f_email, f_phone, f_job, f_employer)\n VALUES ({0}, 0, \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\", \"{8}\", \"{9}\", \"{10}\", \"{11}\", \"{12}\", \"{13}\", \"{14}\", \"{15}\", \"{16}\");\n" .format(apptmp_no,row["parent1FirstName"],row["parent1LastName"],row["parent1Address1"],row["parent1Address2"],row["parent1AddressCity"],row["parent1AddressState"],row["parent1AddressZip"],row["parent1AddressCountry"],row["parent1College1NameCeebName"],row["parent1College1Degree1"],row["parent1Title"],row["parent1Suffix"],row["parent1Email"],row["parent1Phone"].replace('+1.', ''),row["parent1Occupation"],row["parent1Employer"])
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            elif row["parent1Type"] == 'Mother':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, m_first_name, m_last_name, m_addr_line1, m_addr_line2, m_city, m_st, m_zip, m_ctry, m_college, m_deg_earn, m_title, m_suffix, m_email, m_phone, m_job, m_employer))\n VALUES ({0}, 0, \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\", \"{8}\", \"{9}\", \"{10}\", \"{11}\", \"{12}\", \"{13}\", \"{14}\", \"{15}\", \"{16}\");\n" .format(apptmp_no, "",row["parent1FirstName"],row["parent1LastName"],row["parent1Address1"],row["parent1Address2"],row["parent1AddressCity"],row["parent1AddressState"],row["parent1AddressZip"],row["parent1AddressCountry"],row["parent1College1NameCeebName"],row["parent1College1Degree1"],row["parent1Title"],row["parent1Suffix"],row["parent1Email"],row["parent1Phone"].replace('+1.', ''),row["parent1Occupation"],row["parent1Employer"])
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no Parent 1")
                scr.write('--There was no Parent 1 for this application.\n\n');

            if row["parent2Type"] == 'Mother':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, m_first_name, m_last_name, m_addr_line1, m_addr_line2, m_city, m_st, m_zip, m_ctry, m_college, m_deg_earn, m_title, m_suffix, m_email, m_phone, m_job, m_employer))\n VALUES ({0}, 0, \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\", \"{8}\", \"{9}\", \"{10}\", \"{11}\", \"{12}\", \"{13}\", \"{14}\", \"{15}\", \"{16}\");\n" .format(apptmp_no, "",row["parent2FirstName"],row["parent2LastName"],row["parent2Address1"],row["parent2Address2"],row["parent2AddressCity"],row["parent2AddressState"],row["parent2AddressZip"],row["parent2AddressCountry"],row["parent2College1NameCeebName"],row["parent2College1Degree1"],row["parent2Title"],row["parent2Suffix"],row["parent2Email"],row["parent2Phone"].replace('+1.', ''),row["parent2Occupation"],row["parent2Employer"])
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            elif row["parent2Type"] == 'Father':
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, f_first_name, f_last_name, f_addr_line1, f_addr_line2, f_city, f_st, f_zip, f_ctry, f_college, f_deg_earn, f_title, f_suffix, f_email, f_phone, f_job, f_employer)\n VALUES ({0}, 0, \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\", \"{8}\", \"{9}\", \"{10}\", \"{11}\", \"{12}\", \"{13}\", \"{14}\", \"{15}\", \"{16}\");\n" .format(apptmp_no,row["parent2FirstName"],row["parent2LastName"],row["parent2Address1"],row["parent2Address2"],row["parent2AddressCity"],row["parent2AddressState"],row["parent2AddressZip"],row["parent2AddressCountry"],row["parent2College1NameCeebName"],row["parent2College1Degree1"],row["parent2Title"],row["parent2Suffix"],row["parent2Email"],row["parent2Phone"].replace('+1.', ''),row["parent2Occupation"],row["parent2Employer"]) 
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no Parent 2")
                scr.write('--There was no Parent 2 for this application.\n\n');

            # Setting Legal Guardian First Name
            legalGuardianFirstName = row["legalGuardianFirstName"]
            # Setting Legal Guardian Last Name
            legalGuardianLastName = row["legalGuardianLastName"]
            # Setting Sibling Full Name
            legalGuardianFullName = (legalGuardianFirstName + ' ' + legalGuardianLastName)

            if legalGuardianFullName.strip():
                q_insert_partmp_rec = "INSERT INTO partmp_rec (id, app_no, g_first_name, g_last_name, g_addr_line1, g_addr_line2, g_city, g_st, g_zip, g_ctry, g_college, g_deg_earn, g_title, g_suffix, g_email, g_phone, g_job, g_employer)\n VALUES ({0}, 0, \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\", \"{8}\", \"{9}\", \"{10}\", \"{11}\", \"{12}\", \"{13}\", \"{14}\", \"{15}\", \"{16}\");\n" .format(apptmp_no,row["legalGuardianFirstName"],row["legalGuardianLastName"],row["legalGuardianAddress1"],row["legalGuardianAddress2"],row["legalGuardianAddressCity"],row["legalGuardianAddressState"],row["legalGuardianAddressZip"],row["legalGuardianAddressCountry"],row["legalGuardianCollege1NameCeebName"],row["legalGuardianCollege1Degree1"],row["legalGuardianTitle"],row["legalGuardianSuffix"],row["legalGuardianEmail"],row["legalGuardianPhone"].replace('+1.', ''),row["legalGuardianOccupation"],row["legalGuardianEmployer"])
                print (q_insert_partmp_rec)
                scr.write(q_insert_partmp_rec+'\n');
            else:
                print ("There is no legal guardian.")
                scr.write('--There was no legal guardian for this application.\n\n');

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
                insert_interests = "INSERT INTO app_inttmp_rec (id, prsp_no, interest, ctgry, cclevel)\n VALUES ({0}, 0, \"{1}\", "", \"Y\");\n" .format(apptmp_no, activity1)
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
                print ("The was no activities for this application.")
                scr.write('--The was no activities for this application.\n\n');

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
            scr.write('--------------------------------------------------------------------------------\n')
            scr.write('-- END INSERT NEW STUDENT APPLICATION for: ' + row["firstName"] + ' ' + row["lastName"] + "\n")
            scr.write('--------------------------------------------------------------------------------\n\n')

        f.close()


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())