# -*- coding: utf-8 -*-
import os
import sys
import argparse

# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

import django
# prime django
django.setup()

# django settings for script
from django.conf import settings
from django.db.models import Q

from djequis.rt.models import Users
from djtools.utils.mail import validateEmail

# set up command-line options

desc = """
    Update request tracker Users table data
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
    Update request tracker Users table data
    """

    # exclude admin users
    admins = settings.RT_ADMINS

    # obtain all users in the Users table
    users = Users.objects.using('rt4').exclude(id__in = admins).exclude(
        name__isnull=True
    )
    #users = Users.objects.using('rt4').exclude(id__in = admins).filter(
    #   Q(name__contains="carthage.edu") | Q(emailaddress__isnull=True)
    #)
    save = False
    for u in users:
        elist = u.name.split('@')
        if (len(elist) == 2 and elist[1] == 'carthage.edu'):
            # convert user name from email to username
            # see Users 1 incantation
            if test:
                print "Users.name {} will become {}".format(u.name,elist[0])
            else:
                # check if user name is already taken
                try:
                    user = Users.objects.using('rt4').get(name=elist[0])
                except:
                    u.name = elist[0]

            # set email to carthage address if no email present
            # see Users 2 incantation
            if not validateEmail(u.emailaddress) or not u.emailaddress:
                email = '{}@carthage.edu'.format(elist[0])
                if test:
                    print "Users.emailaddress {} will become {}".format(
                        u.emailaddress, email
                    )
                else:
                    u.emailaddress = email

            # set update flag to True
            save = True

        # save user object if we have updated it
        if save and not test:
            u.save()
            save = False

######################
# shell command line
######################

if __name__ == "__main__":

    args = parser.parse_args()
    test = args.test

    sys.exit(main())
