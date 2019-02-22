SELECT DISTINCT
    '00383900' AS OPEID,
    '20' || LEFT(CALREC.acyr, 2) || '-20' || RIGHT(CALREC.acyr, 2) AS AcadYear,
    ACADREC.sess,
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
    TRIM(CUM_AID.txt) AS Loan_name,
    NVL(CUM_AID.Aid_Amount, 0.00) AS Aid_Amount,
    NVL(AidOther.c_InstGrants, 0.00) AS c_InstGrants,
    NVL(AidOther.c_InstScholar, 0.00) AS c_InstScholar,
    NVL(AidOther.c_FedGrants, 0.00) AS c_FedGrants,
    NVL(AidOther.c_SteGrants, 0.00) AS c_SteGrants,
    NVL(AidOther.c_OutsideAid, 0.00) AS c_OutsideAid,
    --Loan Date
    TO_CHAR(CUM_AID.beg_date, '%Y%m%d') AS Loan_Date,
    --Budget Summary
    --ACADREC.prog, ACADREC.subprog,
    CASE
        WHEN ACADREC.prog = 'PRDV'
        THEN 2200
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_TUFE,0) = 0
        THEN 10160
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_TUFE,0) = 0
        THEN 43550
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_TUFE,0) = 0
        THEN 9200
        WHEN ACADREC.subprog = 'PTSM' AND NVL(BGT_COSTS.No_TUFE,0) = 0
        THEN 9200
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_TUFE,0) = 0
        THEN 14700
        WHEN NVL(BGT_COSTS.No_TUFE,0) > 0
        THEN BGT_COSTS.No_TUFE
        WHEN NVL(BGT_COSTS.No_TUFE,0) = 0 AND NVL(BGT_COSTS.Trad_TUFE,0) > 0
        THEN BGT_COSTS.Trad_TUFE
    END AS c_TUFE,
    CASE
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_RMBD,0) = 0
        THEN 8600
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_RMBD,0) = 0
        THEN 11600
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_RMBD,0) = 0
        THEN 9000
        WHEN ACADREC.subprog = 'PTSM' AND NVL(BGT_COSTS.No_RMBD,0) = 0
        THEN 9000
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_RMBD,0) = 0
        THEN 10026
        WHEN NVL(BGT_COSTS.No_RMBD,0) > 0
        THEN BGT_COSTS.No_RMBD
        WHEN NVL(BGT_COSTS.No_RMBD,0) = 0 AND NVL(BGT_COSTS.Trad_RMBD,0) > 0
        THEN BGT_COSTS.Trad_RMBD
    END AS c_RMBD,
    CASE
        WHEN ACADREC.prog = 'PRDV'
        THEN 2200
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_BOOK,0) = 0
        THEN 1600
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_BOOK,0) = 0
        THEN 1200
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_BOOK,0) = 0
        THEN 1600
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_BOOK,0) = 0
        THEN 1200
        WHEN NVL(BGT_COSTS.No_BOOK,0) > 0
        THEN BGT_COSTS.No_BOOK
        WHEN NVL(BGT_COSTS.No_BOOK,0) = 0 AND NVL(BGT_COSTS.Trad_BOOK,0) > 0
        THEN BGT_COSTS.Trad_BOOK
    END AS c_BOOK,
    CASE
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_TRAN,0) = 0
        THEN 1200
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_TRAN,0) = 0
        THEN 1200
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_TRAN,0) = 0
        THEN 1200
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_TRAN,0) = 0
        THEN 2100
        WHEN NVL(BGT_COSTS.No_TRAN,0) > 0
        THEN BGT_COSTS.No_TRAN
        WHEN NVL(BGT_COSTS.No_TRAN,0) = 0 AND NVL(BGT_COSTS.Trad_TRAN,0) > 0
        THEN BGT_COSTS.Trad_TRAN
    END AS c_TRAN,
    CASE
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_MISC,0) = 0
        THEN 1700
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_MISC,0) = 0
        THEN 1700
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_MISC,0) = 0
        THEN 1700
        WHEN ACADREC.subprog = 'PTSM' AND NVL(BGT_COSTS.No_MISC,0) = 0
        THEN 1700
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_MISC,0) = 0
        THEN 1290
        WHEN NVL(BGT_COSTS.No_MISC,0) > 0
        THEN BGT_COSTS.No_MISC
        WHEN NVL(BGT_COSTS.No_MISC,0) = 0 AND NVL(BGT_COSTS.Trad_MISC,0) > 0
        THEN BGT_COSTS.Trad_MISC
    END AS c_MISC,
    CASE
        WHEN ACADREC.prog = 'GRAD' AND NVL(BGT_COSTS.No_LOAN,0) = 0
        THEN 200
        WHEN ACADREC.subprog = 'TRAD' AND NVL(BGT_COSTS.No_LOAN,0) = 0
        THEN 200
        WHEN ACADREC.subprog = 'TRAP' AND NVL(BGT_COSTS.No_LOAN,0) = 0
        THEN 100
        WHEN ACADREC.subprog = '7WK' AND NVL(BGT_COSTS.No_LOAN,0) = 0
        THEN 216
        WHEN NVL(BGT_COSTS.No_LOAN,0) > 0
        THEN BGT_COSTS.No_LOAN
        WHEN NVL(BGT_COSTS.No_LOAN,0) = 0 AND NVL(BGT_COSTS.Trad_LOAN,0) > 0
        THEN BGT_COSTS.Trad_LOAN
    END AS c_LOAN
FROM
    -----------------------------------------------
    --ACTIVE STUDENT LIST
    -----------------------------------------------
    stu_acad_rec ACADREC
    INNER JOIN
        acad_cal_rec CALREC
    ON
        CALREC.sess = ACADREC.sess
    AND
        CALREC.yr = ACADREC.yr
    AND
        CALREC.prog = ACADREC.prog
    AND 
        CALREC.sess in ('AK', 'AM', 'GC', 'KC',  'PC', 'RC', 'YC')
    AND
        CALREC.acyr =
        CASE
            WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
            THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
            ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
        END
    AND ACADREC.ID
        NOT IN
            (SELECT distinct id FROM stu_acad_rec s, acad_cal_rec a
                WHERE
                s.sess = a.sess
                AND s.yr = a.yr
                AND s.prog = a.prog
                AND a.sess in ('AA', 'AB', 'GA', 'KA', 'PA', 'QB', 'RA', 'YA')
                AND
                A.acyr =
                    CASE
                    WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
                    THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                    END)
    -----------------------------------------------
    --STUDENT INFO
    -----------------------------------------------
    INNER JOIN (
        SELECT
            id_rec.id, id_rec.firstname, id_rec.lastname, id_rec.addr_line1,
            id_rec.addr_line2, id_rec.addr_line3, id_rec.ss_no, id_rec.city,
            id_rec.st, id_rec.zip, id_rec.ctry
        FROM
            id_rec
    ) StuID
    ON
        acadrec.id = StuID.id
    -----------------------------------------------
    --TUITION AND FEES
    -----------------------------------------------
    LEFT JOIN (
        SELECT
            IM.bgt_code AS Budget_Code, IM.id AS ID_Number,
            SUM(
                CASE
                    WHEN Detail.faitem = 'TUFE' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_TUFE,
            SUM(
                CASE
                    WHEN Detail.faitem = 'RMBD' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_RMBD,
            SUM(
                CASE
                    WHEN Detail.faitem = 'BOOK' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_BOOK,
            SUM(
                CASE
                    WHEN Detail.faitem = 'TRAN' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_TRAN,
            SUM(
                CASE
                    WHEN Detail.faitem = 'MISC' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_MISC,
            SUM(
                CASE
                    WHEN Detail.faitem = 'LOAN' AND IM.bgt_code = 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS Trad_LOAN,
            --No IM Detail
            SUM(
                CASE
                    WHEN Detail.faitem = 'TUFE' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS No_TUFE,
            SUM(
                CASE
                    WHEN Detail.faitem = 'RMBD' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS No_RMBD,
            SUM(
                CASE
                    WHEN Detail.faitem = 'BOOK' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt ELSE 0 END
            )
            AS No_BOOK,
            SUM(
                CASE
                    WHEN Detail.faitem = 'TRAN' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS No_TRAN,
            SUM(
                CASE
                    WHEN Detail.faitem = 'MISC' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS No_MISC,
            SUM(
                CASE
                    WHEN Detail.faitem = 'LOAN' AND IM.bgt_code <> 'TRAD IM'
                    THEN Detail.amt
                    ELSE 0
                END
            )
            AS No_LOAN
        FROM
            fabgt_rec IM
            INNER JOIN
                fabgtdtl_rec Detail
            ON
                IM.fabgt_no = Detail.fabgt_no
            AND
                IM.fa_yr =
                CASE
                    WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
                    THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                END
            GROUP BY
                Budget_Code, ID_Number, IM.fa_yr
            ORDER BY ID_Number
    ) BGT_COSTS
    ON
        ACADREC.id = BGT_COSTS.ID_Number
    -----------------------------------------------
    -- end LEFT JOIN for TUITION AND FEES
    -----------------------------------------------
    -- GRANTS
    -----------------------------------------------
    LEFT JOIN (
        SELECT
            Aid_Record.id AS Student_ID_Number,
            SUM(
                CASE
                    WHEN Aid_Table.txt LIKE '%Grant%'
                    AND Aid_Table.frm_code IN (
                        'INSF','INSU','PCAR','PMRT','PCEI'
                    )
                    THEN Aid_Record.amt
                    ELSE 0
                END
            )
            AS c_InstGrants,
            SUM(
                CASE
                    WHEN Aid_Table.txt NOT LIKE '%Grant%'
                    AND Aid_Table.frm_code IN (
                        'INSF','INSU','PCAR','PMRT','PCEI'
                    )
                    THEN Aid_Record.amt
                    ELSE 0
                END
            )
                AS c_InstScholar,
            SUM(
                CASE
                    WHEN Aid_Table.frm_code = 'PFGR'
                    THEN Aid_Record.amt
                    ELSE 0
                END
            )
                AS c_FedGrants,
            SUM(
                CASE
                    WHEN Aid_Table.frm_code = 'PSGR'
                    THEN Aid_Record.amt
                    ELSE 0
                END
            )
                AS c_SteGrants,
            SUM(
                CASE
                    WHEN Aid_Table.frm_code = 'POUT'
                    THEN Aid_Record.amt
                    ELSE 0
                END
            )
            AS c_OutsideAid
        FROM
            aid_rec Aid_Record
            INNER JOIN
                aid_table Aid_Table
            ON
                Aid_Record.aid = Aid_Table.aid
            WHERE
                Aid_Record.id > 0
            AND
                Aid_Record.fa_yr =
                CASE
                    WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
                    THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                END
            AND
                Aid_Record.stat IN ('A')
            AND
                Aid_Record.amt_stat IN ('AA','AD','AP','EA')
            AND
                Aid_Record.amt > 0
            GROUP BY
                Student_ID_Number
    ) AidOther
    ON
        ACADREC.id = AidOther.Student_ID_Number
    -----------------------------------------------
    -- end LEFT JOIN for GRANTS
    ------------------------------------------------
    -- CUMULATIVE Aid - Loans
    ------------------------------------------------
    LEFT JOIN (
        SELECT
            AIDREC.id, AIDREC.aid, AIDTBL.txt,
            SUM(AIDREC.amt) AS Aid_Amount,
            loan_rec.beg_date
        FROM
            aid_rec AIDREC, aid_table AIDTBL, loandisb_rec, loan_rec
        WHERE
            AIDREC.aid = AIDTBL.aid
            AND loandisb_rec.aid_no = AIDREC.aid_no
            AND loan_rec.loan_no = loandisb_rec.loan_no
            AND AIDREC.amt_stat IN ('AA','AD','AP','EA')
            AND (
                AIDTBL.aid LIKE ('ALN%')
                OR
                AIDTBL.aid LIKE ('DIS%')
                OR
                AIDTBL.aid LIKE ('PNC%')
                OR
                AIDTBL.aid LIKE ('SMS%')
                OR
                AIDTBL.aid LIKE ('WEL%')
            )
            AND AIDREC.stat = 'A'
            AND AIDREC.amt > 0
        GROUP BY
            AIDREC.id, AIDREC.aid, AIDTBL.txt, loan_rec.beg_date
    ) CUM_AID
    ON
        ACADREC.ID = CUM_AID.ID
    -----------------------------------------------
    -- end LEFT JOIN for CUMULATIVE Aid - Loans
    -----------------------------------------------
    -- EMAIL
    -----------------------------------------------
    LEFT JOIN (
        SELECT  Eml.line1, Eml.id
        FROM    aa_rec Eml
        WHERE   Eml.aa = 'EML1'
        AND     TODAY BETWEEN Eml.beg_date AND NVL(Eml.end_date, TODAY)
    ) Email
    ON
        ACADREC.id = Email.id
    -----------------------------------------------
    -- end LEFT JOIN for EMAIL
    -----------------------------------------------
WHERE
    ACADREC.subprog != 'UWPK'
ORDER BY
    student_id_number
