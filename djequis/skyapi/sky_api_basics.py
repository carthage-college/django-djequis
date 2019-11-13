"""SKY API Authentication/Query Scripts
Modified from code by Mitch Hollberg
(mhollberg@gmail.com, mhollberg@cfgreateratlanta.org)
Python functions to
    a) Get an initial SKYApi token/refresh token and write them to a local file
    b) Make subsequent refreshes and updates to the SKYApi authentication based on tokens in the files.
"""

# from pathlib import Path
import requests
import sys
import os
import json
import time
import base64
import datetime
import django

# import cryptography
from datetime import datetime
# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()
# ________________
from django.conf import settings
from django.core.cache import cache
from sky_api_auth import get_local_token, get_refresh_token, token_refresh
from sky_api_calls import api_get, get_const_custom_fields, \
    get_constituent_id, set_const_custom_field, update_const_custom_fields, \
    delete_const_custom_fields, get_relationships, api_post, api_patch, \
    api_delete, get_custom_fields, get_custom_field_value


def main():
    try:
        # for now, possible actions include get_id = which will bypass
        # all the others, set_status, update_status, delete_field,
        # get_relationships
        action = 'get_id'

        """"--------GET THE TOKEN------------------"""
        # Token is stored in a text file
        current_token = get_local_token()
        # print("Current Token = ")
        # print(current_token)

        """ --------GET THE BLACKBAUD CONSTITUENT ID-----------------"""
        # # First, we have to get the internal ID from blackbaud for
        # the constituent
        const_id = get_constituent_id(current_token, 1534657)
        print("Constituent id = " + str(const_id))

        """------GET CUSTOM FIELDS FOR A CONSTITUENT----------"""
        # Also need to check to see if the custom field exists
        # Does not appear we can filter by category or type...WHY???
        # NEED TO GRAB THE ITEM ID FROM THE SPECIFIC CUSTOM FIELD
        # NOTE:  There seems to be a delay between successfully creating a
        # custom field value and being able to retrieve it for the student
        category = 'Student Status'
        ret = get_const_custom_fields(current_token, const_id, category)
        print(ret)
        item_id = ret
        print("Item ID = " + str(item_id))

        """
        --------------------------
        Here we will need some logic.   If the constituent exists and
        has the specific custom field Student Status, then we need to update
        the existing record, if not we need to add it
        ---------------------------
        """

        if action == 'set_status':
            """-----SET-------"""
            # Then we can deal with the custom fields...
            comment = 'Testing an add'
            val = 'Administrator'
            category = 'Student Status'
            ret = set_const_custom_field(current_token, const_id, val,
                                         category, comment)
            print(ret)

        if action == 'update_status':
            """-----PATCH-------"""
            # Required:  Token, Item ID
            # Need to test to see if all remaining params must be passed or if
            # we only pass the ones that change...We shouldn't need to change the
            # category or type...Would think date added should also
            # remain unchanged
            # category = 'Involvement'
            comment = 'Test 110319'
            valu = 'Not a Student'
            ret = update_const_custom_fields(current_token, item_id, comment, valu)
            print(ret)

            """-----DELETE-------"""
        if action == 'delete_field':
            ret = delete_const_custom_fields(current_token, item_id)
            print(ret)

        if action == 'get_relationships':
            """-----RELATIONSHIPS FOR A CONSTITUENT-------"""
            ret = get_relationships(current_token, const_id)
            print(ret)


        # """ --------These are generic and not specific to a constituent---"""
        # ret = get_custom_fields(current_token)
        # ret = get_custom_field_value(current_token, 'Involvment')


        """-----Once done, the token must be refreshed-------"""
        # Refreshthe API tokens
        r = token_refresh()
        print(r)

    except Exception as e:
        print("Error in main:  " + e.message)
        # fn_write_error("Error in misc_fees.py - Main: "
        #                + e.message)


if __name__ == "__main__":
    # args = parser.parse_args()
    # test = args.test
    # database = args.database

    # if not database:
    #     print "mandatory option missing: database name\n"
    #     parser.print_help()
    #     exit(-1)
    # else:
    #     database = database.lower()

    # if database != 'cars' and database != 'train' and database != 'sandbox':
    #     print "database must be: 'cars' or 'train' or 'sandbox'\n"
    #     parser.print_help()
    #     exit(-1)
    #
    # if not test:
    #     test = 'prod'
    # else:
    #     test = "test"

    sys.exit(main())
