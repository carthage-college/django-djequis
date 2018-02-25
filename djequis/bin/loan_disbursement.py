# -*- coding: utf-8 -*-
import os, sys
# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djequis.settings')

# required if using django models
import django
django.setup()

from django.conf import settings

from djzbar.utils.informix import do_sql
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.utils.mail import send_mail

import argparse
import logging

logger = logging.getLogger('djequis')


SQL = '''
    SELECT
        DISTINCT aa_rec.line1 as email, id_rec.firstname
    FROM
       aid_rec , aa_rec , aid_table , id_rec
    WHERE
        aid_rec.id = aa_rec.id
    AND aid_rec.id = id_rec.id
    AND aa_rec.line1 is not null
    AND aa_rec.line1 <> '  '
    AND aa_rec.aa = 'EML1'
    AND (aa_rec.end_date is null or aa_rec.end_date > TODAY)
    AND aid_rec.stat = 'A'
    AND aid_rec.amt_stat = 'AD'
    AND aid_rec.amt > 0
    AND (aid_rec.amt_stat_date < TODAY AND aid_rec.amt_stat_date > TODAY - 2 )
    AND aid_rec.aid = aid_table.aid
    AND aid_table.loan_track = 'Y'
'''

# set up command-line options
desc = """
    Sends out loan disbursement emails.
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-d', '--database',
    required=True,
    help="Database name (cars or train).",
    dest='database'
)
parser.add_argument(
    '--test',
    action='store_true',
    help="Dry run?",
    dest='test'
)


def main():
    '''
    main function
    '''

    EARL = INFORMIX_EARL_PROD
    if database == 'train':
        EARL = INFORMIX_EARL_TEST

    # blind copy managers
    bcc = [settings.MANAGERS[0][1],settings.FINANCIAL_AID_EMAIL]

    # execute the SQL incantation
    sqlresult = do_sql(SQL, earl=EARL)
    if sqlresult:
        for s in sqlresult:
            if test:
                email = bcc[0]
                logger.debug("email = {}".format(s.email))
            else:
                email = s.email

            data = {
                'object': s, 'email': s.email, 'test': test
            }
            send_mail(
                None, [email,],
                "Loan Disbursement Notification",
                settings.DEFAULT_FROM_EMAIL,
                'core/financialaid/loan_disbursement/email.html',
                data, bcc
            )
    else:
        print "No loan disbursements today"


######################
# shell command line
######################

if __name__ == '__main__':
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

