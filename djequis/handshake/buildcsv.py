import os
import sys
# import pysftp
import csv
from datetime import datetime
import time
from time import strftime
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler

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
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine

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
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY

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

# write out the .sql file
# scr = open("handshake_output.sql", "a")

def main():
    # set start_time in order to see how long script takes to execute
    # start_time = time.time()

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python adptocx.py --database=train --test
    # production server (psm), you would execute:
    # ==> python adptocx.py --database=cars
    # without the --test argument
    ##########################################################################

    # set date and time to be added to the filename
    # datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Defines file names and directory location
    handshakedata = ('handshake.csv'.format(
         settings.HANDSHAKE_CSV_OUTPUT
    ))

    # First remove yesterdays file of updates
    # if os.path.isfile(adp_diff_file):
    #     os.remove(adp_diff_file)

    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        # if database == 'cars':
        #     EARL = INFORMIX_EARL_PROD
        if database == 'train':
            EARL = INFORMIX_EARL_TEST
        else:
        # this will raise an error when we call get_engine()
        # below but the argument parser should have taken
        # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)

        # with open(handshakedata, 'wb') as file_out:
        with open("handshakedata.csv", 'wb') as file_out:
            # Write header row
            csvWriter = csv.writer(file_out)
            csvWriter.writerow(
                ["email_address", "username", "auth_identifier" ,"card_id",
                 "first_name", "last_name", "middle_name", "preferred_name",
                 "school_year_name", "primary_education:education_level_name",
                 "primary_education:cumulative_gpa",
                 "primary_education:department_gpa",
                 "primary_education:primary_major_name",
                 "primary_education:major_names",
                 "primary_education:minor_names",
                 "primary_education:college_name",
                 "primary_education:start_date",
                 "primary_education:end_date",
                 "primary_education:currently_attending",
                 "campus_name", "opt_cpt_eligible", "ethnicity", "gender",
                 "disabled", "work_study_eligible", "system_label_names",
                 "mobile_number", "assigned_to_email_address", "athlete",
                 "veteran", "hometown_location_attributes:name",
                 "eu_gdpr_subject"])
            file_out.close()

            # Query CX and start loop through records
            q_get_data = '''
            SELECT Distinct
            	TRIM(NVL(EML.line1,'')) AS email_address, 
            	TO_CHAR(PER.id) AS username, 
                TRIM(CV.ldap_name) AS auth_identifier, 
                '' AS card_id,  --Prox ID?  but not sure
                TRIM(IR.firstname) AS first_name, 
                TRIM(IR.lastname) AS last_name, 
                TRIM(IR.middlename) AS middle_name, 
                TRIM(ADM.pref_name) AS preferred_name,
                CASE 
                    WHEN CL.CL = 'FF' OR CL.CL = 'FR' THEN 'Freshman' 
                    WHEN (CL.CL = 'SO') THEN 'Sophomore' 
                    WHEN (CL.CL = 'JR') THEN 'Junior' 
                    WHEN (CL.CL = 'SR') THEN 'Senior' 
                    ELSE '' 
                    END AS school_year_name, 
                CASE 
                    WHEN DEG.deg in ('BS','BA') THEN 'Bachelors' 
                    WHEN (DEG.deg = 'CERT') THEN 'Certificate' 
                    WHEN DEG.deg in ('MBDI', 'MBA', 'MSW', 'MS', 'MM', 'MED') THEN 'Masters' 
                    WHEN (DEG.deg = 'NONE') THEN 'Non-Degree Seeking' 
                ELSE DEG.txt 
                    END AS education_level_name,
                SAR.cum_gpa AS cumulative_gpa,
                '' AS department_gpa,
                TRIM(MAJ1.txt) as primary_major_name,
                TRIM(MAJ1.txt) || CASE WHEN NVL(PER.major2,'') = '' THEN '' ELSE ';' 
                    || TRIM(MAJ2.txt) END || CASE WHEN NVL(PER.major3,'') = '' THEN '' ELSE ';' 
                    || TRIM(MAJ3.txt) 
                    END AS major_names,
                TRIM(NVL(MIN1.txt,'')) || CASE WHEN NVL(PER.minor2,'') = '' THEN '' ELSE ';' 
                    || TRIM(MIN2.txt) END || CASE WHEN NVL(PER.minor3,'') = '' THEN '' ELSE ';' 
                    || TRIM(MIN3.txt) 
                    END AS minor_names,
                'Carthage College' AS college_name, 
                PER.adm_date AS start_date, 
                PER.lv_date AS end_date,
                '' as currently_attending,
                '' AS campus_name,
                '' AS opt_cpt_eligible,  
                '' AS ethnicity,
                CASE TRIM(PRO.sex) WHEN 'M' THEN 'Male' WHEN 'F' THEN 'Female' ELSE PRO.sex 
                    END AS gender, 
                '' as disabled,  
                CASE WHEN AID.id IS NULL THEN 'FALSE' ELSE 'TRUE' 
                    END AS work_study_eligible, 
                '' as system_label_names,
                REPLACE(TRIM(NVL(CELL.line1,'')), '-', '') AS mobile_number,   
                TRIM(NVL(ADV.line1,'')) AS assigned_to_email_address,
                CASE WHEN ATH.id IS NULL THEN 'FALSE' ELSE 'TRUE' 
                    END AS athlete, 
                CASE TRIM(PRO.vet) WHEN 'N' THEN 'FALSE' WHEN 'Y' THEN 'TRUE' ELSE '' 
                    END AS veteran, 
                TRIM(IR.city) AS hometown_location_attributes,
                '' AS eu_gdpr_subject   
            FROM
                prog_enr_rec	PER	INNER JOIN	id_rec		IR	ON	PER.id			=	IR.id
					LEFT JOIN		aa_rec		EML	ON	PER.id			=	EML.id
							AND	EML.aa			=	'EML1'
							AND	TODAY		BETWEEN	EML.beg_date AND NVL(EML.end_date, TODAY)
					INNER JOIN	cvid_rec		CV	ON	PER.id			=	CV.cx_id
					INNER JOIN	cl_table		CL	ON	PER.cl			=	CL.cl
					LEFT JOIN		stu_acad_rec	SAR	ON	PER.id			=	SAR.id
							AND	TRIM(SAR.sess) || SAR.yr	IN	(SELECT TRIM(sess) || yr FROM cursessyr_vw)
					LEFT JOIN		major_table	MAJ1	ON	PER.major1		=	MAJ1.major
					LEFT JOIN		major_table	MAJ2	ON	PER.major2		=	MAJ2.major
					LEFT JOIN		major_table	MAJ3	ON	PER.major3		=	MAJ3.major
					LEFT JOIN		deg_table		DEG	ON	PER.deg			=	DEG.deg
					INNER JOIN	adm_rec		ADM	ON	PER.id			=	ADM.id
							AND	ADM.primary_app	=	'Y'
					INNER JOIN	profile_rec	PRO	ON	PER.id			=	PRO.id
					LEFT JOIN		minor_table	MIN1	ON	PER.minor1		=	MIN1.minor
					LEFT JOIN		minor_table	MIN2	ON	PER.minor2		=	MIN2.minor
					LEFT JOIN		minor_table	MIN3	ON	PER.minor3		=	MIN3.minor
					LEFT JOIN		aa_rec		ADV	ON	PER.adv_id		=	ADV.id
							AND	ADV.aa			=	'EML1'
							AND	TODAY		BETWEEN	ADV.beg_date AND NVL(ADV.end_date, TODAY)
					LEFT JOIN		aa_rec		CELL	ON	PER.id			=	CELL.id
							AND	CELL.aa			=	'CELL'
							AND	TODAY		BETWEEN	CELL.beg_date AND NVL(CELL.end_date, TODAY)
					LEFT JOIN		(SELECT id
									FROM aid_rec
									WHERE aid	=	'FWSY'
									AND stat	in	('A','I')
									AND TRIM(sess) || yr	IN	(SELECT TRIM(sess) || yr FROM cursessyr_vw)
									GROUP BY 										id
								)			AID	ON	PER.id			=	AID.id
					LEFT JOIN		(SELECT id
									FROM involve_rec
									WHERE invl		IN	
									  (SELECT invl FROM invl_table WHERE sanc_sport = 'Y')
									AND beg_date	>=	CASE WHEN TODAY < '06/01/'||to_char(YEAR(TODAY))	
														THEN '06/01/'||to_char(YEAR(TODAY)-1)
                                                        ELSE '06/01/'||to_char(YEAR(TODAY))
                                                        END
									GROUP BY id
								)			ATH	ON	PER.id			=	ATH.id

					LEFT JOIN       (
									SELECT id, gpa, mflag
    								FROM degaudgpa_rec
    								WHERE mflag = 'MAJOR1' AND gpa > 0
    								) DGR
								    ON 	DGR.id = PER.ID 
            WHERE
                PER.acst	IN	("GOOD","LOC","PROB","PROC","PROR","READ","RP","SAB","SHAC","SHOC")
                    AND PER.prog in ('UNDG')
                    AND PER.subprog in ('TRAD')
                    AND	NVL(PER.lv_date, TODAY)	>=	TODAY
                    AND EML.line1 is not null
                    LIMIT 15
                '''.format()

            # print(q_get_data)
            data_result = do_sql(q_get_data, key=DEBUG, earl=EARL)
            # scr.write(q_check_addr + '\n');
            ret = list(data_result.fetchall())
            if ret is None:
                print("Data missing")
            #     # fn_write_log("Data missing )
            else:
                print("Data found")
                # print(ret[0][0])
                # with open(handshakedata, 'ab') as file_out:
                with open("handshakedata.csv", 'ab') as file_out:
                    csvWriter = csv.writer(file_out)
                    for row in ret:
                         # print(row)
                         csvWriter.writerow(row)

                file_out.close()

    except Exception as e:
        # fn_write_error("Error in handshake buildcsv.py, Error = "  + e.message)
        print("Error in handshake buildcsv.py, Error = " + e.message)
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
