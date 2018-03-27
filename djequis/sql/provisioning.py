CURRENT_STUDENTS='''
    SELECT
        adm_rec.id, TRIM(id_rec.firstname) AS firstname, TRIM(id_rec.lastname) AS lastname, TRIM(cvid_rec.ldap_name) AS ldap_name
    FROM
        adm_rec INNER JOIN  id_rec          ON  adm_rec.id              =   id_rec.id
                INNER JOIN  acad_cal_rec    ON  adm_rec.plan_enr_sess   =   acad_cal_rec.sess
                                            AND adm_rec.plan_enr_yr     =   acad_cal_rec.yr
                                            AND acad_cal_rec.subsess    =   ' '
                LEFT JOIN   stu_acad_rec    ON  adm_rec.plan_enr_yr     =   stu_acad_rec.yr
                                            AND adm_rec.plan_enr_sess   =   stu_acad_rec.sess
                                            AND adm_rec.id              =   stu_acad_rec.id
                                            AND stu_acad_rec.reg_stat   IN  ('C','R')
                LEFT JOIN   cvid_rec        ON  adm_rec.id              =   cvid_rec.cx_id
    --TODO: Why the additional 150 days? Should the pregrace value be updated in the provsnrule_rec entry be updated or additional records entered to account for other queries in UNION?
    WHERE
        acad_cal_rec.beg_date   <=  TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'ActvDir') + 150
    AND
        TODAY                   <=  NVL(acad_cal_rec.end_date, TODAY)
    AND
        adm_rec.primary_app     =   'Y'
    --TODO: The JOIN condition looks for reg_stat of C or R so this WHERE condition would only find records where the JOIN was unsuccessful. Is this correct?
    AND
        stu_acad_rec.reg_stat   IS  NULL
    AND
        adm_rec.app_no IN (
            SELECT ctc_rec.app_no FROM ctc_rec
            WHERE ctc_rec.tick = 'ADM'
            AND ctc_rec.resrc   IN  ('ADVREGDT','INADVREG','TADVREG')
            AND ctc_rec.stat    IN  ('C','E')
            AND ctc_rec.due_date - 10 <= TODAY
            AND ctc_rec.add_date >= TODAY - 390
        )
    AND
        cvid_rec.ldap_name      IS  NULL
UNION
-- MSW students (we use adm_rec since they do not end up appearing in our student information system, but they need to be provisioned for printing, etc.)
    SELECT
        adm_rec.id, TRIM(id_rec.firstname) AS firstname, TRIM(id_rec.lastname) AS lastname, TRIM(cvid_rec.ldap_name) AS ldap_name
    FROM
        adm_rec INNER JOIN  id_rec          ON  adm_rec.id              =   id_rec.id
                INNER JOIN  acad_cal_rec    ON  adm_rec.plan_enr_yr     =   acad_cal_rec.yr
                                            AND adm_rec.plan_enr_sess   =   acad_cal_rec.sess
                                            AND acad_cal_rec.subsess    =   ' '
                LEFT JOIN   cvid_rec        ON  adm_rec.id              =   cvid_rec.cx_id
    WHERE
        adm_rec.primary_app     =   'Y'
    AND
        adm_rec.subprog         =   'MSW'
    AND
        adm_rec.plan_enr_yr     >=  YEAR(CURRENT) - 1
    AND
        adm_rec.enrstat         =   'APPLIED'
    AND
        acad_cal_rec.beg_date   >=  TODAY - (SELECT postgrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'MSW') - 300
    AND
        acad_cal_rec.beg_date   <=  TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'MSW')
    AND
        cvid_rec.ldap_name      IS  NULL
UNION
-- stu_acad_rec records
    SELECT
        stu_acad_rec.id, TRIM(id_rec.firstname) AS firstname, TRIM(id_rec.lastname) AS lastname, TRIM(cvid_rec.ldap_name) AS ldap_name
    FROM
        stu_acad_rec    INNER JOIN  acad_cal_rec    ON  stu_acad_rec.sess   =   acad_cal_rec.sess
                                                    AND stu_acad_rec.yr     =   acad_cal_rec.yr
                        INNER JOIN  id_rec          ON  stu_acad_rec.id     =   id_rec.id
                        LEFT JOIN   cvid_rec        ON  stu_acad_rec.id     =   cvid_rec.cx_id
    WHERE
        acad_cal_rec.beg_date   <=  TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'ActvDir')
    AND
        TODAY                   <=  NVL(acad_cal_rec.end_date, TODAY)
    AND
        acad_cal_rec.subsess    =   ' '
    AND
        stu_acad_rec.reg_stat   IN  ('R','C')
    AND
        cvid_rec.ldap_name      IS  NULL
UNION
-- prog_enr_rec records (should be redundant with above stu_acad_rec records)
    SELECT
        prog_enr_rec.id, TRIM(id_rec.firstname) AS firstname, TRIM(id_rec.lastname) AS lastname, TRIM(cvid_rec.ldap_name) AS ldap_name
    FROM
        prog_enr_rec    INNER JOIN  id_rec          ON  prog_enr_rec.id         =   id_rec.id
                        INNER JOIN  acad_cal_rec    ON  prog_enr_rec.adm_sess   =   acad_cal_rec.sess
                                                    AND acad_cal_rec.subsess    =   ' '
                                                    AND (
                                                        (prog_enr_rec.adm_yr    =   acad_cal_rec.yr AND prog_enr_rec.acst   IN  ('GOOD','ACPR'))
                                                        OR
                                                        prog_enr_rec.acst       IN  ('READ','PROR')
                                                    )
                        LEFT JOIN   stu_acad_rec    ON  prog_enr_rec.adm_yr     =   stu_acad_rec.yr
                                                    AND prog_enr_rec.adm_sess   =   stu_acad_rec.sess
                                                    AND prog_enr_rec.id         =   stu_acad_rec.id
                                                    AND stu_acad_rec.reg_stat   IN  ('R','C')
                        LEFT JOIN   cvid_rec        ON  prog_enr_rec.id         =   cvid_rec.cx_id
    WHERE
        acad_cal_rec.beg_date   <=  TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'ActvDir')
    AND
        TODAY                   <=  NVL(acad_cal_rec.end_date, TODAY)
    --TODO: See above: The JOIN condition looks for reg_stat of C or R so this WHERE condition would only find records where the JOIN was unsuccessful. Is this correct?
    AND
        stu_acad_rec.reg_stat   IS  NULL
    AND
        cvid_rec.ldap_name      IS  NULL
UNION
-- regclr_rec recoprds (this will pick up straggling Adult Ed students because of the way Continuing Studies clears everyone who has recently been enrolled)
    SELECT
        regclr_rec.id, TRIM(id_rec.firstname) AS firstname, TRIM(id_rec.lastname) AS lastname, TRIM(cvid_rec.ldap_name) AS ldap_name
    FROM
        regclr_rec  INNER JOIN  acad_cal_rec    ON  regclr_rec.sess         =   acad_cal_rec.sess
                                                AND regclr_rec.yr           =   acad_cal_rec.yr
                                                AND acad_cal_rec.subsess    =   ' '
                    INNER JOIN  id_rec          ON  regclr_rec.id           =   id_rec.id
                    LEFT JOIN   cvid_rec        ON  regclr_rec.id           =   cvid_rec.cx_id
    WHERE
        acad_cal_rec.beg_date   <= TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'ActvDir')
    AND
        TODAY                   <=  NVL(acad_cal_rec.end_date, TODAY)
    AND
        cvid_rec.ldap_name      IS  NULL
-- weed out duplicates
GROUP BY
    id, firstname, lastname, ldap_name
ORDER BY
    id
'''

# Current employees, excluding student-employees
CURRENT_EMPLOYEES = '''
SELECT
    job_rec.id, trim(id_rec.firstname) as firstname,
    trim(id_rec.lastname) as lastname, trim(cvid_rec.ldap_name) as ldap_name
FROM
    job_rec INNER JOIN  id_rec      ON  job_rec.id  =   id_rec.id
            LEFT JOIN   cvid_rec    ON  job_rec.id  =   cvid_rec.cx_id
WHERE
    job_rec.hrstat
IN
    ("AD","ADPT","FT","HR","HRPT","PT","STD","TLE","PATH","PTGP")
AND
    job_rec.hrdept                  NOT IN  ("PEND")
AND
    NVL(job_rec.end_date, TODAY)    >=      TODAY
AND
    cvid_rec.ldap_name              IS      NULL
GROUP BY
    job_rec.id, cvid_rec.ldap_name, id_rec.firstname, id_rec.lastname
'''
