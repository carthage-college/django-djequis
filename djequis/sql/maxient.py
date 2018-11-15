DEMOGRAPHIC_DATA = '''
    SELECT DISTINCT DIR.id AS Carthage_ID, TRIM(REPLACE(DIR.email, '@carthage.edu', '')) AS Username,
    DIR.lastname AS Last_Name, DIR.firstname AS First_Name, DIR.middlename AS Middle_Name,
    TO_CHAR(PROF.birth_date, '%Y-%m-%d') AS Date_of_Birth,
    CASE TRIM(PROF.sex)
        WHEN    'M' THEN    'Male'
        WHEN    'F' THEN    'Female'
                    ELSE    'Other: ' || TRIM(PROF.sex)
    END	AS  Gender, TRIM(RACE.txt) AS Ethnicity,
    CASE NVL(HSG.bldg,'')
        WHEN '' THEN
                    CASE NVL(HSGLAST.bldg,'')
                        WHEN ''      THEN 'N/A'
                        WHEN 'CMTR'  THEN 'Off Campus'
                        WHEN 'OFF'   THEN 'Off Campus'
                                     ELSE TRIM(NVL(BLDGLST.txt,''))
                    END
        WHEN 'CMTR'  THEN 'Off Campus'
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
    END AS Room_Number,
    --  LOCAL MAILING ADDRESS
    CASE
        WHEN CAMP.aa_no IS NOT NULL THEN TRIM(TRIM(NVL(CAMP.line1,'')) || ' ' || TRIM(NVL(CAMP.line2,'')) || ' ' || TRIM(NVL(CAMP.line3, '')))
                                    ELSE ''
    END AS Local_Mailing_Address,
    CASE
        WHEN CAMP.aa_no IS NOT NULL THEN TRIM(NVL(CAMP.city,''))
                                    ELSE ''
    END AS Local_City,
    CASE
        WHEN CAMP.aa_no IS NOT NULL THEN TRIM(NVL(CAMP.st,''))
                                    ELSE ''
    END AS Local_State,
    CASE
        WHEN CAMP.aa_no IS NOT NULL THEN TRIM(NVL(CAMP.zip,''))
                                    ELSE ''
    END AS Local_Zip,
    CASE
        WHEN    CAMP.aa_no  IS  NOT NULL THEN TRIM(NVL(CAMP.phone,''))
                                         ELSE ''
    END AS Local_Phone,
    TRIM(NVL(CELL.phone,'')) AS Cell_Phone,
    --  PERMANENT ADDRESS
    CASE
        WHEN PERM.aa_no IS NOT NULL THEN TRIM(TRIM(NVL(PERM.line1,'')) || ' ' || TRIM(NVL(PERM.line2,'')) || ' ' || TRIM(NVL(PERM.line3,'')))
                                    ELSE TRIM(TRIM(DIR.addr_line1) || ' ' || TRIM(DIR.addr_line2))
    END AS Permanent_Address,
    CASE
        WHEN PERM.aa_no IS NOT NULL THEN TRIM(NVL(PERM.city,''))
                                    ELSE TRIM(DIR.city)
    END AS Permanent_City,
    CASE
        WHEN PERM.aa_no IS NOT NULL THEN TRIM(NVL(PERM.st,''))
                                    ELSE TRIM(DIR.st)
    END AS Permanent_State,
    CASE
        WHEN PERM.aa_no IS NOT NULL THEN TRIM(NVL(PERM.zip,''))
                                    ELSE TRIM(DIR.zip)
    END AS Permanent_Zip,
    CASE
        WHEN PERM.aa_no IS NOT NULL THEN CASE TRIM(NVL(PERM.ctry,'')) WHEN 'US' THEN '' WHEN 'USA' THEN '' ELSE TRIM(NVL(PERM.ctry,'')) END
                                    ELSE CASE TRIM(DIR.ctry) WHEN 'US' THEN '' WHEN 'USA' THEN '' ELSE TRIM(NVL(DIR.ctry,'')) END
    END AS Permanent_Country, '' AS Permanent_Phone,
    --  EMERGENCY CONTACT INFORMATION
    CASE
        WHEN LEN(TRIM(NVL(ICE.line1,''))) > 0 THEN TRIM(
                                                        TRIM(NVL(ICE.line1,'')) ||
                                                        CASE WHEN LEN(TRIM(NVL(ICE.line2,''))) = 0 THEN '' ELSE '; ' || TRIM(NVL(ICE.line2,'')) END ||
                                                        CASE WHEN LEN(TRIM(NVL(ICE.line3,''))) = 0 THEN '' ELSE '; ' || TRIM(NVL(ICE.line3,'')) END
                                                        ) || '; Phone: ' || TRIM(NVL(ICE.phone,'N/A'))
                                                    ELSE ''
    END AS Emergency_Contact, TRIM(DIR.email) AS Email_Address, TRIM(NVL(CL.txt,'')) AS Classification,
    TRIM(
        TRIM(NVL(MAJ1.txt,'')) ||
        CASE
            WHEN TRIM(NVL(MAJ2.major,'')) <> '' THEN ', ' || TRIM(NVL(MAJ2.txt,''))
                                                ELSE ''
        END ||
        CASE
            WHEN TRIM(NVL(MAJ3.major,'')) <> '' THEN ', ' || TRIM(NVL(MAJ3.txt,''))
                                                ELSE ''
        END
        ) AS Academic_Major, TRIM(TRIM(NVL(ADV.firstname,'')) || ' ' || TRIM(NVL(ADV.lastname,''))) AS Academic_Advisor, TO_CHAR(GPA.gpa,'&.***') AS GPA_Recent, TO_CHAR(SSR.cum_gpa,'&.***') AS GPA_Cumulative,
    --  ATHLETIC INFORMATION
    CASE
        WHEN NVL(ATH.sport_name,'') <> '' AND NVL(pastAth.sport_name,'') =  '' THEN ATH.sport_name
        WHEN NVL(ATH.sport_name,'') <> '' AND NVL(pastAth.sport_name,'') <> '' THEN ATH.sport_name || ', ' || pastAth.sport_name
        WHEN NVL(ATH.sport_name,'') =  '' AND NVL(pastAth.sport_name,'') <> '' THEN pastAth.sport_name
                                                                               ELSE 'Not Athlete'
    END AS Athlete,
    NVL(GRK.greek_name,'Not Greek') AS Greek, 'N/A' AS Honors, 'N/A' AS ROTC, TO_CHAR(TODAY, '%Y-%m-%d') AS Last_Update
FROM
    directory_vw DIR
        INNER JOIN profile_rec PROF ON DIR.id = PROF.id
        LEFT JOIN race_table RACE ON PROF.ethnic_code = RACE.race
        LEFT JOIN stu_serv_rec HSG ON DIR.id =   HSG.id
                                    AND HSG.yr = YEAR(TODAY)
                                    AND HSG.sess = CASE
                                                    WHEN MONTH(TODAY) = 1 THEN 'RB'
                                                    WHEN MONTH(TODAY) <= 6 THEN 'RC'
                                                                            ELSE 'RA'
                                                    END
        LEFT JOIN bldg_table BLDG ON HSG.bldg = BLDG.bldg
        LEFT JOIN stu_serv_rec HSGLAST ON DIR.id = HSGLAST.id
                                        AND HSGLAST.yr = CASE
                                                            WHEN MONTH(TODAY) = 1 THEN YEAR(TODAY) - 1
                                                                                  ELSE YEAR(TODAY) END
                                        AND HSGLAST.sess = CASE
                                                                WHEN MONTH(TODAY) = 1 THEN 'RA'
                                                                WHEN MONTH(TODAY) <= 3 THEN 'RB'
                                                            END
        LEFT JOIN bldg_table BLDGLST ON HSGLAST.bldg = BLDGLST.bldg
        LEFT JOIN aa_rec CELL ON DIR.id = CELL.id
            AND CELL.aa = 'CELL'
            AND TODAY BETWEEN CELL.beg_date
            AND NVL(CELL.end_date, TODAY)
        LEFT JOIN aa_rec PERM ON DIR.id = PERM.id
            AND PERM.aa = 'PERM'
            AND TODAY BETWEEN PERM.beg_date
            AND NVL(PERM.end_date, TODAY)
        LEFT JOIN aa_rec CAMP ON DIR.id = CAMP.id
            AND CAMP.aa = 'CAMP'
            AND TODAY BETWEEN CAMP.beg_date
            AND NVL(CAMP.end_date, TODAY)
        LEFT JOIN aa_rec ICE ON DIR.id = ICE.id
            AND ICE.aa = 'ICE'
            AND TODAY BETWEEN ICE.beg_date
            AND NVL(ICE.end_date, TODAY)
        LEFT JOIN prog_enr_rec PER ON DIR.id = PER.id
            AND PER.prog = 'UNDG'
        LEFT JOIN cl_table CL ON PER.cl = CL.cl
        LEFT JOIN stu_stat_rec SSR ON DIR.id = SSR.id
            AND SSR.prog = 'UNDG'
        LEFT JOIN id_rec ADV ON PER.adv_id = ADV.id
        LEFT JOIN (
                    SELECT
                        id, MAX(cum_att_hrs) AS max_hrs
                    FROM
                        stu_acad_rec
                    WHERE
                        earn_hrs > 0
                    GROUP BY
                        id
                  ) subGPA ON DIR.id = subGPA.id
                    LEFT JOIN stu_acad_rec GPA ON subGPA.id = GPA.id
                        AND subGPA.max_hrs = GPA.cum_att_hrs
                    LEFT JOIN major_table MAJ1 ON PER.major1 = MAJ1.major
                    LEFT JOIN major_table MAJ2 ON PER.major2 = MAJ2.major
                    LEFT JOIN major_table MAJ3 ON PER.major3 = MAJ3.major
                    LEFT JOIN (
                                SELECT
                                    involve_rec.id, TRIM(invl_table.txt) AS sport_name
                                FROM
                                    involve_rec
                                        INNER JOIN invl_table ON involve_rec.invl = invl_table.invl
                                        AND invl_table.sanc_sport = 'Y'
                                WHERE
                                    --involve_rec.yr    >=  YEAR(TODAY) - 1
                                    --TODAY BETWEEN involve_rec.beg_date AND NVL(involve_rec.end_date, TODAY)
                                    involve_rec.yr  =   YEAR(TODAY)
                                AND
                                    involve_rec.sess = CASE WHEN MONTH(TODAY) <= 6 THEN 'RC' ELSE 'RA' END
                                GROUP BY
                                    involve_rec.id, sport_name
                              )
                                ATH ON DIR.id = ATH.id
                    LEFT JOIN (
                                SELECT
                                    PAST_INV.id, TRIM(PAST_IT.txt) AS sport_name
                                FROM
                                    involve_rec PAST_INV
                                        INNER JOIN invl_table PAST_IT ON PAST_INV.invl = PAST_IT.invl
                                        AND PAST_IT.sanc_sport = 'Y'
                                WHERE
                                    PAST_INV.sess = CASE WHEN MONTH(TODAY) <= 6 THEN 'RA' ELSE 'RC' END
                                AND
                                    PAST_INV.yr = CASE WHEN MONTH(TODAY) <= 6 THEN YEAR(TODAY) - 1 ELSE YEAR(TODAY) END
                                GROUP BY
                                    PAST_INV.id, sport_name
                              )
                                pastAth ON DIR.id = pastAth.id
                    LEFT JOIN (
                                SELECT
                                    involve_rec.id, TRIM(invl_table.txt) AS greek_name
                                FROM
                                    involve_rec INNER JOIN invl_table ON involve_rec.invl = invl_table.invl
                                WHERE
                                    involve_rec.invl IN ('S025','S061','S063','S141','S190','S192','S194','S045','S092','S152','S165','S168','S277','S276','S189','S007')
                                GROUP BY
                                    involve_rec.id, greek_name
                              ) GRK ON DIR.id = GRK.id
    WHERE
        DIR.grouping IN ('Student', 'Incoming')
    AND
        DIR.class_year <> 'GR'
    ORDER BY
        DIR.lastname, DIR.firstname
'''
