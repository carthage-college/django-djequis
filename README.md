# django-djequis

An all purpose Django project for lightweight applications that interact
with the Jenzabar databases, and over time will replace maquettes in /jics.

## Cron Jobs

    # google api groups caching
    20 04 * * * python /d2/django_projects/djusagi/bin/dir_groups_list.py > /d2/django_projects/djusagi/groups.csv
    # google api user reports caching
    00 01 * * * (/d2/django_projects/djusagi/bin/two_factor_auth.sh 2>&1 | mail -s "[djusagi] 2 factor auth caching" webtech@carthage.edu) >> /dev/null 2>&1
    #00 01 * * * /d2/django_projects/djusagi/bin/two_factor_auth.sh >> /dev/null 2>&1
    # scrip safe
    #20 * * * * (python /d2/django_projects/djzbar/bin/scrip_safe.py 2>&1 | mail -s "[scrip safe] SFTP process" webtech@carthage.edu) >> /dev/null 2>&1
    # Terra Dotta: daily before 2h CDT, push out a copy of the Terra Dotta export
    30 01 * * * (python /d2/django_projects/djequis/bin/terradotta.py 2>&1 | mail -s "[TerraDotta] SFTP carthage user data" webtech@carthage.edu) >> /dev/null 2>&1
    #30 01 * * * python /d2/django_projects/djequis/bin/terradotta.py >> /dev/null 2>&1
    # Everbridge: weekly, monday morning at midnight
    00 00 * * 1 (python /d2/django_projects/djequis/bin/everbridge.py 2>&1 | mail -s "[Everbridge] SFTP carthage user data" webtech@carthage.edu) >> /dev/null 2>&1
    # OCLC: weekly, monday morning at 2h, push out a fresh copy of the OCLC xml
    00 02 * * 1 (python /d2/django_projects/djequis/bin/oclc.py 2>&1 | mail -s "[OCLC] FTP carthage user data" webtech@carthage.edu) >> /dev/null 2>&1
    # maxient
    00 03 * * * (python /d2/django_projects/djequis/bin/maxient.py 2>&1 | mail -s "[Maxient] SFTP carthage user data" webtech@carthage.edu) >> /dev/null 2>&1
    # Request Tracker
    */10 * * * * python /d2/django_projects/djequis/rt/users.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/users.py 2>&1 | mail -s "[RT] Users" webtech@carthage.edu) >> /dev/null 2>&1
    */10 * * * * python /d2/django_projects/djequis/rt/tickets.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/tickets.py 2>&1 | mail -s "[RT] Tickets" webtech@carthage.edu) >> /dev/null 2>&1
    # JX scripts
    11 11 * * * (python /d2/django_projects/djequis/bin/class_year.py --action=update --database=jxlive >> /dev/null 2>&1
    # common app
    #00 03 * * 0-5 (python /d2/django_projects/djequis/bin/commonapp.py --database=cars 2>&1 | mail -s "[CommonApp] Fetching data via SFTP" webtech@carthage.edu) >> /dev/null 2>&1
    # barnes and noble
    17 08-17 * * 1-5 (python /d2/django_projects/djequis/bin/barnesandnoble.py 2>&1 | mail -s "[Barnes & Noble] data upload" webtech@carthage.edu) >> /dev/null 2>&1

## Database import

    mysql -u username -p rt4 < rt4.sql
    mysql -u username -p rt4 < rt/views.sql
