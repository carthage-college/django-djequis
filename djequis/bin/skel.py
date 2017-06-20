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

import argparse

'''
Shell script...
'''

# set up command-line options
desc = """
Accepts as input...
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-x', '--equis',
    required=True,
    help="Lorem ipsum dolor sit amet.",
    dest='equis'
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

######################
# shell command line
######################

if __name__ == '__main__':
    args = parser.parse_args()
    equis = args.equis
    test = args.test

    print args

    sys.exit(main())

