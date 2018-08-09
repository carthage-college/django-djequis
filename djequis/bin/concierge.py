import os
import sys
import pysftp
import csv
import time
import argparse
import shutil

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

from djequis.sql.concierge import STUDENTS
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

DEBUG = settings.INFORMIX_DEBUG

desc = """
    Package Concierge is an automated, self-service locker system that allow students 
    to retrieve their packages when it is convenient for them.
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
    # sFTP connection information for Package Concierge
    XTRNL_CONNECTION = {
        'host':settings.CONCIERGE_HOST,
        'username':settings.CONCIERGE_USER,
        'password':settings.CONCIERGE_PASS,
        'port':settings.CONCIERGE_PORT,
        'cnopts':cnopts
    }
    # set local path {/data2/www/data/concierge/}
    source_dir = ('{0}'.format(settings.CONCIERGE_CSV_OUTPUT))
    # get list of files and set local path and filenames
    # variable == /data2/www/data/concierge/{filename.csv}
    directory = os.listdir(source_dir)
    # sFTP PUT moves the STUDENTS.csv files to the Package Concierge server
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            # change directory
            #sftp.chdir("upload/")
            # loop through files in list
            for listfile in directory:
                pkgconciergefile = source_dir + listfile
                if pkgconciergefile.endswith(".csv"):
                    # sftp files if they end in .csv
                    sftp.put(pkgconciergefile, preserve_mtime=True)
                # delete original files from our server
                os.remove(pkgconciergefile)
            # close sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'CONCIERGE UPLOAD failed'
        BODY = 'Unable to PUT .csv files to Package Concierge server.\n\n{0}'.format(str(e))
        sendmail(
            settings.CONCIERGE_TO_EMAIL,settings.CONCIERGE_FROM_EMAIL,
            BODY, SUBJECT
        )

def main():
    ############################################################################
    # development server (bng), you would execute:
    # ==> python concierge.py --database=train --test
    # production server (psm), you would execute:
    # ==> python concierge.py --database=cars
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
    sql_dict = {
        'STUDENTS': STUDENTS
    }
    for key, value in sql_dict.items():
        ########################################################################
        # to print the dictionary key and rows of data, you would execute:
        ########################################################################
        if test:
            print(key)

        sql = do_sql(value, key=DEBUG, earl=EARL)

        rows = sql.fetchall()

        # set directory and filename to be stored
        # ex. /data2/www/data/concierge/STUDENTS.csv
        filename = ('{0}{1}.csv'.format(settings.CONCIERGE_CSV_OUTPUT, key))
        # set destination path and new filename that it will be renamed to when archived
        # ex. /data2/www/data/concierge/STUDENTS_BAK_20180123082403.csv
        archive_destination = ('{0}{1}_{2}_{3}.csv'.format(
            settings.CONCIERGE_CSV_ARCHIVED, key, 'BAK', datetimestr
        ))
        # create .csv file
        csvfile = open(filename, "w");
        output = csv.writer(csvfile)
        if rows is not None:
            if key == 'STUDENTS':  # write header row for STUDENTS
                output.writerow([
                    "Student ID", "First Name", "Last Name", "Email", "Cell Phone",
                    "Address", "City", "State", "Zip", "Year", "Session", "Housing",
                    "Building", "Room Number", "Opt Out", "Privacy"
                ])
            # creating the data rows for the .csv files
            for row in rows:
                if test:
                    print(row)
                if key == 'STUDENTS':  # write data row for STUDENTS
                    output.writerow([
                        row["student_id"], row["first_name"], row["last_name"],
                        row["email_address"], row["cell_phone"], row["address"],
                        row["city"], row["state"], row["zip"], row["year"],
                        row["session"], row["housing"], row["building"], row["room_number"],
                        row["opt_out"], row["privacy"]
                    ])
        else:
            SUBJECT = 'CONCIERGE UPLOAD failed'
            BODY = 'No values in list.'
            sendmail(
                settings.CONCIERGE_TO_EMAIL, settings.CONCIERGE_FROM_EMAIL,
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