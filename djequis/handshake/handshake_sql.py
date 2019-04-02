from sqlalchemy import text

HANDSHAKE_QUERY = '''
SELECT Distinct 
	TRIM(NVL(EML.line1,'')) AS email_address, 
	TO_CHAR(PER.id) AS username, 
	TRIM(CV.ldap_name) AS auth_identifier, 
	'' AS card_id,  
	TRIM(IR.firstname) AS first_name, 
	TRIM(IR.lastname) AS last_name, 
	TRIM(IR.middlename) AS middle_name, 
	TRIM(ADM.pref_name) AS preferred_name,
 	CASE 
		WHEN (CL.CL in ('FR', 'FN', 'FF')) THEN 'Freshman'   
	   	WHEN (CL.CL = 'SO') THEN 'Sophomore' 
	   	WHEN (CL.CL = 'JR') THEN 'Junior' 
	   	WHEN (CL.CL = 'SR') THEN 'Senior' 
	   	WHEN (CL.CL in ('GR', 'AT')) THEN 'Masters' 
	   	WHEN (CL.CL IN ('ND', 'SP')) THEN ''  
	   	WHEN (PER.acst = 'GRAD') AND (PER.lv_date IS NOT NULL OR PER.to_alum_date IS NOT NULL) THEN 'Alumni'  
		ELSE '' 
		END AS school_year_name, 
	CASE 
		WHEN (PER.deg in ('BS','BA')) THEN 'Bachelors' 
	   	WHEN (PER.deg = 'CERT') THEN 'Certificate' 
		WHEN (PER.deg in ('MBDI', 'MBA', 'MSW', 'MS', 'MM', 'MED')) THEN 'Masters' 
	   	WHEN (PER.deg = 'NONE') OR (CL.CL = 'ND') THEN 'Non-Degree Seeking' 
	ELSE ''   
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
	'' AS college_name, 
	PER.adm_date AS start_date, 
	PER.lv_date AS end_date,
	'' as currently_attending,
	'' AS campus_name,
	'' AS opt_cpt_eligible,  
	'' AS ethnicity,
	'' as gender,
	CASE WHEN PER.acst in ('WD', "WDU", 'WX') THEN 'TRUE' ELSE 'FALSE' 
		END as disabled,     
	CASE WHEN AID.id IS NULL THEN 'FALSE' ELSE 'TRUE' 
		END AS work_study_eligible, 
	"" as system_label_names, 
	CASE WHEN len(REPLACE(TRIM(NVL(CELL.phone,'')), '-', '')) = 10 
		THEN REPLACE(TRIM(NVL(CELL.phone,'')), '-', '') 
		ELSE 
			CASE WHEN len(REPLACE(TRIM(NVL(CELL.line1,'')), '-', '')) = 10
			THEN REPLACE(TRIM(NVL(CELL.line1,'')), '-', '')
			ELSE ''
			END
		END AS mobile_number,
	TRIM(NVL(ADV.line1,'')) AS assigned_to_email_address,
	'' AS athlete,
	CASE TRIM(PRO.vet) WHEN 'N' THEN 'FALSE' WHEN 'Y' THEN 'TRUE' ELSE '' 
		END AS veteran, 
	TRIM(IR.city)||', '||TRIM(ST.txt)||', '||ir.ctry 
		AS hometown_location_attributes, 
	'FALSE' AS eu_gdpr_subject   
FROM
		(
			SELECT DISTINCT id, prog, acst, subprog, deg,  site, cl, adm_yr,
			 adm_date, enr_date, acad_date, major1, major2, major3, adv_id,
			conc1, conc2, conc3, minor1, minor2, minor3, deg_grant_date, 
			vet_ben, lv_date, to_alum, to_alum_date, cohort_yr, honors, tle, 
			nurs_prog, nurs_prog_date, unmet_need 
			FROM prog_enr_rec 
			WHERE PROG = 'GRAD' 
			AND ACST IN ('GOOD')
			and (lv_date IS NULL OR lv_date > ADD_MONTHS(TODAY, -1))
			and deg_grant_date is null
			UNION
			SELECT DISTINCT id, prog, acst, subprog, deg,  site, cl, adm_yr, 
			adm_date, enr_date, acad_date, major1, major2, major3, adv_id,
			conc1, conc2, conc3, minor1, minor2, minor3, deg_grant_date, 
			vet_ben, lv_date, to_alum, to_alum_date, cohort_yr, honors, 
			tle, nurs_prog, nurs_prog_date, unmet_need 
			FROM prog_enr_rec 
			WHERE prog NOT IN ('GRAD','PARA') AND (lv_date IS NULL 
			OR lv_date > TODAY-3)
			AND acst IN	("GOOD","LOC","PROB","PROC","PROR","READ","RP",
			"SAB","SHAC","SHOC")
			AND subprog not IN ('KUSD', 'UWPK', 'YOP')
			AND CL != 'UP'
			AND ID NOT IN (Select DISTINCT id from prog_enr_rec where CL in 
			('FF','FN') AND MONTH(TODAY) < 8 AND MONTH(TODAY) > 5) 
			AND ID NOT IN (Select DISTINCT id from prog_enr_rec 
			where PROG = 'GRAD' and acst= 'GOOD')   
						 ) PER					 	 
					INNER JOIN	id_rec		IR	ON	PER.id			=	IR.id
					LEFT JOIN (SELECT id, aa, line1 
 						FROM aa_rec 
 						WHERE aa = 'EML1' AND	TODAY BETWEEN beg_date 
 						AND NVL(end_date, TODAY) 
						) EML ON EML.id = PER.id
					INNER JOIN	cvid_rec		CV	ON	PER.id	=	CV.cx_id
					LEFT JOIN st_table ST ON ST.st = IR.st  
					LEFT JOIN		(
							SELECT id.id, 
							replace(
							replace(
							replace(
							replace(
							replace(
                			replace(      
		                	multiset(      
							SELECT DISTINCT trim(a) from 
								(SELECT invl_table.txt a 
									 FROM involve_rec 
						 			 	JOIN invl_table 
										ON invl_table.invl=involve_rec.invl 
										WHERE id=id.id 
										AND 
										invl_table.sanc_sport = 'Y' 
										ORDER BY invl_table.txt)
									)::lvarchar,'MULTISET{')
									, '}')
									, 'ROW')
									, "')","")
									, "'(","")
									, ',',';')
								  DESCR
								FROM id_rec id
							) SPORT ON SPORT.id = PER.id
					INNER JOIN	cl_table CL	ON	PER.cl = CL.cl
					LEFT JOIN major_table MAJ1	ON	PER.major1 = MAJ1.major
					LEFT JOIN major_table MAJ2	ON	PER.major2 = MAJ2.major
					LEFT JOIN major_table MAJ3	ON	PER.major3 = MAJ3.major
					LEFT JOIN deg_table	DEG	ON	PER.deg	= DEG.deg
					INNER JOIN adm_rec	ADM	ON	PER.id		=	ADM.id
						AND ADM.prog = PER.prog
						AND	ADM.primary_app	=	'Y'
					INNER JOIN profile_rec	PRO	ON	PER.id	=	PRO.id
					LEFT JOIN minor_table	MIN1 ON	PER.minor1 =	MIN1.minor
					LEFT JOIN minor_table	MIN2 ON	PER.minor2 =	MIN2.minor
					LEFT JOIN minor_table	MIN3 ON	PER.minor3 =	MIN3.minor
				 	LEFT JOIN
				 		(SELECT id, aa, line1
 						FROM aa_rec
 						WHERE aa = 'EML1' AND	TODAY BETWEEN beg_date
 						AND NVL(end_date, TODAY)
						) ADV on ADV.id = PER.adv_id
					LEFT JOIN
						(SELECT a.id ID, a.aa aa, a.line1 line1, a.phone phone,
						 a.beg_date beg_date
						FROM aa_rec a
						INNER JOIN
							(
						    SELECT id, MAX(beg_date) beg_date
							    FROM aa_rec
							    WHERE aa = 'CELL'
							    GROUP BY id
								) b
							ON a.id = b.id AND a.beg_date = b.beg_date
							AND a.aa = 'CELL'
						) CELL
						ON CELL.ID = PER.ID
					LEFT JOIN		(
							SELECT id
									FROM aid_rec
									WHERE aid	=	'FWSY'
									AND stat	in	('A','I')
									AND TRIM(sess) || yr	IN
									(SELECT TRIM(sess) || yr FROM cursessyr_vw)
									GROUP BY 		id
								)		AID	ON	PER.id			=	AID.id
					LEFT JOIN
						(SELECT id, gpa, mflag
	    					FROM degaudgpa_rec
    						WHERE mflag = 'MAJOR1' AND gpa > 0
    						) DGR
						ON 	DGR.id = PER.ID
				 	LEFT JOIN
						(SELECT distinct sr.prog, sr.id, replace(sr.subprog,'"', ''),
						sr.cum_gpa, sr.yr, sr.subprog
							FROM stu_acad_rec sr, cursessyr_vw cv
			 				WHERE sr.sess = cv.sess
			 				AND sr.prog = cv.prog
			 				AND sr.yr = cv.yr) SAR
  						ON SAR.id = PER.id
  							AND SAR.prog = PER.prog
WHERE
	EML.line1 IS NOT NULL
		LIMIT 10
'''
