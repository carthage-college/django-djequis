# This query returns all residential students for the current year and session
# Student's opt-in decision of 'N'
# The Y and N are somewhat counter-intuitive in that N means we can text them
# and Y means we cannot.
# Privacy - students who have FERP are excluded from the list

STUDENTS = '''
    SELECT DISTINCT
        TRIM(NVL(bldg_table.txt,'')) || ' ' || TRIM(NVL(stu_serv_rec.room,''))
            AS unitcode,
        directory_vw.firstname AS firstname, directory_vw.lastname AS lastname,
        directory_vw.email AS emailaddress,
        TRIM(NVL(aa_rec.phone,'')) AS cellphone
    FROM directory_vw
    INNER JOIN stu_serv_rec ON directory_vw.id = stu_serv_rec.id
    INNER JOIN profile_rec ON directory_vw.id = profile_rec.id
    INNER JOIN acad_cal_rec ON stu_serv_rec.sess = acad_cal_rec.sess
    INNER JOIN bldg_table ON stu_serv_rec.bldg = bldg_table.bldg
    AND stu_serv_rec.yr = acad_cal_rec.yr
    AND acad_cal_rec.acyr = CASE
        WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
        ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
        END
    AND acad_cal_rec.beg_date >= TODAY
    AND acad_cal_rec.end_date < ADD_MONTHS(today,6)
    LEFT JOIN aa_rec ON directory_vw.id = aa_rec.id
        AND aa_rec.aa = 'CELL'
        AND TODAY BETWEEN aa_rec.beg_date
        AND NVL(aa_rec.end_date, TODAY)
        AND NVL(aa_rec.opt_out, '') = 'N'
    WHERE stu_serv_rec.yr = YEAR(TODAY)
        AND stu_serv_rec.intend_hsg = 'R'
        AND profile_rec.priv_code != 'FERP'
    ORDER BY
        directory_vw.lastname, directory_vw.firstname
'''
