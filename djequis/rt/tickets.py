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
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djpsilobus.settings")
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
django.setup()

# django settings for script
from django.conf import settings
from django.db.models import Q

from djequis.rt.models import Tickets

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

    status_include = settings.RT_TICKET_STATUS_INCLUDE

    # obtain all tickets in the Tsers table
    tickets = Tickets.objects.using('rt4').filter(
        status__in=status_include
    ).exclude(type = "reminder")

    for t in tickets:
        # see Tickets 1 incantation
        if t.timeestimated==0 or \
          (t.timeestimated < (t.timeworked + t.timeleft)):
            if test:
                print t
            else:
                t.timeestimated = t.timeworked + t.timeleft + 1
        # see Tickets 2 incantation
        if not test:
            t.timeleft = t.timeestimated - t.timeworked


######################
# shell command line
######################

if __name__ == "__main__":

    args = parser.parse_args()
    test = args.test

    sys.exit(main())
