--Current students
    SELECT
        TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
        subID.lastname, subID.firstname, subID.id, '' AS facultyStatus, '' AS staffStatus, 'A' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
        'Active Student' AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
    FROM
        adm_rec INNER JOIN  (
                                SELECT
                                    id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                                FROM
                                    id_rec
                            )   subID       ON  adm_rec.id              =   subID.id
                INNER JOIN  acad_cal_rec    ON  adm_rec.plan_enr_sess   =   acad_cal_rec.sess
                                            AND adm_rec.plan_enr_yr     =   acad_cal_rec.yr
                                            AND acad_cal_rec.subsess    =   ' '
                LEFT JOIN   stu_acad_rec    ON  adm_rec.plan_enr_yr     =   stu_acad_rec.yr
                                            AND adm_rec.plan_enr_sess   =   stu_acad_rec.sess
                                            AND adm_rec.id              =   stu_acad_rec.id
                                            AND stu_acad_rec.reg_stat   IN  ('C','R')
                LEFT JOIN   cvid_rec        ON  adm_rec.id              =   cvid_rec.cx_id
                LEFT JOIN   (
                                SELECT
                                    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                    COUNT(*) AS total
                                FROM
                                    cvid_rec
                                WHERE
                                    TRIM(NVL(ldap_name, ''))    <>  ''
                                GROUP BY
                                    name_only
                            )   subCVID     ON  subID.username  =   subCVID.name_only
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
        TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
        subID.lastname, subID.firstname, subID.id, '' AS facultyStatus, '' AS staffStatus, 'A' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
        'Active Student' AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
    FROM
        adm_rec INNER JOIN  (
                                SELECT
                                    id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                                FROM
                                    id_rec
                            )   subID       ON  adm_rec.id              =   subID.id
                INNER JOIN  acad_cal_rec    ON  adm_rec.plan_enr_yr     =   acad_cal_rec.yr
                                            AND adm_rec.plan_enr_sess   =   acad_cal_rec.sess
                                            AND acad_cal_rec.subsess    =   ' '
                LEFT JOIN   cvid_rec        ON  adm_rec.id              =   cvid_rec.cx_id
                LEFT JOIN   (
                                SELECT
                                    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                    COUNT(*) AS total
                                FROM
                                    cvid_rec
                                WHERE
                                    TRIM(NVL(ldap_name, ''))    <>  ''
                                GROUP BY
                                    name_only
                            )   subCVID     ON  subID.username  =   subCVID.name_only
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
        TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
        subID.lastname, subID.firstname, subID.id, '' AS facultyStatus, '' AS staffStatus, 'A' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
        'Active Student' AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
    FROM
        stu_acad_rec    INNER JOIN  acad_cal_rec    ON  stu_acad_rec.sess   =   acad_cal_rec.sess
                                                    AND stu_acad_rec.yr     =   acad_cal_rec.yr
                        INNER JOIN  (
                                        SELECT
                                            id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                                        FROM
                                            id_rec
                                    )   subID       ON  stu_acad_rec.id     =   subID.id
                        LEFT JOIN   cvid_rec        ON  stu_acad_rec.id     =   cvid_rec.cx_id
                        LEFT JOIN   (
                                        SELECT
                                            LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                            COUNT(*) AS total
                                        FROM
                                            cvid_rec
                                        WHERE
                                            TRIM(NVL(ldap_name, ''))    <>  ''
                                        GROUP BY
                                            name_only
                                    )   subCVID     ON  subID.username  =   subCVID.name_only
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
        TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
        subID.lastname, subID.firstname, subID.id, '' AS facultyStatus, '' AS staffStatus, 'A' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
        'Active Student' AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
    FROM
        prog_enr_rec    INNER JOIN  (
                                        SELECT
                                            id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                                        FROM
                                            id_rec
                                    )   subID       ON  prog_enr_rec.id         =   subID.id
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
                        LEFT JOIN   (
                                        SELECT
                                            LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                            COUNT(*) AS total
                                        FROM
                                            cvid_rec
                                        WHERE
                                            TRIM(NVL(ldap_name, ''))    <>  ''
                                        GROUP BY
                                            name_only
                                    )   subCVID     ON  subID.username  =   subCVID.name_only
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
        TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
        subID.lastname, subID.firstname, subID.id, '' AS facultyStatus, '' AS staffStatus, 'A' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
        'Active Student' AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
    FROM
        regclr_rec  INNER JOIN  acad_cal_rec    ON  regclr_rec.sess         =   acad_cal_rec.sess
                                                AND regclr_rec.yr           =   acad_cal_rec.yr
                                                AND acad_cal_rec.subsess    =   ' '
                    INNER JOIN  (
                                    SELECT
                                        id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                                    FROM
                                        id_rec
                                )   subID       ON  regclr_rec.id           =   subID.id
                    LEFT JOIN   cvid_rec        ON  regclr_rec.id           =   cvid_rec.cx_id
                    LEFT JOIN   (
                                    SELECT
                                        LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                        COUNT(*) AS total
                                    FROM
                                        cvid_rec
                                    WHERE
                                        TRIM(NVL(ldap_name, ''))    <>  ''
                                    GROUP BY
                                        name_only
                                )   subCVID     ON  subID.username  =   subCVID.name_only
    WHERE
        acad_cal_rec.beg_date   <= TODAY + (SELECT pregrace FROM provsnrule_rec WHERE provsystm = 'JenzUpld' AND subsys = 'STU' AND ruleid = 'ActvDir')
    AND
        TODAY                   <=  NVL(acad_cal_rec.end_date, TODAY)
    AND
        cvid_rec.ldap_name      IS  NULL
UNION
-- Current employees, excluding student-employees
SELECT
    --Look for (in order):
    --  *Existing CVID ldap name - does the user already have a username?
    --  *Other users with same first initial-last name combination - calculate how many users would share the username and append the next number in the sequence
    --  *Username does not exist in any format yet so we create the original (first initial-last name)
    TRIM(NVL(cvid_rec.ldap_name, NVL(subCVID.name_only || subCVID.total, subID.username))) AS loginID,
    subID.lastname, subID.firstname, subID.id,
    CASE WHEN TRIM(job_rec.hrstat) IN ('FT','PT','PTGP') THEN 'A' ELSE '' END AS facultyStatus,
    CASE WHEN TRIM(job_rec.hrstat) IN ('AD','ADPT','HR','HRPT','STD','TLE','PATH') THEN 'A' ELSE '' END AS staffStatus, '' AS studentStatus, '' AS retireStatus, '' AS dob, '' AS zip,
    CASE
        WHEN    TRIM(job_rec.hrstat)    IN  ('FT')                                          THEN    'Faculty'
        WHEN    TRIM(job_rec.hrstat)    IN  ('PT','PTGP')                                   THEN    'Adjunct Faculty'
        WHEN    TRIM(job_rec.hrstat)    IN  ('AD','ADPT','HR','HRPT','STD','TLE','PATH')    THEN    'Staff'
                                                                                            ELSE    ''
    END AS acctTypes, '' AS proxID, '' AS phoneExt, '' AS depts
FROM
    job_rec INNER JOIN  (
                            SELECT
                                id, TRIM(firstname) AS firstname, TRIM(lastname) AS lastname, LOWER(firstname[1,1]) || LOWER(TRIM(lastname)) AS username
                            FROM
                                id_rec
                        )   subID   ON  job_rec.id  =   subID.id
            LEFT JOIN   cvid_rec    ON  job_rec.id  =   cvid_rec.cx_id
            LEFT JOIN   (
                            SELECT
                                LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(ldap_name),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9',''),'0','')) AS name_only,
                                COUNT(*) AS total
                            FROM
                                cvid_rec
                            WHERE
                                TRIM(NVL(ldap_name, ''))    <>  ''
                            GROUP BY
                                name_only
                        )   subCVID ON  subID.username = subCVID.name_only
WHERE
    --Administration, Part-time Admin, FT Faculty, Hourly Employee, Part-time Hourly, Part-time Fac Day, Student Worker, TLE, Part-time Athletics, Part-time Fac GPS
    job_rec.hrstat                  IN      ("AD","ADPT","FT","HR","HRPT","PT","STD","TLE","PATH","PTGP")
AND
    job_rec.hrdept                  NOT IN  ("PEND")
AND
    NVL(job_rec.end_date, TODAY)    >=      TODAY
AND
    cvid_rec.ldap_name              IS      NULL
-- Remove duplicates
GROUP BY
    loginID, subID.id, cvid_rec.ldap_name, subID.firstname, subID.lastname, facultyStatus, staffStatus, acctTypes
ORDER BY
    id;

--Create the Carthage email record for the user.
INSERT INTO
    aa_rec (id, aa, beg_date, peren, line1, ofc_add_by)
VALUES
    ([id from query], 'EML1', TODAY, 'N', '[ldap_name from query]@carthage.edu', 'INFS');

--Create the cvid record for the user
--(this prevents the user from being picked up by the "add new" process again.
INSERT INTO
    cvid_rec (old_id, old_id_num, cx_id, cx_id_char, ldap_name)
VALUES (
    'SinceCvrsn', [id from query], [id from query], '[id from query]',
    '[ldap_name from query]'
);
