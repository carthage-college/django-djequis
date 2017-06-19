# -*- coding: utf-8 -*-
import os, sys

# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

from django.conf import settings

from djzbar.utils.informix import get_session

from datetime import datetime

import argparse

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
Optional --test argument
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)


def main():
    '''
    First generation align. Aligns adm_rec with FAFSA information.
    '''

    # create database connection
    session = get_session(EARL)
    if test:
        print "database connection URL = {}".format(EARL)

    #...........................................
    if test:
        print "drop temp tables, just in case"

    drop1 = "DROP TABLE adm_records"
    if not test:
        try:
            session.execute(drop1(
            print "adm_records dropped"
        except:
            print "no temp table: adm_records"
    else:
        print drop1

    Sel1SQL = '''
        SELECT
            app_no, id from adm_rec
        WHERE
            primary_app = 'Y'
        AND
            plan_enr_sess = 'RA'
        AND
            plan_enr_yr = 2017
        AND
            prog = 'UNDG'
        AND
            subprog = 'TRAD'
        INTO
            adm_records
    '''

    if not test:
        session.execute(Sel1SQL)
    else:
        print Sel1SQL

    Sel2SQL = '''
        Select
            id,
            CASE
                WHEN
                    naf1718_rec.dad_educ = '3' THEN 'N'
                WHEN
                    naf1718_rec.mom_educ = '3' THEN 'N'
                ELSE
                    'Y'
            END AS
                first_generation
        FROM
            naf1718_rec
        WHERE
            method = 'FM'
        INTO
            naf_records
    '''

    if not test:
        session.execute(Sel2SQL)
    else:
        print Sel2SQL

    Sel3SQL = '''
        SELECT
            app_no, first_generation
        FROM
            adm_records, naf_records
        WHERE
            adm_records.id = naf_records.id
    '''

    if not test:
        results = session.execute(Sel3SQL)
    else:
        print Sel3SQL


    for row in results:

        updSQL = '''
            UPDATE
                adm_rec
            SET
                first_gen == {}
            WHERE
                app_no == {}
            AND
                first_gen <> {}
        '''.format(row[1], row[0], row[1])

        if not test:
            session.execute(updSQL)
        else:
            print updSQL

    Sel7SQL = '''
        SELECT
            id,
            CASE
                WHEN
                    naf1718_rec.dad_educ = '3' THEN 'N'
                WHEN
                    naf1718_rec.mom_educ = '3' THEN 'N'
                ELSE
                    'Y'
            END AS first_generation
        FROM
             naf1718_rec
        WHERE
            method = 'FMS'
        INTO
            naf_recordsfms
    '''

    if not test:
        session.execute(Sel7SQL)
    else:
        print Sel7SQL

    if not test:
        try:
            session.commit()
        except Exception, e:
            print >> sys.stderr, "Commit failed"
            print >> sys.stderr, "Exception: %s" % str(e)
            sys.exit(1)
    else:
        # end time
        print datetime.now()

    # Temporary tables are automatically dropped when the SQL session ends
    session.close()


######################
# shell command line
######################

if __name__ == "__main__":

    sys.exit(main())
