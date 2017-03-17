#!/bin/bash
MUSER="$1"
MDB="$2"
MDBS="$3"

# Detect paths
MYSQL=$(which mysql)
AWK=$(which awk)
GREP=$(which grep)

if [ $# -ne 3 ]
then
        echo "Usage: $0 {MySQL-User-Name} {MySQL-Database-Name} {MySQL-Database-Server}"
        echo "Drops all tables from a MySQL"
        exit 1
fi

echo -e "Please enter MySQL password for $MUSER"
read -s MPASS

TABLES=$($MYSQL -u $MUSER -p$MPASS -D $MDB -h $MDBS -e 'show tables' | $AWK '{ print $1}' | $GREP -v '^Tables' )

for t in $TABLES
do
        echo "Deleting $t table from $MDB database..."
        $MYSQL -u $MUSER -p$MPASS $MDB -e "SET FOREIGN_KEY_CHECKS = 0;drop table $t"
        #$MYSQL -u $MUSER -p$MPASS $MDB -e "drop view $t"
done
