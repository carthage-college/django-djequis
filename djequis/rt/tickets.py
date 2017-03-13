# -*- coding: utf-8 -*-
import os, sys
import django
import argparse

# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections

from djequis.rt.models import Tickets
from djequis.sql.rt import *

# set up command-line options

desc = """
    Update request tracker tickets
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    """
    Update request tracker tickets
    """

    # we need this for our SQL incantations
    globs = globals()

    status_include = settings.RT_TICKET_STATUS_INCLUDE

    # obtain all tickets in the Tickets table that have a certain status,
    # while excluding some
    tickets = Tickets.objects.using('rt4').filter(
        status__in=status_include
    ).exclude(type = "reminder")

    for idx, t in enumerate(tickets):

        # Tickets 1 incantation
        if t.timeestimated==0 or t.timeestimated < (t.timeworked + t.timeleft):
            t.timeestimated = t.timeworked + t.timeleft + 1

        # Tickets 2 incantation
        t.timeleft = t.timeestimated - t.timeworked

        if test:
            print "{} Ticket: {}".format(idx, t.creator)
        else:
            t.save()

    # new need to execute raw SQL
    cursor = connections['rt4'].cursor()
    for idx in [3,4,5]:
        if test:
            sql = globs['TICKETS_{}_{}'.format('SELECT',idx)]
            print sql
        else:
            sql = globs['TICKETS_{}_{}'.format('UPDATE',idx)]

        cursor.execute(sql)
        if test:
            results = cursor.fetchall()
            print results


######################
# shell command line
######################

if __name__ == "__main__":

    args = parser.parse_args()
    test = args.test

    sys.exit(main())