# This query returns all residential students for the current year and session
# Student's opt-in decision of 'N'
# The Y and N are somewhat counter-intuitive in that N means we can text them and Y means we cannot.
# Privacy - students who have FERP are excluded from the list
STUDENTS = '''
    SELECT DISTINCT DIR.id AS Student_ID, DIR.firstname AS First_Name, DIR.lastname AS Last_Name, DIR.email AS Email_Address,
    TRIM(NVL(CELL.phone,'')) AS Cell_Phone, TRIM(DIR.addr_line1) AS Address,
    TRIM(DIR.city) AS City, TRIM(DIR.st) AS State,
    TRIM(DIR.zip) AS Zip, HSG.yr AS Year, HSG.sess AS Session, HSG.intend_hsg AS Housing,
    CASE NVL(HSG.bldg,'')
        WHEN 'CMTR'  THEN 'Commuter'
        WHEN 'OFF'   THEN 'Off Campus'
                     ELSE TRIM(NVL(BLDG,''))
    END AS Building,
    CASE
        WHEN NVL(HSG.room,'') LIKE 'UN%' THEN ''
                                         ELSE NVL(HSG.room,'')
    END AS Room_Number, CELL.opt_out AS OPT_OUT, PROF.priv_code AS Privacy
    FROM directory_vw DIR
    INNER JOIN stu_serv_rec HSG ON DIR.id = HSG.id
    INNER JOIN profile_rec PROF ON DIR.id = PROF.id
    INNER JOIN acad_cal_rec ACR
    on HSG.sess = ACR.sess
    and HSG.yr = ACR.yr
    and ACR.acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')	THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                    END
    and ACR.beg_date >= TODAY
    and ACR.end_date < ADD_MONTHS(today,6)
    LEFT JOIN aa_rec CELL ON DIR.id = CELL.id
        AND CELL.aa = 'CELL'
        AND TODAY BETWEEN CELL.beg_date
        AND NVL(CELL.end_date, TODAY)
    where HSG.yr = YEAR(TODAY)
    AND HSG.intend_hsg = 'R'
    AND CELL.opt_out != 'Y'
    AND PROF.priv_code != 'FERP'
    ORDER BY
        DIR.lastname, DIR.firstname
'''