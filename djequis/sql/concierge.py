# This query returns all residential students for the current year and session
# Student's opt-in decision of 'N'
# The Y and N are somewhat counter-intuitive in that N means we can text them
# and Y means we cannot.
# Privacy - students who have FERP are excluded from the list
STUDENTS = '''
SELECT
    TRIM(NVL(BLD.txt,'')) || ' ' || TRIM(NVL(SSR.room,'')) AS unitcode,
    DIR.firstname, DIR.lastname, DIR.email AS emailaddress,
    TRIM(NVL(PHN.phone,'')) AS cellphone
FROM
    directory_vw DIR
INNER JOIN stu_serv_rec     SSR ON DIR.id = SSR.id
INNER JOIN profile_rec      PRO ON DIR.id = PRO.id
INNER JOIN bldg_table       BLD ON SSR.bldg = BLD.bldg
INNER JOIN acad_cal_rec     CAL
    ON  SSR.sess = CAL.sess
    AND SSR.yr = CAL.yr
    AND TODAY BETWEEN CAL.beg_date AND CAL.end_date
    AND CAL.subsess = ''
    AND CAL.prog = 'UNDG'
LEFT JOIN aa_rec PHN
    ON  DIR.id = PHN.id
    AND PHN.aa = 'CELL'
    AND TODAY BETWEEN PHN.beg_date
    AND NVL(PHN.end_date, TODAY)
    AND NVL(PHN.opt_out, '') = 'N'
WHERE
    SSR.intend_hsg = 'R'
AND
    PRO.priv_code != 'FERP'
ORDER BY
    DIR.lastname, DIR.firstname
'''
