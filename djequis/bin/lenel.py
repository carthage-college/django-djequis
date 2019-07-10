# -*- coding: utf-8 -*-

import pyodbc

from djzbar.settings import MSSQL_LENEL_EARL

connection = pyodbc.connect(MSSQL_LENEL_EARL)
sql = """
    SELECT
        EMP.SSNO as carthageID, EMP.FIRSTNAME, EMP.LASTNAME,
        MMOBJS.LNL_BLOB as photo
    FROM
        EMP left join MMOBJS on MMOBJS.EMPID = EMP.ID
    WHERE
        mmobjs.object = 1
    AND
        mmobjs.type = 0
    AND
        emp.ssno = '#LMS_students.host_id#'
"""
# sql = "SELECT uid, name FROM sysusers ORDER BY name"

result = connection.execute(sql)

for row in result:
     print(row)

result.close()
connection.close()
