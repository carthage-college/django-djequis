STUDENT_UPLOAD = '''
    SELECT UNIQUE
        TRIM(id_rec.firstname) firstname, id_rec.middlename[1,1] middleinitial,
        TRIM(id_rec.lastname) lastname, TRIM(id_rec.suffixname) suffix,
        id_rec.id ExternalID, 'United States' as Country,
        'Carthage College' as BusinessName, 'Students' as RecordType,
        ens_rec.phone as Phone1, 'United States' as PhoneCountry1,
        TRIM(email_rec.line1) as EmailAddress1, TRIM(ens_rec.line1) ||
        TRIM(ens_rec.line2) as EmailAddress2,
        CASE WHEN NVL(ens_rec.opt_out, 1)   =   1   THEN    ens_rec.phone
                                                    ELSE    ''
        END as SMS1, 'United States' as SMS1Country, 'Standing' as CustomField1,
        CASE prog_enr_rec.cl
            WHEN    'FF'    THEN    'Freshman'
            WHEN    'FN'    THEN    'Freshman'
            WHEN    'FR'    THEN    'Freshman'
            WHEN    'SO'    THEN    'Sophomore'
            WHEN    'JR'    THEN    'Junior'
            WHEN    'SR'    THEN    'Senior'
            WHEN    'GR'    THEN    'Graduate Student'
            WHEN    'UT'    THEN    'Transfer'
                            ELSE    'Bad match: ' || prog_enr_rec.cl
        END as CustomValue1, 'Dormitory' as CustomField2,
        CASE
            WHEN    UPPER(stu_serv_rec.bldg) = 'ABRD'       THEN    'Study Abroad'
            WHEN    UPPER(stu_serv_rec.bldg) = 'BW'         THEN    'Best Western'
            WHEN    UPPER(stu_serv_rec.bldg) = 'APT'        THEN    'Campus Apartments'
            WHEN    UPPER(stu_serv_rec.bldg) = 'CCHI'       THEN    'Chicago Programs'
            WHEN    UPPER(stu_serv_rec.bldg) = 'CMTR'       THEN    'Commuter'
            WHEN    UPPER(stu_serv_rec.bldg) = 'DEN'        THEN    'Denhart'
            WHEN    UPPER(stu_serv_rec.bldg) = 'JOH'        THEN    'Johnson'
            WHEN    UPPER(stu_serv_rec.bldg) = 'MADR'       THEN    'Madrigrano'
            WHEN    UPPER(stu_serv_rec.bldg[1,3]) = 'OAK'   THEN    'Oaks ' || stu_serv_rec.bldg[4,4]
            WHEN    UPPER(stu_serv_rec.bldg) = 'OFF'        THEN    'Commuter'
            WHEN    UPPER(stu_serv_rec.bldg) = 'SWE'        THEN    'Swenson'
            WHEN    UPPER(stu_serv_rec.bldg) = 'TAR'        THEN    'Tarble'
            WHEN    UPPER(stu_serv_rec.bldg) = 'TOWR'       THEN    'Tower'
            WHEN    UPPER(stu_serv_rec.bldg) = 'UN'         THEN    ''
            WHEN    UPPER(stu_serv_rec.bldg) = 'UNDE'       THEN    ''
            WHEN    UPPER(stu_serv_rec.bldg) = ''           THEN    ''
                                                            ELSE    'Bad match: ' || stu_serv_rec.bldg
        END AS CustomValue2,
        'Parking Lot' as CustomField3, --TRIM(REPLACE(lot_table.txt, 'Apts', '')) AS CustomValue3
        CASE WHEN TRIM(NVL(PLT.lot_code,'')) = 'CMTR' THEN 'CMTR' WHEN TRIM(NVL(PLT.lot_code,'')) <> '' THEN PLT.lot_code[1,3] || ' ' || PLT.lot_code[4,4] ELSE '' END AS CustomValue3
        ,'END' as END
    FROM
        prog_enr_rec    INNER JOIN  id_rec              ON  prog_enr_rec.id =   id_rec.id
                        LEFT JOIN   profile_rec         ON  id_rec.id       =   profile_rec.id
                        LEFT JOIN   aa_rec as email_rec ON  id_rec.id       =   email_rec.id
                                                        AND email_rec.aa    =   "EML1"
                        LEFT JOIN   stu_acad_rec        ON  id_rec.id       =   stu_acad_rec.id
                        LEFT JOIN   aa_rec as ens_rec   ON  id_rec.id       =   ens_rec.id
                                                        AND    ens_rec.aa      =   'ENS'
                        LEFT JOIN
                        (
                            SELECT stu_serv_rec.id, MAX(stu_serv_rec.stusv_no) stusv_no
                            FROM stu_serv_rec
                            GROUP BY stu_serv_rec.id
                        )           building            ON  id_rec.id           =   building.id
                        LEFT JOIN   stu_serv_rec        ON  building.stusv_no   =   stu_serv_rec.stusv_no
                        LEFT JOIN    cc_prkg_vehicle_rec    PRK    ON    id_rec.id    =    PRK.carthage_id
                                                            AND    TODAY    BETWEEN    PRK.reg_date AND NVL(PRK.inactive_date,TODAY)
                        LEFT JOIN    cc_prkg_assign_rec    PAR    ON    PRK.veh_no    =    PAR.veh_no
                                                            AND    TODAY    BETWEEN    PAR.assign_begin AND NVL(PAR.assign_end, TODAY)
                        LEFT JOIN    cc_prkg_lot_table    PLT    ON    PAR.lot_no    =    PLT.lot_no
                        --LEFT JOIN   prkgpermt_rec   prk ON  id_rec.id           =   prk.permt_id
                        --                                AND prk.acadyr          =   YEAR(TODAY)
                        --LEFT JOIN   lot_table           ON  prk.lotcode         =   lot_table.lotcode
    WHERE prog_enr_rec.subprog NOT IN
        ("YOP","UWPK","RSBD","SLS","PARA","MSW","KUSD","ENRM","CONF","CHWK")
    AND prog_enr_rec.lv_date IS NULL
    AND prog_enr_rec.cl IN ("FF","FN","FR","SO","JR","SR","GR","UT")
    AND prog_enr_rec.acst = "GOOD"
    AND stu_acad_rec.yr = YEAR(TODAY)
    AND stu_acad_rec.sess IN ("RA","RC","AM","GC","PC","TC")
    AND stu_acad_rec.reg_hrs > 0
    ORDER BY lastname, firstname
'''

ADULT_UPLOAD = '''
    SELECT
        TRIM(IDrec.firstname) AS firstname, IDrec.middlename[1,1] AS middleinitial,
        TRIM(IDrec.lastname) AS lastname, TRIM(IDrec.suffixname) AS suffix,
        IDrec.id ExternalID, 'United States' AS Country,
        'Carthage College' AS BusinessName, 'Adult Students' AS RecordType,
        ENSrec.phone AS Phone1, 'United States' AS PhoneCountry1,
        TRIM(EMLrec.line1) AS EmailAddress1,
        TRIM(ENSrec.line1) || TRIM(ENSrec.line2) AS EmailAddress2,
        CASE
            WHEN NVL(ENSrec.opt_out, 1) =    1 THEN ENSrec.phone
                                                ELSE    ''
        END AS SMS1, 'United States' AS SMS1Country, 'Standing' AS CustomField1,
        'Adult Student' AS CustomValue1, 'Dormitory' as CustomField2,
        'Commuter' AS CustomValue2, 'Parking Lot' AS CustomField3,
        'CMTR' AS CustomValue3,'END' AS END
    FROM
        id_rec  IDrec   INNER JOIN  stu_acad_rec SArec   ON  IDrec.id   =   SArec.id
                        INNER JOIN  acad_cal_rec    ACrec   ON  SArec.yr    =   ACrec.yr
                                                            AND SArec.sess  =   ACrec.sess
                        LEFT JOIN   aa_rec          ENSrec  ON  IDrec.id    =   ENSrec.id
                                                            AND ENSrec.aa   =   'ENS'
                                                            AND TODAY   BETWEEN ENSrec.beg_date AND NVL(ENSrec.end_date, TODAY)
                        LEFT JOIN   aa_rec          EMLrec  ON  IDrec.id    =   EMLrec.id
                                                            AND EMLrec.aa   =   'EML1'
                                                            AND TODAY   BETWEEN EMLrec.beg_date AND NVL(EMLrec.end_date, TODAY)
    WHERE
        ACrec.yr    =   YEAR(TODAY)
    AND
        ACrec.sess  IN  (SELECT sess FROM sess_table WHERE prog IN ('GRAD','PARA','PRDV')
        AND TODAY BETWEEN active_date AND NVL(inactive_date, TODAY))
    AND
        TODAY   BETWEEN ACrec.beg_date AND ACrec.end_date
    GROUP BY
        IDrec.id, IDrec.firstname, IDrec.lastname, IDrec.middlename[1,1],
        IDrec.suffixname, Phone1, EmailAddress1, EmailAddress2, SMS1
    ORDER BY
        lastname, firstname
'''

FACSTAFF_UPLOAD = '''
    SELECT UNIQUE
        TRIM(id_rec.firstname) firstname, id_rec.middlename[1,1] middleinitial,
        TRIM(id_rec.lastname) lastname, TRIM(id_rec.suffixname) suffix,
        id_rec.id::varchar(10) ExternalID, 'United States' as Country,
        'Carthage College' as BusinessName, 'Employee' as RecordType,
        CASE WHEN   NVL(ens_rec.opt_out, 1) =   1   THEN    ens_rec.phone
                                                    ELSE    ''
        END as Phone1, 'United States' as PhoneCountry1,
        CASE WHEN   school_rec.phone    =   '___-___-____'  THEN    ''
                                                            ELSE    TRIM(school_rec.phone)
        END as Phone2, 'United States' as PhoneCountry2,
        TRIM(email_rec.line1) as EmailAddress1,
        TRIM(ens_rec.line1) || TRIM(ens_rec.line2) as EmailAddress2,
        CASE WHEN   NVL(ens_rec.opt_out, 1) =   1   THEN    TRIM(ens_rec.phone)
                                                    ELSE    ''
        END as SMS1, 'United States' as SMS1Country, 'Office Building' as CustomField1,
        CASE TRIM(UPPER(school_rec.line3[1,3]))
            WHEN    'ARE'   THEN    'Tarble Center'
            WHEN    'CC'    THEN    'Clausen Center'
            WHEN    'DIN'   THEN    ''
            WHEN    'DSC'   THEN    'David Straz Center'
            WHEN    'HL'    THEN    'Hedberg Library'
            WHEN    'JAC'   THEN    'Johnson Art Center'
            WHEN    'JOH'   THEN    'Johnson Hall'
            WHEN    'LH'    THEN    'Lentz Hall'
            WHEN    'LEN'   THEN    'Lentz Hall'
            WHEN    'MAD'   THEN    'Madrigrano Hall'
            WHEN    'PEC'   THEN    'Physical Education Center'
            WHEN    'SC'    THEN    'Siebert Chapel'
            WHEN    'SIE'   THEN    'Siebert Chapel'
            WHEN    'STR'   THEN    'David Straz Center'
            WHEN    'SU'    THEN    'Student Union'
            WHEN    'TAR'   THEN    'Tarble Center'
            WHEN    'TWC'   THEN    'Todd Wehr Center'
            WHEN    ''      THEN    ''
                            ELSE    'Bad match: ' || TRIM(REPLACE(school_rec.line3,',','[comma]'))
        END as CustomValue1, 'Standing' as CustomField2,
        CASE jenzcst_rec.status_code
            WHEN    'FAC'   THEN    'Faculty'
            WHEN    'STF'   THEN    'Staff'
        END as CustomValue2, 'Full/Part Time' as CustomField3,
        CASE hrstat.hrstat
            WHEN    'FT'    THEN    'Full-Time'
            WHEN    'PT'    THEN    'Part-Time'
        END AS CustomValue3
        ,'END' as END
    FROM
        id_rec  INNER JOIN  job_rec             ON  id_rec.id       =   job_rec.id
                INNER JOIN  pos_table           ON  job_rec.tpos_no =   pos_table.tpos_no
                LEFT JOIN   aa_rec  school_rec  ON  id_rec.id       =   school_rec.id
                                                AND school_rec.aa   =   "SCHL"
                LEFT JOIN   aa_rec  email_rec   ON  id_rec.id       =   email_rec.id
                                                AND email_rec.aa    =   "EML1"
                LEFT JOIN   aa_rec  ens_rec     ON  id_rec.id       =   ens_rec.id
                                                AND ens_rec.aa      =   'ENS'
                LEFT JOIN
                (
                    SELECT  host_id, MIN(seq_no) seq_no
                    FROM    jenzcst_rec
                    WHERE   status_code IN ('FAC','STF')
                    GROUP BY    host_id
                )   filter                      ON  id_rec.id       =   filter.host_id
                LEFT JOIN   jenzcst_rec         ON  filter.host_id  =   jenzcst_rec.host_id
                                                AND filter.seq_no   =   jenzcst_rec.seq_no
                LEFT JOIN
                (
                    SELECT  id, hrstat
                    FROM    job_rec
                    WHERE   TODAY   BETWEEN beg_date    AND NVL(end_date, TODAY)
                    AND     hrstat  IN      ('FT','PT')
                    GROUP BY id, hrstat
                )   hrstat                      ON  id_rec.id       =   hrstat.id
    WHERE
        TODAY   BETWEEN job_rec.beg_date        AND NVL(job_rec.end_date, TODAY)
        AND
        TODAY   BETWEEN pos_table.active_date   AND NVL(pos_table.inactive_date, TODAY)
        AND
        job_rec.title_rank  IS  NOT NULL
    ORDER BY lastname, firstname
'''
