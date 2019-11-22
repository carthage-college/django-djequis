import os
import sys
import csv
import argparse
import django
import mimetypes
import smtplib

""" Note to self, keep this here"""
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()

from django.conf import settings
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from email.mime.text import MIMEText
from djequis.core.utils import sendmail

from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from utilities import fn_get_bill_code, fn_translate_bldg_for_adirondack, \
    fn_write_error, fn_send_mail

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Collect adirondack data Room assignments for stu_serv_rec
"""
parser = argparse.ArgumentParser(description=desc)

def fn_get_name(id, EARL):
    fname = ""
    Q_GET_NAME = '''select fullname from id_rec 
       where id = {0}'''.format(id)
    ret = do_sql(Q_GET_NAME, key=DEBUG, earl=EARL)
    if ret is not None:
        row = ret.fetchone()
        if row is None:
            print("Name not found")
            fn_write_error(
                "Error in asign_notify.py - fn_get namen: No "
                "name found ")
            quit()
            fname = str(id)
        else:
            fname = row[0]

    return fname

def fn_notify(file, EARL):
    try:
        from operator import itemgetter
        # This needs to be pointed to the d2 data folder
        room_file = file
        # room_file = 'assignment.csv'
        # print(room_file)
        r = csv.reader(open(room_file))

        """
        Task
        Enable the send mail line in assign_notify.py line 169
        Remove commented test "MAIN" from assign_notify
        Remove testing call to fn_notify at end of room_assignments 
        Disable notification emails in Manual mode
        """

        '''
        I am creating a room assignment csv on each day of changes and
        sending the bill code to CX
        Can easily add bill code to the csv file and make comparisons based
        on that code, the csv file is only used for history and auditing...
        so after the assignment.csv is created, read the csv back into
        memory sorted by student ID and date
        Loop through that set and determine if a room has changed and the
        bill code has also changed.
        '''

        code_list = [""]
        xtra_list = [""]
        lastid = ""
        lastdate = ""
        lastroom = ""
        lastroomtype = ""
        lastbldg = ""
        lastcode = ""
        fullname = ""
        """Sorting by ID and by date 
        so if there are two records, the older will be a change, post code of 2
        The second record will have post code of 0
        If there is only 1 record, the post code will be 0
        
        So if record is a new ID and the post code = 2, we have a change
        The next record should be the same ID, with a code of 0
        At that point would take note of the change
        
        If the ID is new and the code is 0, we have a new assignment
        write the record
        
        if the id is not numeric skip
        """

        for line in sorted(r, key=itemgetter(0, 10)):
            # print("__________________________________")
            post = line[21]
            # print("last id = " + str(lastid))
            """Revision 11/21/19 - records can come as a change, which
              pulls two records from the API, or an add, which pulls
              only one.   An add needs to be accounted for as a code
              change, so I've reworked the logic"""

            # Skip the first line
            if not unicode(line[0]).isnumeric() and lastid == 0:
                print("Skip header")
                # if line[0] == "STUDENTNUMBER":
                pass
            # elif not unicode(line[0]).isnumeric() and lastid != 0:
            else:
                if post == "2":
                    # print("First record of change")
                    """Same student, different row, change
                        write the record to the notification
                        set the passcount to 2
                    """
                    # if line[23] != lastcode:

                elif post == "0":
                    if line[0] == lastid:
                        #this is the second record of a change
                        if lastcode == line[23]:
                            code_list.append("Student " + line[0]
                                    + ", " + fullname + " moved to "
                                    + line[2] + " " + line[4] + " " + line[23]
                                    + ", " + line[6] + " from " + lastbldg
                                    + " " + lastroom + " "
                                    + lastcode + ", " + lastroomtype
                                    + " on " + line[10])
                        else:
                            xtra_list.append("Student " + line[0]
                                    + ", " + fullname + " moved to " + line[2]
                                    + " " + line[4] + " " + line[23] + ", "
                                    + line[6] + " from " + lastbldg + " "
                                    + lastroom + " " + lastcode + ", "
                                    + lastroomtype + " on " + line[10])

                elif line[0] != lastid:
                    """The first assignment   """
                    fullname = fn_get_name(lastid, EARL)
                    code_list.append("Student " + lastid
                                     + ", " + fullname
                                     + " initially assigned to "
                                     + lastbldg + " " + lastroom + " "
                                     + lastcode + ", " + lastroomtype
                                     + " on " + lastdate)

                # store this row and go to the next record
                lastid = line[0]
                lastdate = line[10]
                lastroomtype = line[6]
                lastcode = line[23]
                lastbldg = line[2]
                lastroom = line[4]

        """PREPARE THE EMAIL"""
        body = "\n" + "Room changes requiring bill code change:"
        for i in code_list:
            body = body + i + "\n"
        body = body + "\n" + "Room changes not affecting bill code:"

        for i in xtra_list:
            body = body + i + "\n"

        frum = settings.ADIRONDACK_FROM_EMAIL
        # tu = settings.ADIRONDACK_TO_EMAIL
        tu = settings.ADIRONDACK_ASCII_EMAIL  #has Marietta and Carol
        subj = "Adirondack - Room Bill Code Change"
        # fn_send_mail(tu, frum, body, subj)
        print("Mail Sent " + subj + " TO: " + str(tu) + " FROM: " + str(frum)
              + " DETAILS: " + "\n" + body)

    except Exception as e:
        print(
                "Error in assign_notify.py:  " + e.message)
        # fn_write_error(
        #     "Error in assign_notify.py:" + e.message)


# def main():
#     EARL = INFORMIX_EARL_TEST
#     room_file = settings.ADIRONDACK_TXT_OUTPUT + \
#                 settings.ADIRONDACK_ROOM_ASSIGNMENTS + '.csv'
#     fn_notify(room_file, EARL)
#
#
# if __name__ == "__main__":
#
#     sys.exit(main())
#
