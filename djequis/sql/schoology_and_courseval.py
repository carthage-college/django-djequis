# fetch courses and sections
# This query should return all courses and sections active with a start date less
# than six months from the current date.
# Based on the dates for the terms courses and sections are made active
# or inactive automatically.
COURSES = '''
    SELECT 
        TRIM(jenzccd_rec.title) Coursename, TRIM(jenzdpt_rec.descr) Department, 
        TRIM(jenzcrs_rec.course_code) CourseCode, jenzcrs_rec.hrs Credits, 
        TRIM(jenzccd_rec.title)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(st.txt)||' '||secmtg_rec.yr||' '||  case 
            when TRIM(x) = TRIM(y) then x
            else  x||' / '||y
        end  descr,
        TRIM(jenzcrs_rec.sec)||'-'||TRIM(InstrName)||' '||TRIM(st.txt)||' '||secmtg_rec.yr||' '|| case 
            when TRIM(x) = TRIM(y) then x
            else  x||' / '||y
         end SectionName,
        TRIM(jenzcrs_rec.coursekey) SecSchoolCode,
        left(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) SectionCode,
            case
            when TRIM(x) = TRIM(y) then x
            else  x||' / '||y end as SecDescr,
        --nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
        'Carthage College' School,
        TRIM(jenzcrs_rec.term_code)||' '||Instructor.subsess GradingPeriod,
        'Active' Sec_status
        , crs_rec.crs_no as eval_course_no, TRIM(jenzcrs_rec.sec) as eval_section, replace(disc_table.dept,"_","") as eval_dept, trim(Instructor.session) || " " || Instructor.yr as eval_period, Instructor.username, Instructor.fac_id, Instructor.email, MeetPattern.im as eval_coursetype,
        year(jenztrm_rec.start_date) || lpad(month(jenztrm_rec.start_date),2,'0') || lpad(day(jenztrm_rec.start_date),2,'0') as eval_start_date,
        year(jenztrm_rec.end_date) || lpad(month(jenztrm_rec.end_date),2,'0') || lpad(day(jenztrm_rec.end_date),2,'0') as eval_end_date, CrossLists.mtg_no as crosslist
    FROM jenzcrs_rec 
    JOIN crs_rec 
    	on TRIM(jenzcrs_rec.course_code) = TRIM(crs_rec.crs_no)||' ('||TRIM(crs_rec.cat)||')'
    JOIN Jenzccd_rec 
    	on Jenzccd_rec.course_code = jenzcrs_rec.course_code 
    JOIN jenztrm_rec 
    	on jenztrm_rec.term_code = jenzcrs_rec.term_code
    LEFT JOIN jenzdpt_rec 
    	on jenzdpt_rec.dept_code = jenzccd_rec.dept_code
    LEFT JOIN jenzsch_rec 
    	on jenzsch_rec.term_code = jenzcrs_rec.term_code
        and jenzsch_rec.sec = jenzcrs_rec.sec
        and jenzsch_rec.course_code = jenzcrs_rec.course_code
    JOIN secmtg_rec 
    	on secmtg_rec.crs_no = crs_rec.crs_no
        and secmtg_rec.sec_no = jenzcrs_rec.sec
        and TRIM(secmtg_rec.sess) = left(jenzcrs_rec.term_code,2) 
        and secmtg_rec.yr =  SUBSTRING(jenzcrs_rec.term_code FROM 4 FOR 4)
        and secmtg_rec.cat = crs_rec.cat
    JOIN (select a.crs_no, a.sec_no, a.cat, a.yr, a.sess, trim(sess_table.txt) as session, a.subsess, 
          c.lastname as InstrName, c.firstname, c.fullname, a.fac_id, 
          trim(cvid_rec.ldap_name) as username, trim(aa_rec.line1) as email
          from sec_rec a, id_rec c, cvid_rec, aa_rec, sess_table
          where c.id = a.fac_id
          and a.yr > year(today)-2
          and a.sess = sess_table.sess
          and cvid_rec.cx_id = a.fac_id
          and aa_rec.id = a.fac_id 
          and aa_rec.aa = "EML1" 
          and nvl(aa_rec.end_date,today) >= today
         ) Instructor 
         on Instructor.sec_no = secmtg_rec.sec_no
         and Instructor.crs_no = secmtg_rec.crs_no
         and Instructor.cat = secmtg_rec.cat
         and Instructor.yr = secmtg_rec.yr
         and Instructor.sess = secmtg_rec.sess
    JOIN sess_table st 
     	on st.sess = secmtg_rec.sess 
    LEFT JOIN (SELECT  b.crs_no, b.yr, b.sec_no, b.cat, b.sess,
                       MAX(a.mtg_no) as MaxMtgNo, 
                       MAX(TRIM(b.crs_no)||'-'||b.sec_no) as x,
                       MIN(TRIM(b.crs_no)||'-'||b.sec_no) as y,
                       a.im
               FROM  secmtg_rec b
               JOIN mtg_rec a 
                   on a.mtg_no = b.mtg_no
		           AND a.yr = b.yr
		           AND a.sess = b.sess
		       LEFT JOIN bldg_table c 
	               ON c.bldg = a.bldg
               GROUP BY b.crs_no, b.yr, b.sec_no, b.cat, b.sess, a.im 
              ) MeetPattern
        ON MeetPattern.crs_no = crs_rec.crs_no
        AND MeetPattern.yr = left(jenzcrs_rec.coursekey,4)
        AND MeetPattern.MaxMtgNo = secmtg_rec.mtg_no      
    LEFT JOIN (
		select mtg_no
		from secmtg_rec
		where yr = 2019
		and sess in ("RA","GA","AA","AB")
		group by mtg_no
		having count(crs_no) > 1
    ) CrossLists
    	ON CrossLists.mtg_no = secmtg_rec.mtg_no
    LEFT JOIN disc_table
        on jenzcrs_rec.course_code[1,3] = disc_table.disc
    WHERE jenztrm_rec.start_date <= ADD_MONTHS(today,6)
    AND jenztrm_rec.end_date >= ADD_MONTHS(today,-1)
    --AND right(trim(jenzcrs_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
    AND jenzccd_rec.title IS NOT NULL
	AND MeetPattern.im not in ("RT")
	and jenzcrs_rec.term_code[1,7] in ("RA 2019","GA 2019","AA 2019","AB 2019")

UNION

    SELECT TRIM(cr.title1)||' '||TRIM(cr.title2)||' '||TRIM(cr.title3) Coursename, 
           TRIM(dt.txt) department, TRIM(sr.crs_no)||' ('||TRIM(sr.cat)||')' coursecode, 
           TO_CHAR(sr.hrs,"*.**")  credit,
           TRIM(trim(cr.title1)||' '||TRIM(cr.title2)||' '||TRIM(cr.title3))||'-'||
           TRIM(sr.sec_no)||' '||TRIM(st.txt)||' '||sr.yr||' '||
           CASE 
               WHEN TRIM(x) = TRIM(y) THEN x 
               ELSE  x || ' / ' || y 
           END descr,
           TRIM(sr.sec_no)||'-'||TRIM(ir.lastname)||' '||TRIM(st.txt)||' '||sr.yr||' '||
           CASE 
               WHEN TRIM(x) = TRIM(y) then x 
               ELSE  x || ' / ' || y 
           END sectionname,
           sr.yr||';'||TRIM(sr.sess)||';'||TRIM(sr.crs_no)||';'||TRIM(sr.sec_no)||';'||TRIM(sr.cat)||';'||TRIM(cr.prog) sectionschoolcode,
           TRIM(sr.crs_no)||'-'||TRIM(sr.sec_no)||' '||TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) sectioncode,
           CASE 
               WHEN TRIM(x) = TRIM(y) THEN x 
               ELSE  x ||' / '|| y 
           END secdescr,
           --nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
           'Carthage College' School,
           TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) GradingPeriod, 'Cancelled' Sec_status
           , sr.crs_no as eval_course_no, TRIM(sr.sec_no) as eval_section, replace(disc_table.dept,"_","") as eval_dept, trim(st.txt) || " " || sr.yr as eval_period, trim(cvid_rec.ldap_name) as username, sr.fac_id, trim(email.line1) as email, MeetPattern.im as eval_coursetype,
           year(sr.beg_date) || lpad(month(sr.beg_date),2,'0') || lpad(day(sr.beg_date),2,'0') as eval_start_date,
           year(sr.end_date) || lpad(month(sr.end_date),2,'0') || lpad(day(sr.end_date),2,'0') as eval_end_date, CrossLists.mtg_no as crosslist
    FROM sec_rec sr
    JOIN crs_rec cr 
        on cr.crs_no = sr.crs_no
        and cr.cat = sr.cat
    JOIN id_rec ir 
        on ir.id = sr.fac_id 
    JOIN aa_rec email
        on email.id = sr.fac_id
        and email.aa = "EML1"
        and nvl(email.end_date,today) >= today
    JOIN cvid_rec  
        on cvid_rec.cx_id = sr.fac_id
    JOIN sess_table st 
        on sr.sess = st.sess
    JOIN dept_table dt 
        on dt.dept = cr.dept
    JOIN secmtg_rec mtg 
        on mtg.crs_no = sr.crs_no
        AND mtg.sec_no = sr.sec_no
        AND trim(mtg.sess) = sr.sess 
        AND mtg.yr =  sr.yr
        AND mtg.cat = sr.cat
    LEFT JOIN (select  b.crs_no, b.yr, b.sec_no, b.cat, b.sess,
               MAX(a.mtg_no) as MaxMtgNo, 
               MAX(TRIM(b.crs_no)||'-'||b.sec_no) as x,
               MIN(TRIM(b.crs_no)||'-'||b.sec_no) as y,
               a.im
               FROM  secmtg_rec b
               JOIN mtg_rec a 
                   on a.mtg_no = b.mtg_no
                   AND a.yr = b.yr
                   AND a.sess = b.sess
               LEFT JOIN bldg_table c 
                   ON c.bldg = a.bldg
               GROUP BY b.crs_no, b.yr, b.sec_no, b.cat, b.sess, a.mtg_no, a.im
              ) MeetPattern
        ON MeetPattern.crs_no = sr.crs_no
        AND MeetPattern.yr = sr.yr
        AND MeetPattern.MaxMtgNo = mtg.mtg_no 
    LEFT JOIN (
		select mtg_no
		from secmtg_rec
		where yr = 2019
		and sess in ("RA","GA","AA","AB")
		group by mtg_no
		having count(crs_no) > 1
    ) CrossLists
    	ON CrossLists.mtg_no = mtg.mtg_no
    LEFT JOIN disc_table
        on sr.crs_no[1,3] = disc_table.disc
    WHERE sr.stat = 'X'
    AND sr.end_date > TODAY
    AND sr.stat_date > TODAY-4
    AND trim(cr.prog) NOT IN ('PRDV','PARA','KUSD')
    and MeetPattern.im not in ("RT")
    and sr.yr = 2019
    and sr.sess in ("RA","GA","AA","AB")'''
# fetch users
# Users are collected in a single query to get both Students and Faculty/Staff.
# The student query portion pulls all students with an academic record
# between the start of the current fiscal year (July 1) and the end of the current fiscal year.
# The Faculty/Staff portion should get all employees with active job records
# within the last year.
# There are enrollments for individuals who are not currently staff or faculty.
# If I filter to only users who were employed in the last year,
# I find enrollment records without a matching user. 

'''
SELECT firstname, preferred_first_name, middlename, lastname, '' name_prefix,
    username, EMAIL, UniqueID, ROLE, school, schoology_id, Position, 
    '' pwd, '' gender, '' GradYr, '' additional_schools 
FROM
	(SELECT DISTINCT
	    IR.firstname, ADR.alt_name preferred_first_name,
	    IR.middlename, IR.lastname, 
	    trim(JPR.host_username) username, TRIM(JPR.e_mail) EMAIL,
	    to_number(JPR.host_id) UniqueID,
	    CASE WHEN title1.hrpay NOT IN ('VEN', 'DPW', 'BIW', 'FV2', 'SUM', 'GRD')
	        OR TLE.tle = 'Y'
	        THEN 'FAC' ELSE 'STU' END AS ROLE,
	    'Carthage College' school, JPR.host_id schoology_id,
	    CASE NVL(title1.job_title,'x') WHEN 'x' THEN '' 
			ELSE trim(title1.job_title) END||
	    CASE NVL(title2.job_title,'x') WHEN 'x' THEN '' 
	   		ELSE '; '||trim(title2.job_title) END||
	    CASE NVL(title3.job_title,'x') WHEN 'x' THEN '' 
	   		ELSE '; '||trim(title3.job_title) END
	    Position, 
	    row_number() OVER 
	    (partition BY JC.host_id
			ORDER BY
				CASE 
				WHEN status_code = 'FAC' THEN 1  
				WHEN status_code = 'AMA' THEN 2  
				WHEN status_code = 'AMO' THEN 3  
				WHEN status_code = 'GLL' THEN 4  
				WHEN status_code = 'FAA' THEN 5  
				WHEN status_code = 'ADA' THEN 6  
				WHEN status_code = 'ADV' THEN 7  
				WHEN status_code = 'GLL' THEN 8  
				WHEN status_code = 'STF' THEN 9  
				WHEN status_code = 'FW0' THEN 10  
				WHEN status_code = 'FWS' THEN 11
				WHEN status_code = 'STU' THEN 12
				ELSE 99 end
		) as row_num
	FROM jenzcst_rec JC
	    LEFT JOIN jenzprs_rec JPR ON JPR.host_id = JC.host_id
	    JOIN id_rec IR ON IR.id =  JC.host_id
		LEFT JOIN job_rec title1 ON title1.id = JC.host_id 
	       AND title1.title_rank = 1
	       AND (title1.end_date IS NULL OR title1.end_date > current) 
	       AND title1.job_title IS NOT NULL
	    LEFT JOIN job_rec title2 ON title2.id = JC.host_id 
	       AND title2.title_rank = 2
	       AND (title2.end_date is null or title2.end_date > current) 
	       AND title2.job_title IS NOT NULL
	    LEFT JOIN job_rec title3 ON title3.id = JC.host_id 
	       AND title3.title_rank = 3
	       AND (title3.end_date is null or title3.end_date > current) 
	       AND title3.job_title IS NOT NULL
	    LEFT JOIN job_rec title4 ON title4.id = JC.host_id 
	       AND title4.title_rank = 4
	       AND (title4.end_date is null or title4.end_date > current) 
	       AND title4.job_title IS NOT NULL
	    LEFT JOIN prog_enr_rec TLE ON TLE.id = JC.host_id
	       AND TLE.acst in ('GOOD', 'GRAD')
	       AND TLE.tle = 'Y'
	    LEFT JOIN addree_rec ADR ON ADR.prim_id = JC.host_id
	       AND ADR.style = 'N' 
	WHERE status_code not in ('PGR', 'ALM',  'PTR')
	       AND	JC.host_id NOT IN 
		   (
		    SELECT ID FROM role_rec
			WHERE role = 'PREFF' AND end_date IS NULL 
			AND MONTH(TODAY) IN (6,7)
	    	)  
	)
WHERE row_num = 1
ORDER BY lastname ASC, firstname ASC, role ASC;
'''
USERS = '''
    SELECT DISTINCT
       trim(id_rec.firstname) as firstname, trim(addree_rec.alt_name) as preferred_first_name,
       trim(id_rec.middlename) as middlename, trim(id_rec.lastname) as lastname, '' as name_prefix,
       trim(jenzprs_rec.host_username) as username, TRIM(jenzprs_rec.e_mail) as email,
       to_number(jenzprs_rec.host_id) as UniqueID,
       CASE WHEN title1.hrpay NOT IN ('VEN', 'DPW', 'BIW', 'FV2', 'SUM', 'GRD')
           OR TLE.tle = 'Y'
           THEN 'FAC' ELSE 'STU' END AS role,
       'Carthage College' school, jenzprs_rec.host_id schoology_id,
       CASE NVL(title1.job_title,'x') WHEN 'x' then '' ELSE trim(title1.job_title) END||
       CASE NVL(title2.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title2.job_title) END||
       CASE NVL(title3.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title3.job_title) END
       Position, '' pwd, '' gender, '' GradYr, '' additional_schools
       , fac_rec.dept as eval_dept, case when dept_table.dept is not null then "Y" else null end as eval_chair
    FROM jenzprs_rec
        LEFT JOIN jenzcst_rec
       	    ON jenzprs_rec.host_id = jenzcst_rec.host_id
            AND jenzcst_rec.status_code IN ('FAC', 'STF', 'STU', 'ADM')
        JOIN id_rec 
       	    ON id_rec.id =  jenzprs_rec.host_id
        JOIN provisioning_vw on provisioning_vw.id = jenzprs_rec.host_id
        LEFT JOIN job_rec title1 
            ON title1.id = jenzprs_rec.host_id 
            AND title1.title_rank = 1
            AND (title1.end_date IS NULL OR title1.end_date > current) 
            AND title1.job_title IS NOT NULL
        LEFT JOIN job_rec title2 
            ON title2.id = jenzprs_rec.host_id 
            AND title2.title_rank = 2
            AND (title2.end_date is null or title2.end_date > current) 
            AND title2.job_title IS NOT NULL
        LEFT JOIN job_rec title3 
            ON title3.id = jenzprs_rec.host_id 
            AND title3.title_rank = 3
            AND (title3.end_date is null or title3.end_date > current) 
            AND title3.job_title IS NOT NULL
        LEFT JOIN job_rec title4 
            ON title4.id = jenzprs_rec.host_id 
            AND title4.title_rank = 4
            AND (title4.end_date is null or title4.end_date > current) 
            AND title4.job_title IS NOT NULL
        LEFT JOIN prog_enr_rec TLE
            ON TLE.id = jenzprs_rec.host_id
    	    AND TLE.acst in ('GOOD', 'GRAD')
            AND TLE.tle = 'Y'
        LEFT JOIN addree_rec 
            ON addree_rec.prim_id = jenzprs_rec.host_id
            AND addree_rec.style = 'N'
        LEFT JOIN fac_rec 
        	ON fac_rec.id = jenzprs_rec.host_id
        	AND fac_rec.dept in (
		        select dept
				from dept_table
				where nvl(active_date,today) <= today
				and nvl(inactive_date,today) <= today
				and web_display="Y"
				and div in ("PRST","ACPR","NSSS","ARHU")
			) 
		LEFT JOIN dept_table
			on dept_table.dept = fac_rec.dept
			and dept_table.head_id = fac_rec.id
			and nvl(dept_table.inactive_date,today) >= today
    WHERE jenzprs_rec.host_id IN
          (
            SELECT to_number(host_id) as UID
            FROM jenzcrp_rec
           
            UNION ALL
           
            select cx_id as UID
            from provsndtl_rec
            where subsys = 'MSTR'
            AND action = 'Active'
            AND roles NOT IN ('Contractor')
          )
    AND jenzprs_rec.host_id NOT IN 
        (
            select ID 
	        from role_rec
	        where role = 'PREFF' and end_date is null
	        and MONTH(TODAY) IN (6,7)
        )
   GROUP BY id_rec.lastname, id_rec.firstname, preferred_first_name,
            id_rec.middlename, name_prefix, jenzprs_rec.host_username, email, UniqueID, schoology_id,
            Position, title1.job_title, TLE.tle, title1.hrpay, fac_rec.dept, dept_table.dept
   ORDER BY lastname ASC, firstname ASC, role ASC;
'''
# Fetch enrollment data. Use enrollment_vw so that Schoology and Courseval can operate off of the same base list of enrollments.
# Schoology uses different start and end date parameters than Courseval, so the view is agnostic about dates. 
# This query should return all instructors and students enrolled in active courses
# with a start date less than six months from the current date.
# The union picks up recent canceled courses so Schoology knows to delete them. Canceled courses are not included in enrollment_vw.

# This enrollment_vw section is a temporary holding-place for the query that should eventually become an actual view. For now, it's just a temporary table
ENROLLMENT_VW = '''
    select cast(substr(jcp.term_code,4,4) as integer) as year,
           substr(jcp.term_code,1,2) as sess, 
           substr(jcp.course_code,charindex('(',jcp.course_code)+1,4) as catalog,
           right(trim(jcp.term_code),4) as program,
           trim(substr(jcp.course_code,1,charindex('(',jcp.course_code)-1)) as course_no,
           trim(jcp.sec) as sec,
           trim(jcr.title) as course_title,
           to_number(trim(jcp.host_id)) as Carthage_ID,
           trim(jcp.status_code) as role,
           jtm.start_date as sess_start_date,
           jtm.end_date as sess_end_date     
    from jenzcrp_rec jcp
        JOIN jenzcrs_rec jcr 
            ON jcp.course_code = jcr.course_code
            AND jcp.sec = jcr.sec
            AND jcp.term_code = jcr.term_code
        JOIN jenztrm_rec jtm 
            ON jtm.term_code = jcr.term_code
    into temp enrollment_vw with no log;
'''

ENROLLMENT = '''
    SELECT
        trim(enr.course_no) || " (" || enr.catalog || ")" as CourseCode,
        trim(enr.course_no) || "-" || enr.sec || " " || enr.sess || " " || enr.year || " " || enr.program as SectionCode,
        enr.year || ";" || enr.sess || ";" || enr.course_no || ";" || enr.sec || ";" || enr.catalog || ";" || enr.program as SecSchoolCode,
        enr.carthage_id as UniqueUserID,
        enr.role as EnrollmentType,
        enr.sess || ' ' || enr.program as GradePeriod,
        enr.sess_start_date as start_date, 
        'Open'
    FROM enrollment_vw enr
    WHERE enr.sess_start_date <= ADD_MONTHS(today,6)
    AND enr.sess_end_date >= ADD_MONTHS(today,-1)
    
    UNION

    SELECT
        TRIM(sr.crs_no)||' ('||TRIM(sr.cat)||')' coursecode, 
        TRIM(sr.crs_no)||'-'||TRIM(sr.sec_no)||' '||TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) sectioncode,
        sr.yr||';'||TRIM(sr.sess)||';'||TRIM(sr.crs_no)||';'||TRIM(sr.sec_no)||';'||TRIM(sr.cat)||';'||TRIM(cr.prog) sectionschoolcode,
        sr.fac_id uniqueuserid,
        '1PR' enrollmenttype,
        TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) gradeperiod,
        sr.beg_date startdate, 'Closed'
    FROM
        sec_rec sr
    JOIN 
        crs_rec cr ON cr.crs_no = sr.crs_no
        AND cr.cat = sr.cat
    JOIN 
        id_rec ir ON ir.id = sr.fac_id 
    JOIN 
        sess_table st ON sr.sess = st.sess
    JOIN 
        dept_table dt ON dt.dept = cr.dept
    WHERE 
        sr.stat = 'X'
        AND sr.end_date > TODAY
        AND sr.stat_date > TODAY-4
        AND trim(cr.prog) NOT IN ('PRDV','PARA','KUSD')
'''

EVAL_STUDENT_ENROLLMENT = '''
	SELECT
        enr.course_no as CourseNumber,
        enr.sec as CourseSection,
        enr.carthage_id as PersonIdentifier,
        enr.sess || ' ' || enr.year as GradePeriod,
        CASE 
        	WHEN enr.sess = "RA" THEN "Fall " || enr.year
        	WHEN enr.sess = "RB" THEN "J-Term " || enr.year
        	WHEN enr.sess = "RC" THEN "Spring " || enr.year
        	WHEN enr.sess = "RE" THEN "Summer " || enr.year
        	WHEN enr.sess = "GA" THEN "Fall Graduate " || enr.year
        	WHEN enr.sess = "GB" THEN "J-Term Graduate " || enr.year
        	WHEN enr.sess = "GC" THEN "Spring Graduate " || enr.year
        	WHEN enr.sess = "GE" THEN "Summer Graduate " || enr.year
        	WHEN enr.sess = "AA" THEN "Fall I " || enr.year
        	WHEN enr.sess = "AB" THEN "Fall II " || enr.year
        	WHEN enr.sess = "AG" THEN "J-Term " || enr.year
        	WHEN enr.sess = "AK" THEN "Spring I " || enr.year
        	WHEN enr.sess = "AM" THEN "Spring II " || enr.year
        	WHEN enr.sess = "AS" THEN "Summer I " || enr.year
        	WHEN enr.sess = "AT" THEN "Summer II " || enr.year
        END as Period
    FROM enrollment_vw enr
    WHERE enr.sess_start_date <= today
    AND enr.sess_end_date >= ADD_MONTHS(today,-1)
    AND enr.sess[1,1] != "K"
    AND enr.role = "STU"
'''

EVAL_FACULTY_ENROLLMENT = '''
	SELECT
        enr.course_no as CourseNumber,
        enr.sec as CourseSection,
        enr.carthage_id as PersonIdentifier,
        enr.sess || ' ' || enr.year as GradePeriod,
        CASE 
        	WHEN enr.sess = "RA" THEN "Fall " || enr.year
        	WHEN enr.sess = "RB" THEN "J-Term " || enr.year
        	WHEN enr.sess = "RC" THEN "Spring " || enr.year
        	WHEN enr.sess = "RE" THEN "Summer " || enr.year
        	WHEN enr.sess = "GA" THEN "Fall Graduate " || enr.year
        	WHEN enr.sess = "GB" THEN "J-Term Graduate " || enr.year
        	WHEN enr.sess = "GC" THEN "Spring Graduate " || enr.year
        	WHEN enr.sess = "GE" THEN "Summer Graduate " || enr.year
        	WHEN enr.sess = "AA" THEN "Fall I " || enr.year
        	WHEN enr.sess = "AB" THEN "Fall II " || enr.year
        	WHEN enr.sess = "AG" THEN "J-Term " || enr.year
        	WHEN enr.sess = "AK" THEN "Spring I " || enr.year
        	WHEN enr.sess = "AM" THEN "Spring II " || enr.year
        	WHEN enr.sess = "AS" THEN "Summer I " || enr.year
        	WHEN enr.sess = "AT" THEN "Summer II " || enr.year
        END as Period
    FROM enrollment_vw enr
    WHERE enr.sess_start_date <= today
    AND enr.sess_end_date >= ADD_MONTHS(today,-1)
    AND enr.sess[1,1] != "K"
    AND enr.role = "1PR"
'''
# fetch crosslist courses
# this query returns two different sections that have the same meeting time
# and place but may have a different course number for a program with a start date
# less than six months from the current date.
CROSSLIST = '''
    SELECT
    q1.mtg_no,  q2.crls_code, q1.targ_code
     --Important, the targ_code is the section that will be the master for the cross-listed sections.
     --MUST NOT CHANGE the order or the load into schoology will undo previous loads.
    FROM
    (
        --First part of query finds sections that share a meeting pattern
        SELECT sr2.mtg_no,
        MAX(mr2.yr||';'||TRIM(mr2.sess)||';'||TRIM(sr2.crs_no)||';'||TRIM(sr2.sec_no)||';'||TRIM(cr2.cat)||';'||cr2.prog) AS targ_code
        FROM secmtg_rec sr2
        INNER JOIN
            (
            SELECT mtg_no, sess, yr
            FROM mtg_rec
            WHERE (mtg_rec.beg_date <= ADD_MONTHS(today,6)
            AND mtg_rec.end_date >= ADD_MONTHS(today,-3)) --Different date range FROM course and enrollments.
            --Will not unlink courses til 3 months after end date
            --after that, course should definitely be archived and removing the cross listing will have no effect on course materials
            ) mr2
            ON sr2.mtg_no = mr2.mtg_no
        INNER JOIN
            (SELECT prog, crs_no, cat
            FROM crs_rec
            ) cr2
            ON cr2.crs_no = sr2.crs_no
            AND cr2.cat = sr2.cat
        GROUP BY sr2.mtg_no
        HAVING COUNT(sr2.mtg_no) > 1
    )
     q1
    INNER JOIN
    --This portion finds any additional sections with the same meeting number as those found above
    (
        SELECT s.mtg_no, s.crs_no, mr.yr, mr.sess, cr.cat, cr.prog, s.sec_no,
        mr.yr||';'||TRIM(mr.sess)||';'||TRIM(s.crs_no)||';'||TRIM(s.sec_no)||';'||TRIM(cr.cat)||';'||cr.prog as crls_code
        FROM secmtg_rec s
        INNER JOIN 
            (
            SELECT mtg_no, sess, yr
            FROM mtg_rec
            ) mr 
            ON s.mtg_no = mr.mtg_no
        INNER JOIN
            (SELECT prog, crs_no, cat
            FROM crs_rec
            ) cr 
            ON cr.crs_no = s.crs_no
            AND cr.cat = s.cat 
    )
    q2
    ON q1.mtg_no =  q2.mtg_no
    AND q2.crls_code != q1.targ_code
    ORDER BY q1.mtg_no;
'''
CANCELLED_COURSES = '''
        SELECT  
        au.crs_no, au.sec_no, au.sess, au.yr,
        TRIM(cr.title1) || ' ' || TRIM(cr.title2) || ' ' || TRIM(cr.title3) AS Title,
        au.beg_date, au.end_date, au.stat, au.stat_date,        au.schd_upd_date, 
        bu.stat OldStat, au.stat newstat, au.audit_timestamp 
    FROM
        cars_audit:sec_rec au
    JOIN 
        cars_audit:sec_rec bu
        ON bu.crs_no = au.crs_no
        AND bu.cat = au.cat
        AND bu.yr = au.yr
        AND bu.sess = au.sess
        AND bu.sec_no = au.sec_no
        AND bu.audit_timestamp = au.audit_timestamp
        AND bu.stat != au.stat
    JOIN id_rec ir
        ON ir.id = au.fac_id
    JOIN crs_rec cr
        on cr.crs_no = au.crs_no
        AND cr.cat = au.cat
    WHERE au.STAT = 'X'
        AND au.audit_timestamp > TODAY-1 
    ORDER BY au.crs_no, au.sec_no
'''