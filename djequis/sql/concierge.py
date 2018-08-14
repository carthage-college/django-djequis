# This query returns all residential students for the current year and session
# Student's opt-in decision of 'N'
# The Y and N are somewhat counter-intuitive in that N means we can text them and Y means we cannot.
# Privacy - students who have FERP are excluded from the list
STUDENTS = '''
    SELECT DISTINCT 
        DIR.id AS studentid, DIR.firstname AS firstname, DIR.lastname AS lastname, 
        DIR.email AS emailaddress, '2001 Alford Park Drive' AS address, 'Kenosha' AS city, 
        'WI' AS state, '53140' AS zip
    FROM directory_vw DIR
        INNER JOIN stu_serv_rec SSR ON DIR.id = SSR.id
        INNER JOIN profile_rec PROF ON DIR.id = PROF.id
        INNER JOIN acad_cal_rec ACR ON SSR.sess = ACR.sess
        AND SSR.yr = ACR.yr
        AND ACR.acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')   THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                        ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                        END
        AND ACR.beg_date >= TODAY
        AND ACR.end_date < ADD_MONTHS(today,6)
        LEFT JOIN aa_rec ON DIR.id = aa_rec.id
            AND aa_rec.aa = 'CELL'
            AND TODAY BETWEEN aa_rec.beg_date
            AND NVL(aa_rec.end_date, TODAY)
        WHERE SSR.yr = YEAR(TODAY)
        AND SSR.intend_hsg = 'R'
        AND PROF.priv_code != 'FERP'
    ORDER BY
        DIR.lastname, DIR.firstname
'''