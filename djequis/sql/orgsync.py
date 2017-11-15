ORGSYNC_DATA = '''
    SELECT DISTINCT TRIM(REPLACE(DIR.email, '@carthage.edu', '')) AS Username,
    '' AS New_Username, DIR.email AS Email_Address, DIR.firstname AS First_Name,
    DIR.lastname AS Last_Name, LEFT(DIR.middlename, 1) AS Middle_Initial,
    TRIM(NVL(CELL.phone,'')) AS Phone_Number, TRIM(DIR.addr_line1) AS Address,
    TRIM(DIR.city) AS City, TRIM(DIR.st) AS State,
    TRIM(DIR.zip) AS Zip,
    CASE TRIM(INITCAP(NVL(CT.txt,'')))
        WHEN ''                 THEN 'NA'
        WHEN 'Australia'        THEN 'AU'
        WHEN 'Canada'           THEN 'CA'
        WHEN 'China'            THEN 'CN'
        WHEN 'Greece'           THEN 'GR'
        WHEN 'Hong Kong'        THEN 'HK'
        WHEN 'Ireland'          THEN 'IE'
        WHEN 'Japan'            THEN 'JP'
        WHEN 'Kenya'            THEN 'KE'
        WHEN 'Peoples'' Repub Of China' THEN 'NA'
        WHEN 'Serbia'           THEN 'RS'
        WHEN 'South Africa'     THEN 'ZA'
        WHEN 'United States'    THEN 'US'
                                ELSE TRIM(INITCAP(NVL(CT.txt,'')))
    END AS Country,
    TO_CHAR(PROF.birth_date, '%m-%d-%Y') AS Birthday, '' AS Id_Card_Number,
    '158512' as Portal_Number, '614847' AS Group_Number,
    CASE DIR.class_year
        WHEN    'FF'    THEN    'Freshman'
        WHEN    'FN'    THEN    'First-time Nursing Stu.'
        WHEN    'FR'    THEN    'Freshman'
        WHEN    'SO'    THEN    'Sophomore'
        WHEN    'JR'    THEN    'Junior'
        WHEN    'SR'    THEN    'Senior'
                        ELSE    DIR.class_year
    END as Classification, TRIM(PROF.sex) AS  Gender,
    TRIM(DIR.city) AS Hometown,
    TRIM(NVL(MAJ1.txt,'')) AS Major_1,
    TRIM(NVL(MAJ2.txt,'')) AS Major_2,
    TRIM(NVL(MAJ3.txt,'')) AS Major_3,
    TRIM(NVL(MIN1.txt,'')) AS Minor_1,
    TRIM(NVL(MIN2.txt,'')) AS Minor_2,
    TRIM(NVL(MIN3.txt,'')) AS Minor_3,
    DIR.id AS Student_ID, TRIM(RACE.txt) AS Ethnicity,
    PER.plan_grad_yr AS Projected_Grad_Yr,
    CASE HSG.intend_hsg
            WHEN 'R' THEN 'Resident'
            WHEN 'O' THEN 'Off Campus'
            WHEN 'C' THEN 'Commuter'
            WHEN 'I' THEN 'Intended'
                     ELSE 'N/A'
    END AS Housing_Status,
    CASE
       WHEN CTC.ctc_no IS NOT NULL THEN 'Y'
                                   ELSE 'N' 
    END AS International_Student,
    ADM.trnsfr AS Transfer,
    CASE NVL(HSG.bldg,'')
        WHEN '' THEN
            CASE NVL(HSGLAST.bldg,'')
                WHEN ''     THEN 'N/A'
                WHEN 'CMTR' THEN 'Commuter'
                WHEN 'OFF'  THEN 'Off Campus'
                            ELSE TRIM(NVL(BLDGLST.txt,''))
            END
        WHEN 'CMTR'  THEN 'Commuter'
        WHEN 'OFF'   THEN 'Off Campus'
                     ELSE TRIM(NVL(BLDG.txt,''))
    END AS Building,
    CASE
        WHEN HSG.room IS NULL THEN
            CASE
                WHEN NVL(HSGLAST.room,'') LIKE 'UN%' THEN ''
                                                     ELSE NVL(HSGLAST.room,'')
            END
        WHEN NVL(HSG.room,'') LIKE 'UN%' THEN ''
                                         ELSE NVL(HSG.room,'')
    END AS Room_Number, HSG.campus_box AS Mailbox
    FROM directory_vw DIR
    INNER JOIN profile_rec PROF ON DIR.id = PROF.id
    LEFT JOIN race_table RACE ON PROF.ethnic_code = RACE.race
    LEFT JOIN stu_serv_rec HSG ON DIR.id =   HSG.id
        AND HSG.yr = YEAR(TODAY)
        AND HSG.sess = CASE
                        WHEN MONTH(TODAY) = 1 THEN 'RB'
                        WHEN MONTH(TODAY) <= 6 THEN 'RC'
                                               ELSE 'RA'
                        END
    LEFT JOIN stu_serv_rec HSGLAST ON DIR.id = HSGLAST.id
        AND HSGLAST.yr = CASE
                         WHEN MONTH(TODAY) = 1 THEN YEAR(TODAY) - 1
                                               ELSE YEAR(TODAY) END
        AND HSGLAST.sess = CASE
                           WHEN MONTH(TODAY) = 1 THEN 'RA'
                           WHEN MONTH(TODAY) <= 3 THEN 'RB'
                           END
    LEFT JOIN bldg_table BLDGLST ON HSGLAST.bldg = BLDGLST.bldg
    LEFT JOIN bldg_table BLDG ON HSG.bldg = BLDG.bldg
    LEFT JOIN aa_rec CELL ON DIR.id = CELL.id
        AND CELL.aa = 'CELL'
        AND TODAY BETWEEN CELL.beg_date
        AND NVL(CELL.end_date, TODAY)
    LEFT JOIN aa_rec CAMP ON DIR.id = CAMP.id
        AND CAMP.aa = 'CAMP'
        AND TODAY BETWEEN CAMP.beg_date
        AND NVL(CAMP.end_date, TODAY)
    INNER JOIN prog_enr_rec PER ON DIR.id = PER.id
        AND PER.prog = 'UNDG'
    INNER JOIN id_rec IR ON DIR.id = IR.id
    INNER JOIN adm_rec ADM ON DIR.id = ADM.id
        AND ADM.primary_app = 'Y'
        AND ADM.prog = 'UNDG'
    LEFT JOIN ctry_table CT ON DIR.ctry = CT.ctry
        AND TODAY BETWEEN  CT.active_date AND NVL(CT.inactive_date, TODAY)
    LEFT JOIN major_table MAJ1 ON PER.major1 = MAJ1.major
    LEFT JOIN major_table MAJ2 ON PER.major2 = MAJ2.major
    LEFT JOIN major_table MAJ3 ON PER.major3 = MAJ3.major
    LEFT JOIN minor_table MIN1 ON PER.minor1 = MIN1.minor
    LEFT JOIN minor_table MIN2 ON PER.minor2 = MIN2.minor
    LEFT JOIN minor_table MIN3 ON PER.minor3 = MIN3.minor
    LEFT JOIN ctc_rec CTC ON DIR.id = CTC.id
        AND CTC.resrc = 'I20'
    WHERE
        DIR.grouping = 'Student'
        AND DIR.class_year IN ('FF','FN','FR','SO','JR','SR')
    ORDER BY
        DIR.lastname, DIR.firstname
'''
