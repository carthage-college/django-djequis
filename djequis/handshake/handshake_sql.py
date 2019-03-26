HANDSHAKE_QUERY = '''
SELECT Distinct
    TRIM(NVL(EML.line1,'')) AS email_address, 
    TO_CHAR(PER.id) AS username, 
    TRIM(CV.ldap_name) AS auth_identifier, 
    '' AS card_id,  --Prox ID?  but not sure
    TRIM(IR.firstname) AS first_name, 
    TRIM(IR.lastname) AS last_name, 
    TRIM(IR.middlename) AS middle_name, 
    TRIM(ADM.pref_name) AS preferred_name,
    CASE 
        WHEN CL.CL = 'FF' OR CL.CL = 'FR' THEN 'Freshman' 
        WHEN (CL.CL = 'SO') THEN 'Sophomore' 
        WHEN (CL.CL = 'JR') THEN 'Junior' 
        WHEN (CL.CL = 'SR') THEN 'Senior' 
        ELSE '' 
        END AS school_year_name, 
    CASE 
        WHEN DEG.deg in ('BS','BA') THEN 'Bachelors' 
        WHEN (DEG.deg = 'CERT') THEN 'Certificate' 
        WHEN DEG.deg in ('MBDI', 'MBA', 'MSW', 'MS', 'MM', 'MED') THEN 'Masters' 
        WHEN (DEG.deg = 'NONE') THEN 'Non-Degree Seeking' 
    ELSE DEG.txt 
        END AS education_level_name,
    SAR.cum_gpa AS cumulative_gpa,
    '' AS department_gpa,
    TRIM(MAJ1.txt) as primary_major_name,
    TRIM(MAJ1.txt) || CASE WHEN NVL(PER.major2,'') = '' THEN '' ELSE ';' 
        || TRIM(MAJ2.txt) END || CASE WHEN NVL(PER.major3,'') = '' THEN '' ELSE ';' 
        || TRIM(MAJ3.txt) 
        END AS major_names,
    TRIM(NVL(MIN1.txt,'')) || CASE WHEN NVL(PER.minor2,'') = '' THEN '' ELSE ';' 
        || TRIM(MIN2.txt) END || CASE WHEN NVL(PER.minor3,'') = '' THEN '' ELSE ';' 
        || TRIM(MIN3.txt) 
        END AS minor_names,
    'Carthage College' AS college_name, 
    PER.adm_date AS start_date, 
    PER.lv_date AS end_date,
    '' as currently_attending,
    '' AS campus_name,
    '' AS opt_cpt_eligible,  
    '' AS ethnicity,
    CASE TRIM(PRO.sex) WHEN 'M' THEN 'Male' WHEN 'F' THEN 'Female' ELSE PRO.sex 
        END AS gender, 
    '' as disabled,  
    CASE WHEN AID.id IS NULL THEN 'FALSE' ELSE 'TRUE' 
        END AS work_study_eligible, 
    '' as system_label_names,
    REPLACE(TRIM(NVL(CELL.line1,'')), '-', '') AS mobile_number,   
    TRIM(NVL(ADV.line1,'')) AS assigned_to_email_address,
    CASE WHEN ATH.id IS NULL THEN 'FALSE' ELSE 'TRUE' 
        END AS athlete, 
    CASE TRIM(PRO.vet) WHEN 'N' THEN 'FALSE' WHEN 'Y' THEN 'TRUE' ELSE '' 
        END AS veteran, 
    TRIM(IR.city) AS hometown_location_attributes,
    '' AS eu_gdpr_subject   
FROM
    prog_enr_rec	PER	INNER JOIN	id_rec		IR	ON	PER.id			=	IR.id
        LEFT JOIN		aa_rec		EML	ON	PER.id			=	EML.id
                AND	EML.aa			=	'EML1'
                AND	TODAY		BETWEEN	EML.beg_date AND NVL(EML.end_date, TODAY)
        INNER JOIN	cvid_rec		CV	ON	PER.id			=	CV.cx_id
        INNER JOIN	cl_table		CL	ON	PER.cl			=	CL.cl
        LEFT JOIN		stu_acad_rec	SAR	ON	PER.id			=	SAR.id
                AND	TRIM(SAR.sess) || SAR.yr	IN	(SELECT TRIM(sess) || yr FROM cursessyr_vw)
        LEFT JOIN		major_table	MAJ1	ON	PER.major1		=	MAJ1.major
        LEFT JOIN		major_table	MAJ2	ON	PER.major2		=	MAJ2.major
        LEFT JOIN		major_table	MAJ3	ON	PER.major3		=	MAJ3.major
        LEFT JOIN		deg_table		DEG	ON	PER.deg			=	DEG.deg
        INNER JOIN	adm_rec		ADM	ON	PER.id			=	ADM.id
                AND ADM.prog = PER.prog
                AND	ADM.primary_app	=	'Y'
        INNER JOIN	profile_rec	PRO	ON	PER.id			=	PRO.id
        LEFT JOIN		minor_table	MIN1	ON	PER.minor1		=	MIN1.minor
        LEFT JOIN		minor_table	MIN2	ON	PER.minor2		=	MIN2.minor
        LEFT JOIN		minor_table	MIN3	ON	PER.minor3		=	MIN3.minor
        LEFT JOIN		aa_rec		ADV	ON	PER.adv_id		=	ADV.id
                AND	ADV.aa			=	'EML1'
                AND	TODAY		BETWEEN	ADV.beg_date AND NVL(ADV.end_date, TODAY)
        LEFT JOIN		aa_rec		CELL	ON	PER.id			=	CELL.id
                AND	CELL.aa			=	'CELL'
                AND	TODAY		BETWEEN	CELL.beg_date AND NVL(CELL.end_date, TODAY)
        LEFT JOIN		(SELECT id
                        FROM aid_rec
                        WHERE aid	=	'FWSY'
                        AND stat	in	('A','I')
                        AND TRIM(sess) || yr	IN	(SELECT TRIM(sess) || yr FROM cursessyr_vw)
                        GROUP BY 										id
                    )			AID	ON	PER.id			=	AID.id
        LEFT JOIN		(SELECT id
                        FROM involve_rec
                        WHERE invl		IN	
                          (SELECT invl FROM invl_table WHERE sanc_sport = 'Y')
                        AND beg_date	>=	CASE WHEN TODAY < '06/01/'||to_char(YEAR(TODAY))	
                                            THEN '06/01/'||to_char(YEAR(TODAY)-1)
                                            ELSE '06/01/'||to_char(YEAR(TODAY))
                                            END
                        GROUP BY id
                    )			ATH	ON	PER.id			=	ATH.id

        LEFT JOIN       (
                        SELECT id, gpa, mflag
                        FROM degaudgpa_rec
                        WHERE mflag = 'MAJOR1' AND gpa > 0
                        ) DGR
                        ON 	DGR.id = PER.ID 
WHERE
    PER.acst	IN	("GOOD","LOC","PROB","PROC","PROR","READ","RP","SAB","SHAC","SHOC")
        AND PER.prog in ('UNDG')
        AND PER.subprog in ('TRAD')
        AND	NVL(PER.lv_date, TODAY)	>=	TODAY
        AND EML.line1 is not null
LIMIT  10
    '''
