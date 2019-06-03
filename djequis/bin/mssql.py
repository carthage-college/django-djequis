# -*- coding: utf-8 -*-

import pyodbc

from djzbar.settings import MSSQL_LENEL_EARL

connection = pyodbc.connect(MSSQL_LENEL_EARL)
result     = connection.execute("select uid, name from sysusers order by name")

for row in result:
     print row

result.close()
connection.close()
