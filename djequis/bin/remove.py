import os
import sys
import argparse
import time

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

# set up command-line options
desc = """
    Remove old files
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    # go to our storage directory on the server
    os.chdir(settings.TEST_OUTPUT)

    # Define variables
    xdays = 5
    now   = time.time()

    # set directory and filename
    dirpath = ('{}'.format(
        settings.TEST_OUTPUT
    ))

    # List all files older than xdays
    print "\nList all files older than " + str(xdays) + " days"
    print "==========================" + "=" * len(str(xdays)) + "====="
    for root, dirs, files in os.walk(dirpath):
      for name in files:
        filename = os.path.join(root, name)
        if os.stat(filename).st_mtime < now - (xdays * 86400):
          if test:
            print(filename)
        #os.remove(filename)

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
