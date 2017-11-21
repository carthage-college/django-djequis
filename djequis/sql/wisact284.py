def getaid(dispersed):
    if dispersed:
        amt_stat_values = ("'AD'")
    else:
        amt_stat_values = ("'AA','AD','AP','EA'")
    # SQL for Wisconsin ACT 284
    WIS_ACT_284_SQL = '''
        SELECT
            '00383900' AS OPEID, '20' || LEFT(T1.fa_yr, 2) || '-20' || RIGHT(T1.fa_yr, 2) AS AcadYear,
            REPLACE(ID_Record.ss_no, '-', '') AS Social_Security_Number, TRIM(ID_Record.firstname) AS Student_First_Name,
            TRIM(ID_Record.lastname) AS Student_Last_Name, T1.id AS Student_ID_Number, TRIM(ID_Record.addr_line1) AS Student_Address_Line_1,
            TRIM(ID_Record.addr_line2) AS Student_Address_Line_2, TRIM(ID_Record.addr_line3) AS Student_Address_Line_3,
            TRIM(ID_Record.city) AS Student_City, TRIM(ID_Record.st) AS Student_State_Code, TRIM(ID_Record.zip) AS Student_Postal_Code,
            TRIM(ID_Record.ctry) AS Student_Country_Code, TRIM(NVL(Email.line1,'')) AS Student_email,
            --Aid Detail
            TRIM(T1.aid) AS Aid_Code, TRIM(Aid_Record_Aid_Table.txt) AS Loan_name, SUM(T1.amt) AS Aid_Amount,
            --Aid Other
            AidOther.c_InstGrants, AidOther.c_InstScholar, AidOther.c_FedGrants, AidOther.c_SteGrants, AidOther.c_OutsideAid,
            --Loan Date
            TO_CHAR(loan_rec.beg_date, '%Y%m%d') AS Loan_Date,
            --Budget Summary
            --NVL(Summary.No_TUFE, Summary.Trad_TUFE) AS c_TUFE, NVL(Summary.No_RMBD, Summary.Trad_RMBD) AS c_RMBD,
            --NVL(Summary.No_BOOK, Summary.Trad_BOOK) AS c_BOOK, NVL(Summary.No_TRAN, Summary.Trad_TRAN) AS c_TRAN,
            --NVL(Summary.No_MISC, Summary.Trad_MISC) AS c_MISC, NVL(Summary.No_LOAN, Summary.Trad_LOAN) AS c_LOAN
            CASE    WHEN    NVL(Summary.No_TUFE,0)  >   0   THEN    Summary.No_TUFE	ELSE    Summary.Trad_TUFE   END AS  c_TUFE,
            CASE    WHEN    NVL(Summary.No_RMBD,0)  >   0   THEN    Summary.No_RMBD	ELSE    Summary.Trad_RMBD   END	AS  c_RMBD,
            CASE    WHEN    NVL(Summary.No_BOOK,0)  >   0   THEN    Summary.No_BOOK	ELSE    Summary.Trad_BOOK   END	AS  c_BOOK,
            CASE    WHEN    NVL(Summary.No_TRAN,0)  >   0   THEN    Summary.No_TRAN	ELSE    Summary.Trad_TRAN   END	AS  c_TRAN,
            CASE    WHEN    NVL(Summary.No_MISC,0)  >   0   THEN    Summary.No_MISC	ELSE    Summary.Trad_MISC   END	AS  c_MISC,
            CASE    WHEN    NVL(Summary.No_LOAN,0)  >   0   THEN    Summary.No_LOAN	ELSE    Summary.Trad_LOAN   END	AS  c_LOAN
        FROM
            aid_rec T1  INNER JOIN  aid_table   Aid_Record_Aid_Table    ON  T1.aid  =   Aid_Record_Aid_Table.aid
                        INNER JOIN  (
                            SELECT
                                Aid_Record.id AS Student_ID_Number,
                                SUM(CASE WHEN Aid_Table.txt LIKE '%Grant%' AND Aid_Table.frm_code IN ('INSF','INSU','PCAR','PMRT','PCEI') THEN Aid_Record.amt ELSE 0 END) AS c_InstGrants,
                                SUM(CASE WHEN Aid_Table.txt NOT LIKE '%Grant%' AND Aid_Table.frm_code IN ('INSF','INSU','PCAR','PMRT','PCEI') THEN Aid_Record.amt ELSE 0 END) AS c_InstScholar,
                                SUM(CASE WHEN Aid_Table.frm_code = 'PFGR' THEN Aid_Record.amt ELSE 0 END) AS c_FedGrants,
                                SUM(CASE WHEN Aid_Table.frm_code = 'PSGR' THEN Aid_Record.amt ELSE 0 END) AS c_SteGrants,
                                SUM(CASE WHEN Aid_Table.frm_code = 'POUT' THEN Aid_Record.amt ELSE 0 END) AS c_OutsideAid
                            FROM
                                aid_rec Aid_Record  INNER JOIN  aid_table   Aid_Table   ON  Aid_Record.aid  =   Aid_Table.aid
                            WHERE
                                Aid_Record.id > 0
                            AND
                                Aid_Record.fa_yr =  CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')  THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                    END
                            AND
                                Aid_Record.stat IN ('A')
                            AND
                                Aid_Record.amt_stat IN ({0})
                            AND
                                Aid_Record.amt > 0
                            GROUP BY
                                Student_ID_Number
                        )                           AidOther            ON  T1.id       =   AidOther.Student_ID_Number
                        LEFT JOIN   loandisb_rec                        ON  T1.aid_no   =   loandisb_rec.aid_no
                        LEFT JOIN   loan_rec                            ON  loandisb_rec.loan_no    =   loan_rec.loan_no
                        LEFT JOIN   (
                            SELECT
                                IM.bgt_code AS Budget_Code, IM.id AS ID_Number,
                                --Trad IM Detail
                                SUM(CASE WHEN Detail.faitem = 'TUFE' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_TUFE,
                                SUM(CASE WHEN Detail.faitem = 'RMBD' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_RMBD,
                                SUM(CASE WHEN Detail.faitem = 'BOOK' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_BOOK,
                                SUM(CASE WHEN Detail.faitem = 'TRAN' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_TRAN,
                                SUM(CASE WHEN Detail.faitem = 'MISC' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_MISC,
                                SUM(CASE WHEN Detail.faitem = 'LOAN' AND IM.bgt_code = 'TRAD IM' THEN Detail.amt ELSE 0 END) AS Trad_LOAN,
                                --No IM Detail
                                SUM(CASE WHEN Detail.faitem = 'TUFE' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_TUFE,
                                SUM(CASE WHEN Detail.faitem = 'RMBD' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_RMBD,
                                SUM(CASE WHEN Detail.faitem = 'BOOK' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_BOOK,
                                SUM(CASE WHEN Detail.faitem = 'TRAN' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_TRAN,
                                SUM(CASE WHEN Detail.faitem = 'MISC' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_MISC,
                                SUM(CASE WHEN Detail.faitem = 'LOAN' AND IM.bgt_code <> 'TRAD IM' THEN Detail.amt ELSE 0 END) AS No_LOAN
                            FROM
                                fabgt_rec   IM  INNER JOIN  fabgtdtl_rec    Detail  ON  IM.fabgt_no =   Detail.fabgt_no
                                                                                    AND	IM.fa_yr    =   CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')  THEN    MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                                                                        ELSE    MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                                                                        END
                            GROUP BY
                                Budget_Code, ID_Number
                        )                   Summary         ON  T1.id       =   Summary.ID_number
                        LEFT JOIN   aa_rec  Email           ON  T1.id       =   Email.id
                                                            AND Email.aa    =   'EML1'
                                                            AND	TODAY   BETWEEN Email.beg_date AND NVL(Email.end_date, TODAY)
                        INNER JOIN  id_rec  ID_Record       ON  T1.id       =   ID_Record.id
        WHERE
            T1.fa_yr =  CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')  THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                        ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                        END
        AND
            T1.stat IN ('A')
        AND
            T1.amt_stat IN ({0})
        AND
            T1.amt > 0
        AND
            Aid_Record_Aid_Table.dsl_loan_type = 'AL'
        GROUP BY 
            T1.id, T1.aid, Aid_Record_Aid_Table.txt, Loan_Date, c_TUFE, c_RMBD, c_BOOK, c_TRAN, c_MISC, c_LOAN, Student_email,
            Social_Security_Number, Student_First_Name, Student_Last_Name, Student_Address_Line_1, Student_Address_Line_2, Student_Address_Line_3, Student_City, Student_State_Code, Student_Postal_Code, Student_Country_Code,
            AidOther.c_InstGrants, AidOther.c_InstScholar, AidOther.c_FedGrants, AidOther.c_SteGrants, AidOther.c_OutsideAid, AcadYear
        ORDER BY
            T1.id
    '''.format(amt_stat_values)
    return WIS_ACT_284_SQL