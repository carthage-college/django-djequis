# django-djequis

An all purpose Django project for lightweight applications that interact
with the Jenzabar databases, and over time will replace maquettes in /jics.

## Cron Jobs

    # google api groups caching
    20 04 * * * python /d2/django_projects/djusagi/bin/dir_groups_list.py > /d2/django_projects/djusagi/groups.csv
    # google api user reports caching
    00 01 * * * (/d2/django_projects/djusagi/bin/two_factor_auth.sh 2>&1 | mail -s "[djusagi] 2 factor auth caching" larry@carthage.edu) >> /dev/null 2>&1
    #00 01 * * * /d2/django_projects/djusagi/bin/two_factor_auth.sh >> /dev/null 2>&1
    # scrip safe
    #20 * * * * (python /d2/django_projects/djzbar/bin/scrip_safe.py 2>&1 | mail -s "[scrip safe] SFTP process" larry@carthage.edu) >> /dev/null 2>&1
    # Terra Dotta: daily before 2h CDT, push out a copy of the Terra Dotta export
    30 01 * * * (python /d2/django_projects/djequis/bin/terradotta.py 2>&1 | mail -s "[TerraDotta] SFTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    #30 01 * * * python /d2/django_projects/djequis/bin/terradotta.py >> /dev/null 2>&1
    # Everbridge: weekly, monday morning at midnight
    00 00 * * 1 (python /d2/django_projects/djequis/bin/everbridge.py 2>&1 | mail -s "[Everbridge] SFTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    # OCLC: weekly, monday morning at 2h, push out a fresh copy of the OCLC xml
    00 02 * * 1 (python /d2/django_projects/djequis/bin/oclc.py 2>&1 | mail -s "[OCLC] FTP carthage user data" ssmolik@carthage.edu) >> /dev/null 2>&1
    # maxient
    00 03 * * * (python /d2/django_projects/djequis/bin/maxient.py 2>&1 | mail -s "[Maxient] SFTP carthage user data" ssmolik@carthage.edu) >> /dev/null 2>&1
    # Request Tracker
    */10 * * * * python /d2/django_projects/djequis/rt/users.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/users.py 2>&1 | mail -s "[RT] Users" larry@carthage.edu) >> /dev/null 2>&1
    */10 * * * * python /d2/django_projects/djequis/rt/tickets.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/tickets.py 2>&1 | mail -s "[RT] Tickets" larry@carthage.edu) >> /dev/null 2>&1
    # JX scripts
    11 11 * * * (python /d2/django_projects/djequis/bin/class_year.py --action=update --database=jxlive >> /dev/null 2>&1
    # common app
    00 04 * * 0-5 (python /d2/django_projects/djequis/bin/commonapp.py --database=cars 2>&1 | mail -s "[CommonApp] Fetching data via SFTP" rob@carthage.edu,nick@carthage.edu,ssmolik@carthage.edu) >> /dev/null 2>&1
    # barnes and noble
    17 08-17 * * 1-5 (python /d2/django_projects/djequis/bin/barnesandnoble.py) >> /dev/null 2>&1
    # Papercut: monthly, 2nd day of every month at 23:55h, create .csv file for Papercut charge backs
    55 23 2 * * (python /d2/django_projects/djequis/bin/papercut.py 2>&1 | mail -s "[PaperCut] Papercut charge backs data" ssmolik@carthage.edu) >> /dev/null 2>&1
    # Papercut GL: monthly, 3rd day of every month at 2:45h, create .csv file of Papercut GL accounts
    #45 02 3 * * (python /d2/django_projects/djequis/bin/papercut_glrec.py 2>&1 | mail -s "[PaperCut] Papercut GL accounts data" ssmolik@carthage.edu) >> /dev/null 2>&1
    # Loan Dispursements (every four hours)
    20 04 * * * (python /d2/django_projects/djequis/bin/loan_disbursement.py --database=cars 2>&1 | mail -s "[Financial Aid] Load Dispursements" larry@carthage.edu) >> /dev/null 2>&1

## Database import

    mysql -u username -p rt4 < rt4.sql
    mysql -u username -p rt4 < rt/views.sql
