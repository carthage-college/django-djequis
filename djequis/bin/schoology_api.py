import os
import sys
import argparse
import urllib2
import json

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

from schoolopy import Schoology, Auth

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

desc = """
    API Testing
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)


def main():
    sc = Schoology(
        Auth(settings.SCHOOLOGY_API_KEY, settings.SCHOOLOGY_API_SECRET)
    )
    sc.limit = 100  # Only retrieve 10 objects max

    print('Your name is {}'.format(sc.get_me().name_display))

    if test:
        print('feed {}'.format(sc.get_feed()))

    for update in sc.get_feed():

        if test:
            #print update
            print update.body
            print update.realm
            print update.uid
            print update.created
            print update.num_comments
            print update.likes
            print update.user_like_action
            print update.group_id
            print update.id

        user = sc.get_user(update.uid)
        if user:
            print('By: ' + user.name_display)
            print(update.body[:40].replace('\r\n', ' ').replace('\n', ' ') + '...')
            print('%d likes\n' % update.likes)


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
