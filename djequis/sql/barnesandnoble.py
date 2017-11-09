# builds academic calendar for active terms with pre & post grace periods per term
TMP_ACTV_SESS = '''
    SELECT
        TODAY as today_date, acad_cal_rec.acyr, acad_cal_rec.sess,
        acad_cal_rec.yr, acad_cal_rec.beg_date, tmp_sess_grace.pre_grace,
        (acad_cal_rec.beg_date-pre_grace) as pre_calc, acad_cal_rec.end_date,
        tmp_sess_grace.post_grace, (acad_cal_rec.end_date+post_grace) as post_calc,
        acad_cal_rec.subsess
    FROM
        acad_cal_rec,
            (SELECT TRIM(acad_cal_rec.sess) AS sess,
                CASE
                    WHEN sess = 'AA' THEN 45
                    WHEN sess = 'AB' THEN 60
                    WHEN sess = 'AG' THEN 10
                    WHEN sess = 'AK' THEN 25
                    WHEN sess = 'AM' THEN 45
                    WHEN sess = 'AS' THEN 25
                    WHEN sess = 'AT' THEN 45
                    WHEN sess = 'GA' THEN 45
                    WHEN sess = 'GB' THEN 45
                    WHEN sess = 'GC' THEN 45
                    WHEN sess = 'GE' THEN 25
                    WHEN sess = 'RA' THEN 21
                    WHEN sess = 'RB' THEN 10
                    WHEN sess = 'RC' THEN 21
                    WHEN sess = 'RE' THEN 25
                    ELSE 99
                END AS pre_grace,
                CASE
                    WHEN sess = 'AA' THEN 45
                    WHEN sess = 'AB' THEN 20
                    WHEN sess = 'AG' THEN 35
                    WHEN sess = 'AK' THEN 52
                    WHEN sess = 'AM' THEN 36
                    WHEN sess = 'AS' THEN 45
                    WHEN sess = 'AT' THEN 10
                    WHEN sess = 'GA' THEN 30
                    WHEN sess = 'GB' THEN 4
                    WHEN sess = 'GC' THEN 19
                    WHEN sess = 'GE' THEN 45
                    WHEN sess = 'RA' THEN 42
                    WHEN sess = 'RB' THEN 2
                    WHEN sess = 'RC' THEN 15
                    WHEN sess = 'RE' THEN 45
                    ELSE 99
                END AS post_grace
            FROM acad_cal_rec
            WHERE acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                        ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100) END
                AND subsess= ""
                AND sess IN ("AA","AB","AG","AK","AM","AS","AT","GA","GB","GC", "GE", "RA","RB","RC", "RE")) tmp_sess_grace
    WHERE
        TODAY BETWEEN (beg_date - tmp_sess_grace.pre_grace) AND (end_date + tmp_sess_grace.post_grace)
        AND acad_cal_rec.sess = tmp_sess_grace.sess
        AND acad_cal_rec.subsess = " "
'''
# fetch active students and sets budget limit for export (books = '100' & 3000.00) and active UBAL holds
STU_ACAD_REC_100 = '''
    SELECT
        sar.id AS Userid, TRIM(ir.lastname) AS Elastname, TRIM(ir.firstname) AS Efirstname,
        UPPER(LEFT(ir.middlename,1)) AS Xmiddleinit,
        CASE
            WHEN tmpU.id IS NOT NULL THEN 0
                                     ELSE 300000
        END AS Xcred_limit, 100 AS EProviderCode, TO_CHAR(MIN(tas.beg_date), '%m/%d/%Y') AS Ebegdate,
        TO_CHAR(MAX(tas.end_date), '%m/%d/%Y') AS Eenddate, "" AS Eidtype, "" AS Erecordtype, "D" AS Eaccttype
    FROM
        stu_acad_rec sar
        INNER JOIN id_rec ir ON sar.id = ir.id
        INNER JOIN
            (SELECT
                TODAY as today_date, acad_cal_rec.acyr, acad_cal_rec.sess,
                acad_cal_rec.yr, acad_cal_rec.beg_date, pre_grace,
                (acad_cal_rec.beg_date-pre_grace) as pre_calc, acad_cal_rec.end_date,
                post_grace, (acad_cal_rec.end_date+post_grace) as post_calc,
                acad_cal_rec.subsess
            FROM
                acad_cal_rec,
                (SELECT TRIM(acad_cal_rec.sess) AS sess,
                    CASE
                        WHEN sess = 'AA' THEN 45
                        WHEN sess = 'AB' THEN 60
                        WHEN sess = 'AG' THEN 10
                        WHEN sess = 'AK' THEN 25
                        WHEN sess = 'AM' THEN 45
                        WHEN sess = 'AS' THEN 25
                        WHEN sess = 'AT' THEN 45
                        WHEN sess = 'GA' THEN 45
                        WHEN sess = 'GB' THEN 45
                        WHEN sess = 'GC' THEN 45
                        WHEN sess = 'GE' THEN 25
                        WHEN sess = 'RA' THEN 21
                        WHEN sess = 'RB' THEN 10
                        WHEN sess = 'RC' THEN 21
                        WHEN sess = 'RE' THEN 25
                        ELSE 99
                    END AS pre_grace,
                    CASE
                        WHEN sess = 'AA' THEN 45
                        WHEN sess = 'AB' THEN 20
                        WHEN sess = 'AG' THEN 35
                        WHEN sess = 'AK' THEN 52
                        WHEN sess = 'AM' THEN 36
                        WHEN sess = 'AS' THEN 45
                        WHEN sess = 'AT' THEN 10
                        WHEN sess = 'GA' THEN 30
                        WHEN sess = 'GB' THEN 4
                        WHEN sess = 'GC' THEN 19
                        WHEN sess = 'GE' THEN 45
                        WHEN sess = 'RA' THEN 42
                        WHEN sess = 'RB' THEN 2
                        WHEN sess = 'RC' THEN 15
                        WHEN sess = 'RE' THEN 45
                        ELSE 99
                    END AS post_grace
                FROM acad_cal_rec
                WHERE acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                            ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100) END
                AND subsess= ""
                AND sess IN ("AA","AB","AG","AK","AM","AS","AT","GA","GB","GC", "GE", "RA","RB","RC", "RE")) tmp_sess_grace
            WHERE
                TODAY BETWEEN (beg_date - pre_grace) AND (end_date + post_grace)
                AND acad_cal_rec.sess = tmp_sess_grace.sess
                AND acad_cal_rec.subsess = " ") as tas ON sar.sess = tas.sess
                LEFT JOIN
                    (SELECT id
                    FROM hold_rec
                    WHERE hld ="UBAL"
                    AND (end_date IS NULL or end_date > TODAY)) tmpU ON sar.id = tmpU.id
    WHERE
        tas.yr = sar.yr
        AND sar.subprog IN ("TRAD","PTSM","TRAP","YOP","7WK","MED","ACT")
        AND sar.reg_hrs > 0
        AND (sar.reg_stat = "R" OR sar.reg_stat = "C")
    GROUP BY
        sar.id, Elastname, Efirstname, Xmiddleinit, Xcred_limit,
        EProviderCode, Eidtype, Erecordtype, Eaccttype
    ORDER BY Elastname, Efirstname
'''
# fetch active students and sets budget limit for export (supplies = '200' & 50.00) and active UBAL holds
STU_ACAD_REC_200 = '''
    SELECT
        sar.id AS Userid, TRIM(ir.lastname) AS Elastname, TRIM(ir.firstname) AS Efirstname,
        UPPER(LEFT(ir.middlename,1)) AS Xmiddleinit,
        CASE
            WHEN tmpU.id IS NOT NULL THEN 0
                                     ELSE 5000
        END AS Xcred_limit, 200 AS EProviderCode, TO_CHAR(MIN(tas.beg_date), '%m/%d/%Y') AS Ebegdate,
        TO_CHAR(MAX(tas.end_date), '%m/%d/%Y') AS Eenddate, "" AS Eidtype, "" AS Erecordtype, "D" AS Eaccttype
    FROM
        stu_acad_rec sar
        INNER JOIN id_rec ir ON sar.id = ir.id
        INNER JOIN
            (SELECT
                TODAY as today_date, acad_cal_rec.acyr, acad_cal_rec.sess,
                acad_cal_rec.yr, acad_cal_rec.beg_date, tmp_sess_grace.pre_grace,
                (acad_cal_rec.beg_date-pre_grace) as pre_calc, acad_cal_rec.end_date,
                tmp_sess_grace.post_grace, (acad_cal_rec.end_date+post_grace) as post_calc,
                acad_cal_rec.subsess
            FROM
                acad_cal_rec,
                (SELECT TRIM(acad_cal_rec.sess) AS sess,
                    CASE
                        WHEN sess = 'AA' THEN 45
                        WHEN sess = 'AB' THEN 60
                        WHEN sess = 'AG' THEN 10
                        WHEN sess = 'AK' THEN 25
                        WHEN sess = 'AM' THEN 45
                        WHEN sess = 'AS' THEN 25
                        WHEN sess = 'AT' THEN 45
                        WHEN sess = 'GA' THEN 45
                        WHEN sess = 'GB' THEN 45
                        WHEN sess = 'GC' THEN 45
                        WHEN sess = 'GE' THEN 25
                        WHEN sess = 'RA' THEN 21
                        WHEN sess = 'RB' THEN 10
                        WHEN sess = 'RC' THEN 21
                        WHEN sess = 'RE' THEN 25
                        ELSE 99
                    END AS pre_grace,
                    CASE
                        WHEN sess = 'AA' THEN 45
                        WHEN sess = 'AB' THEN 20
                        WHEN sess = 'AG' THEN 35
                        WHEN sess = 'AK' THEN 52
                        WHEN sess = 'AM' THEN 36
                        WHEN sess = 'AS' THEN 45
                        WHEN sess = 'AT' THEN 10
                        WHEN sess = 'GA' THEN 30
                        WHEN sess = 'GB' THEN 4
                        WHEN sess = 'GC' THEN 19
                        WHEN sess = 'GE' THEN 45
                        WHEN sess = 'RA' THEN 42
                        WHEN sess = 'RB' THEN 2
                        WHEN sess = 'RC' THEN 15
                        WHEN sess = 'RE' THEN 45
                        ELSE 99
                    END AS post_grace
                FROM acad_cal_rec
                WHERE acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                            ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100) END
                    AND subsess= ""
                    AND sess IN ("AA","AB","AG","AK","AM","AS","AT","GA","GB","GC", "GE", "RA","RB","RC", "RE")) tmp_sess_grace
            WHERE
                TODAY BETWEEN (beg_date - tmp_sess_grace.pre_grace) AND (end_date + tmp_sess_grace.post_grace)
                AND acad_cal_rec.sess = tmp_sess_grace.sess
                AND acad_cal_rec.subsess = " ") tas ON sar.sess = tas.sess
                LEFT JOIN
                    (SELECT id
                    FROM hold_rec
                    WHERE hld ="UBAL"
                    AND (end_date IS NULL or end_date > TODAY)) tmpU ON sar.id = tmpU.id
    WHERE
        tas.yr = sar.yr
        AND sar.subprog IN ("TRAD","PTSM","TRAP","YOP","7WK","MED","ACT")
        AND sar.reg_hrs > 0
        AND (sar.reg_stat = "R" OR sar.reg_stat = "C")
    GROUP BY
        sar.id, Elastname, Efirstname, Xmiddleinit, Xcred_limit,
        EProviderCode, Eidtype, Erecordtype, Eaccttype
    ORDER BY Elastname, Efirstname;
'''
# *** Need description
EXENRCRS = '''
    SELECT
        "001" AS bnUnitNo, bnTerm, SUBSTR(tfc.yr,3,2) AS bnYear,
        TRIM(LEFT(sr.crs_no,4)) AS bnDept, TRIM(SUBSTR(sr.crs_no,5,8)) AS bnCourseNo,
        TRIM(sr.sec_no) AS bnSectionNo, TRIM(LEFT(ir.fullname,20)) AS bnProfName,
        MAX(sr.max_reg) AS bnMaxCapcty, MAX(sr.reg_num) AS bnEstEnrlmnt,
        MAX(sr.reg_num) AS bnActEnrlmnt, "" AS bnContClss, "" AS bnEvngClss,
        "" AS bnExtnsnClss, "" AS bnTxtnetClss, "" AS bnLoctn,
        TRIM(LEFT(cr.title1,25)) AS bntCourseTitl,
        TRIM(sr.crs_no || " " || sr.sec_no) AS bnCourseID
    FROM
        sec_rec sr
            INNER JOIN
            (SELECT acr.acyr AS calyr, TRIM(acr.sess) AS sess, YEAR(acr.end_date) AS yr,
                CASE
                    WHEN sess = "AA" THEN 45
                    WHEN sess = "AB" THEN 60
                    WHEN sess = "AG" THEN 10
                    WHEN sess = "AK" THEN 25
                    WHEN sess = "AM" THEN 45
                    WHEN sess = "AS" THEN 25
                    WHEN sess = "AT" THEN 45
                    WHEN sess = "GA" THEN 45
                    WHEN sess = "GB" THEN 45
                    WHEN sess = "GC" THEN 45
                    WHEN sess = 'GE' THEN 25
                    WHEN sess = "RA" THEN 21
                    WHEN sess = "RB" THEN 10
                    WHEN sess = "RC" THEN 21
                    WHEN sess = 'RE' THEN 25
                    ELSE 99
                END AS pre_grace,
                CASE
                    WHEN sess = "AA" THEN 45
                    WHEN sess = "AB" THEN 20
                    WHEN sess = "AG" THEN 35
                    WHEN sess = "AK" THEN 52
                    WHEN sess = "AM" THEN 36
                    WHEN sess = "AS" THEN 45
                    WHEN sess = "AT" THEN 10
                    WHEN sess = "GA" THEN 30
                    WHEN sess = "GB" THEN 4
                    WHEN sess = "GC" THEN 19
                    WHEN sess = 'GE' THEN 45
                    WHEN sess = "RA" THEN 42
                    WHEN sess = "RB" THEN 2
                    WHEN sess = "RC" THEN 15
                    WHEN sess = 'RE' THEN 45
                    ELSE 99
                END AS post_grace,
                CASE
                    WHEN sess = "AA" THEN "G"
                    WHEN sess = "AB" THEN "G"
                    WHEN sess = "AG" THEN "J"
                    WHEN sess = "AK" THEN "S"
                    WHEN sess = "AM" THEN "S"
                    WHEN sess = "AS" THEN "B"
                    WHEN sess = "AT" THEN "B"
                    WHEN sess = "GA" THEN "F"
                    WHEN sess = "GB" THEN "I"
                    WHEN sess = "GC" THEN "W"
                    WHEN sess = 'GE' THEN "A"
                    WHEN sess = "RA" THEN "F"
                    WHEN sess = "RB" THEN "I"
                    WHEN sess = "RC" THEN "W"
                    WHEN sess = 'RE' THEN "A"
                    ELSE "z"
                END AS bnTerm
            FROM acad_cal_rec acr
            WHERE end_date-0 >= TODAY
            AND subsess= ""
            AND sess IN ("AA","AB","AG","AK","AM","AS","AT","GA","GB","GC", "GE", "RA",
                        "RB","RC","RE")) tfc ON tfc.sess = sr.sess
                INNER JOIN id_rec ir ON sr.fac_id = ir.id
                INNER JOIN crs_rec cr ON sr.crs_no = cr.crs_no
    WHERE
        tfc.yr = sr.yr
    AND
        sr.cat = cr.cat
    AND
        sr.stat IN ("R","O","C")
    GROUP BY
        bnUnitNo, bnTerm, bnYear, bnDept, bnCourseNo, bnSectionNo, bnProfName,
        bntCourseTitl, bnCourseID
    ORDER BY
        bnDept, bnCourseNo, bnYear, bnSectionNo;
'''