import os
import sys
import pysftp
import csv
import time
import argparse
import shutil
import datetime

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

from djequis.sql.schoology import COURSES
from djequis.sql.schoology import USERS
from djequis.sql.schoology import ENROLLMENT
from djequis.sql.schoology import CROSSLIST
from djequis.sql.schoology import CANCELLED_COURSES
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

DEBUG = settings.INFORMIX_DEBUG

desc = """
    Schoology Upload
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
'''
    Creates a sFTP client connected to the supplied host on the supplied port
    authenticating as the user with supplied username and supplied password
'''
def file_download():
    # by adding cnopts, I'm authorizing the program to ignore the host key and just continue
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None # ignore known host key checking
    # sFTP connection information for Schoology
    XTRNL_CONNECTION = {
        'host':settings.SCHOOLOGY_HOST,
        'username':settings.SCHOOLOGY_USER,
        'password':settings.SCHOOLOGY_PASS,
        'port':settings.SCHOOLOGY_PORT,
        'cnopts':cnopts
    }
    # set local path {/data2/www/data/schoology/}
    source_dir = ('{0}'.format(settings.SCHOOLOGY_CSV_OUTPUT))
    # get list of files and set local path and filenames
    # variable == /data2/www/data/schoology/{filename.csv}
    directory = os.listdir(source_dir)
    # sFTP PUT moves the COURSES.csv, USERS.csv, ENROLLMENT.csv files to the Schoology server
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            # change directory
            sftp.chdir("upload/")
            # loop through files in list
            for listfile in directory:
                schoologyfiles = source_dir + listfile
                if schoologyfiles.endswith(".csv"):
                    # sftp files if they end in .csv
                    sftp.put(schoologyfiles, preserve_mtime=True)
                # delete original files from our server
                os.remove(schoologyfiles)
            # close sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'SCHOOLOGY UPLOAD failed'
        BODY = 'Unable to PUT .csv files to Schoology server.\n\n{0}'.format(str(e))
        sendmail(
            settings.SCHOOLOGY_TO_EMAIL,settings.SCHOOLOGY_FROM_EMAIL,
            BODY, SUBJECT
        )

def main():
    ############################################################################
    # development server (bng), you would execute:
    # ==> python schoology.py --database=train --test
    # production server (psm), you would execute:
    # ==> python schoology.py --database=cars
    # without the --test argument
    ############################################################################
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
    # formatting date and time string 
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # getting date and time string
    dt = datetime.datetime.now()
    # if it's after 12 PM then we will email if there any cancelled courses
    if dt.hour > 12:
        # check to see if there are any cancelled courses 
        sqlresult = do_sql(CANCELLED_COURSES, key=DEBUG, earl=EARL)
        resultrow = sqlresult.fetchone()
    
        # if the resultrow qry returns a row then we will create the courses cancelled list
        if resultrow is not None:
            allsqlresult = do_sql(CANCELLED_COURSES, key=DEBUG, earl=EARL)
            # now get all rows for the cancelled courses
            resulalltrows = allsqlresult.fetchall()
            items = []
            for row in resulalltrows:
                items.append('COURSE: {0} - {1} {2} {3} {4}\n'
                             .format(row[0], row[1], row[2], row[3], row[4]))
            courses_table = ''.join(items)
            # send email
            SUBJECT = 'SCHOOLOGY - Cancelled Courses'
            BODY = 'The following courses have been cancelled.\n\n{0}'.format(courses_table)
            sendmail(
                settings.SCHOOLOGY_MSG_EMAIL,settings.SCHOOLOGY_FROM_EMAIL,
                BODY, SUBJECT
            )
        else:
            print('Do nothing!')
    else:
        print('Do nothing!')

    # set dictionary
    sql_dict = {
        'COURSES': COURSES,
        'USERS': USERS,
        'ENROLLMENT': ENROLLMENT,
        'CROSSLIST': CROSSLIST
        }
    for key, value in sql_dict.items():
        ########################################################################
        # to print the dictionary key and rows of data, you would execute:
        ########################################################################
        if test:
            print(key)
        ########################################################################
        # Dict Value 'COURSES and SECTIONS' return all courses and sections with
        # a start date less than six months from the current date.
        # Based on the dates for the terms courses and sections are made active
        # or inactive automatically

        # Dict Value 'USERS' returns both Students and Faculty/Staff
        # The student query portion pulls all students with an academic record
        # between the start of the current fiscal year (July 1) and the end of
        # the current fiscal year.
        # The Faculty/Staff portion gets all employees with active job records
        # within the last year.

        # Dict Value 'ENROLLMENT' returns all students and instructors enrolled
        # in a course/section with a start date less than six months from the
        # current date.

        # Dict Value 'CROSSLIST' returns two different sections that have the
        # same meeting time and place but may have a different course number
        # for a program it looks six months ahead
        ########################################################################
        sql = do_sql(value, key=DEBUG, earl=EARL)

        rows = sql.fetchall()

        # set directory and filename to be stored
        # ex. /data2/www/data/schoology/COURSES.csv
        filename = ('{0}{1}.csv'.format(settings.SCHOOLOGY_CSV_OUTPUT,key))
        # set destination path and new filename that it will be renamed to when archived
        # ex. /data2/www/data/schoology_archives/COURSES_BAK_20180123082403.csv
        archive_destination = ('{0}{1}_{2}_{3}.csv'.format(
            settings.SCHOOLOGY_CSV_ARCHIVED,key,'BAK',datetimestr
        ))
        # create .csv file
        csvfile = open(filename,"w");
        output = csv.writer(csvfile)
        if rows is not None:
            if key == 'COURSES': # write header row for COURSES and SECTIONS
                output.writerow([
                    "Course Name", "Department", "Course Code", "Credits",
                    "Description", "Section Name", "Section School Code",
                    "Section Code", "Section Description", "Location", "School",
                    "Grading Period"
                    ])
            if key == 'USERS': # write header row for USERS
                output.writerow([
                    "First Name", "Preferred First Name", "Middle Name",
                    "Last Name", "Name Prefix", "User Name", "Email",
                    "Unique ID", "Role", "School", "Schoology ID", "Position",
                    "Pwd", "Gender", "Graduation Year", "Additional Schools"
                    ])
            if key == 'ENROLLMENT': # write header row for ENROLLMENT
                output.writerow([
                    "Course Code", "Section Code", "Section School Code",
                    "Unique ID", "Enrollment Type", "Grade Period"
                    ])
            if key == 'CROSSLIST': # write header row for CROSSLIST
                output.writerow([
                    "Meeting Number", "Cross-listed Section Code", "Target Code" 
                    ])
            # creating the data rows for the .csv files
            for row in rows:
                if test:
                    print(row)
                if key == 'COURSES': # write data row for COURSES
                    output.writerow([
                        row["coursename"], row["department"],
                        row["coursecode"], row["credits"], row["descr"],
                        row["sectionname"], row["secschoolcode"],
                        row["sectioncode"], row["secdescr"], row["location"],
                        row["school"], row["gradingperiod"]
                        ])
                if key == 'USERS': # write data row for USERS
                    output.writerow([
                        row["firstname"], row["preferred_first_name"],
                        row["middlename"], row["lastname"], row["name_prefix"],
                        row["username"], row["email"],
                        ("{0:.0f}".format(0 if row['uniqueid'] is None else row['uniqueid'])),
                        row["role"], row["school"], row["schoology_id"],
                        row["position"], row["pwd"], row["gender"],
                        row["gradyr"], row["additional_schools"]
                        ])
                if key == 'ENROLLMENT': # write data row for ENROLLMENT
                    output.writerow([
                        row["coursecode"], row["sectioncode"],
                        row["secschoolcode"],
                        ("{0:.0f}".format(0 if row['uniqueuserid'] is None else row['uniqueuserid'])),
                        row["enrollmenttype"], row["gradeperiod"]
                        ])
                if key == 'CROSSLIST': # write data row for CROSSLIST
                    output.writerow([
                        row["mtg_no"], row["crls_code"], row["targ_code"]
                        ])
        else:
           SUBJECT = 'SCHOOLOGY UPLOAD failed'
           BODY = 'No values in list.'
           sendmail(
               settings.SCHOOLOGY_TO_EMAIL,settings.SCHOOLOGY_FROM_EMAIL,
               BODY, SUBJECT
           )
        csvfile.close()
        # renaming old filename to newfilename and move to archive location
        shutil.copy(filename, archive_destination)
    if not test:
        file_download()


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test
    database = args.database
    
    if not database:
        print("mandatory option missing: database name\n")
        parser.print_help()
        exit(-1)
    else:
        database = database.lower()

    if database != 'cars' and database != 'train':
        print("database must be: 'cars' or 'train'\n")
        parser.print_help()
        exit(-1)

    sys.exit(main())