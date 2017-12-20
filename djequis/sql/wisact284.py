def getaid(dispersed):
    if dispersed:
        amt_stat_values = ("'AD'")
    else:
        amt_stat_values = ("'AA','AD','AP','EA'")
    # SQL for Wisconsin ACT 284
    WIS_ACT_284_SQL = '''
        select distinct
            '00383900' AS OPEID, 
            '20' || LEFT(CALREC.acyr, 2) || '-20' || RIGHT(CALREC.acyr, 2) AS AcadYear,
            REPLACE(StuID.ss_no, '-', '') AS Social_Security_Number, 
            TRIM(StuID.firstname) AS Student_First_Name,
            TRIM(StuID.lastname) AS Student_Last_Name, 
            StuID.id AS Student_ID_Number, 
            TRIM(StuID.addr_line1) AS Student_Address_Line_1,
            TRIM(StuID.addr_line2) AS Student_Address_Line_2, 
            TRIM(StuID.addr_line3) AS Student_Address_Line_3,
            TRIM(StuID.city) AS Student_City, 
            TRIM(StuID.st) AS Student_State_Code, 
            TRIM(StuID.zip) AS Student_Postal_Code,
            TRIM(StuID.ctry) AS Student_Country_Code, 
            TRIM(NVL(Email.line1,'')) AS Student_email,
            --Aid Detail
            --TRIM(CUM_AID.aid) AS Aid_Code,
            TRIM(CUM_AID.txt) AS Loan_name, CUM_AID.Aid_Amount AS Aid_Amount,
            --Aid Other
            AidOther.c_InstGrants, AidOther.c_InstScholar, AidOther.c_FedGrants, AidOther.c_SteGrants, AidOther.c_OutsideAid,
            --Loan Date
            TO_CHAR(CUM_AID.beg_date, '%Y%m%d') AS Loan_Date, --CUM_AID.FA_YR,
            --Budget Summary
        CASE    WHEN    NVL(BGT_COSTS.No_TUFE,0)    >   0   THEN    BGT_COSTS.No_TUFE   ELSE    BGT_COSTS.Trad_TUFE END AS  c_TUFE,
        CASE    WHEN    NVL(BGT_COSTS.No_RMBD,0)    >   0   THEN    BGT_COSTS.No_RMBD   ELSE    BGT_COSTS.Trad_RMBD END AS  c_RMBD,
        CASE    WHEN    NVL(BGT_COSTS.No_BOOK,0)    >   0   THEN    BGT_COSTS.No_BOOK   ELSE    BGT_COSTS.Trad_BOOK END AS  c_BOOK,
        CASE    WHEN    NVL(BGT_COSTS.No_TRAN,0)    >   0   THEN    BGT_COSTS.No_TRAN   ELSE    BGT_COSTS.Trad_TRAN END AS  c_TRAN,
        CASE    WHEN    NVL(BGT_COSTS.No_MISC,0)    >   0   THEN    BGT_COSTS.No_MISC   ELSE    BGT_COSTS.Trad_MISC END AS  c_MISC,
        CASE    WHEN    NVL(BGT_COSTS.No_LOAN,0)    >   0   THEN    BGT_COSTS.No_LOAN   ELSE    BGT_COSTS.Trad_LOAN END AS  c_LOAN
        from 
         -----------------------------------------------
         --ACTIVE STUDENT LIST
         -----------------------------------------------
        stu_acad_rec ACADREC 
        inner join acad_cal_rec CALREC
        on CALREC.sess = ACADREC.sess
        and CALREC.yr = ACADREC.yr
        and CALREC.prog = ACADREC.prog 
        and CALREC.acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')    THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                    END       
         -----------------------------------------------
         --STUDENT INFO
         -----------------------------------------------
        inner Join 
            (select id_rec.id, id_rec.firstname, id_rec.lastname, id_rec.addr_line1, id_rec.addr_line2, id_rec.addr_line3, id_rec.ss_no,
            id_rec.city, id_rec.st, id_rec.zip, id_rec.ctry
            from id_rec) StuID
            on acadrec.id = StuID.id
         -----------------------------------------------
         --TUITION AND FEES
         -----------------------------------------------
        left JOIN
            (SELECT IM.bgt_code AS Budget_Code, IM.id AS ID_Number, --IM.fa_yr,
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
            fabgt_rec   IM
                INNER JOIN  fabgtdtl_rec    Detail
                    ON  IM.fabgt_no =   Detail.fabgt_no
                    AND IM.fa_yr    =   CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')  THEN    MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                    ELSE    MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                    END
                GROUP BY
                    Budget_Code, ID_Number, IM.fa_yr
                order by ID_Number
                ) 
                BGT_COSTS
                on ACADREC.id = BGT_COSTS.ID_Number
         -----------------------------------------------
         --GRANTS
         -----------------------------------------------
        left join
            (SELECT
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
            )   AidOther
            on ACADREC.id= AidOther.Student_ID_Number
        ------------------------------------------------
        --CUMULATIVE Aid - Loans
        ------------------------------------------------
            LEFT JOIN
                (select AIDREC.id, 
                AIDREC.aid, AIDTBL.txt, sum(AIDREC.amt) as Aid_Amount, 
                loan_rec.beg_date
                from    aid_rec AIDREC, aid_table AIDTBL, loandisb_rec, loan_rec
                where   AIDREC.aid = AIDTBL.aid
                and loandisb_rec.aid_no = AIDREC.aid_no
                and loan_rec.loan_no = loandisb_rec.loan_no
                and AIDREC.amt_stat in ({0})
                AND (AIDTBL.aid like ('ALN%') or AIDTBL.aid like ('DIS%') or AIDTBL.aid like ('PNC%') or AIDTBL.aid like ('SMS%') or AIDTBL.aid like ('WEL%'))
                and AIDREC.stat = ('A')
                and AIDREC.amt > 0
                group by AIDREC.id, AIDREC.aid, AIDTBL.txt, loan_rec.beg_date) CUM_AID
                on ACADREC.ID = CUM_AID.ID
         -----------------------------------------------
         --EMAIL
         -----------------------------------------------
            LEFT JOIN
                (Select Eml.line1, Eml.id
                from aa_rec Eml
                where Eml.aa    =   'EML1'
                AND	TODAY   BETWEEN Eml.beg_date AND NVL(Eml.end_date, TODAY)
                ) Email
            ON  ACADREC.id      =   Email.id
         -----------------------------------------------
        ORDER BY
            student_id_number
    '''.format(amt_stat_values)
    return WIS_ACT_284_SQL