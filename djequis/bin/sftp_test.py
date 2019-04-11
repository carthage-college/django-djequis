from django.conf import settings

import pysftp


if True:
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # External connection information for Common Application server
    #XTRNL_CONNECTION = {
       #'host':settings.COMMONAPP_HOST,
       #'username':settings.COMMONAPP_USER,
       #'password':settings.COMMONAPP_PASS,
       #'cnopts':cnopts
    #}

    XTRNL_CONNECTION = {
       'host':'dione.carthage.edu',
       'username':'',
       'password':'',
       'cnopts':cnopts
    }

    print(XTRNL_CONNECTION)

    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        # Remote Path is the Common App server and once logged in we fetch
        # directory listing
        remotepath = sftp.listdir()
        # Loop through remote path directory list
        for filename in remotepath:
            print(filename)
            '''
            remotefile = filename
            # set local directory for which the common app file will be
            # downloaded to
            local_dir = ('{0}'.format(
                settings.COMMONAPP_CSV_OUTPUT
            ))
            localpath = local_dir + remotefile
            # GET file from sFTP server and download it to localpath
            sftp.get(remotefile, localpath)
            #############################################################
            # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
            # from sFTP (Common App) server
            #############################################################
            sftp.remove(filename)
            '''
    sftp.close()
