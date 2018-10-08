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
        nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
        'Carthage College' School,
        TRIM(jenzcrs_rec.term_code)||' '||Instructor.subsess GradingPeriod,
        'Active' Sec_status
    FROM 
        jenzcrs_rec 
    JOIN 
        crs_rec on TRIM(jenzcrs_rec.course_code) = TRIM(crs_rec.crs_no)||' ('||TRIM(crs_rec.cat)||')'
    JOIN 
        Jenzccd_rec on Jenzccd_rec.course_code = jenzcrs_rec.course_code 
    JOIN
        jenztrm_rec on jenztrm_rec.term_code = jenzcrs_rec.term_code
    LEFT JOIN 
        jenzdpt_rec on jenzdpt_rec.dept_code = jenzccd_rec.dept_code
    LEFT JOIN 
        jenzsch_rec on jenzsch_rec.term_code = jenzcrs_rec.term_code
        and jenzsch_rec.sec = jenzcrs_rec.sec
        and jenzsch_rec.course_code = jenzcrs_rec.course_code
    JOIN 
        secmtg_rec on secmtg_rec.crs_no = crs_rec.crs_no
        and secmtg_rec.sec_no = jenzcrs_rec.sec
        and TRIM(secmtg_rec.sess) = left(jenzcrs_rec.term_code,2) 
        and secmtg_rec.yr =  SUBSTRING(jenzcrs_rec.term_code FROM 4 FOR 4)
        and secmtg_rec.cat = crs_rec.cat
    JOIN 
        (select a.crs_no, a.sec_no, a.cat, a.yr, a.sess, a.subsess, c.lastname as InstrName, c.firstname, c.fullname, a.fac_id
        from sec_rec a, id_rec c
        where c.id = a.fac_id) Instructor
        on Instructor.sec_no = secmtg_rec.sec_no
        and Instructor.crs_no = secmtg_rec.crs_no
        and Instructor.cat = secmtg_rec.cat
        and Instructor.yr = secmtg_rec.yr
        and Instructor.sess = secmtg_rec.sess
     JOIN sess_table st on 
        st.sess = secmtg_rec.sess 
    LEFT JOIN
        (SELECT  b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt as BLDG, a.room as ROOM,
            a.mtg_no as MaxMtgNo, 
            MAX(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int),'------- 0-0')) as x,
            MIN(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int),'------- 0-0')) as y	
            FROM  secmtg_rec b
            JOIN mtg_rec a on a.mtg_no = b.mtg_no
            AND a.yr = b.yr
            AND a.sess = b.sess
            LEFT JOIN bldg_table c 
            ON c.bldg = a.bldg
        GROUP BY b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt, a.room, a.mtg_no ) MeetPattern
        ON MeetPattern.crs_no = crs_rec.crs_no
        AND MeetPattern.yr = left(jenzcrs_rec.coursekey,4)
        AND MeetPattern.MaxMtgNo = secmtg_rec.mtg_no
    WHERE
        jenztrm_rec.start_date <= ADD_MONTHS(today,6)
        AND
        jenztrm_rec.end_date >= ADD_MONTHS(today,-1)
        AND right(trim(jenzcrs_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
        AND jenzccd_rec.title IS NOT NULL

    UNION ALL

    SELECT
        TRIM(cr.title1)||' '||TRIM(cr.title2)||' '||TRIM(cr.title3) Coursename, 
        TRIM(dt.txt) department, TRIM(sr.crs_no)||' ('||TRIM(sr.cat)||')' coursecode, 
        TO_CHAR(sr.hrs,"*.**")  credit,
        TRIM(trim(cr.title1)||' '||TRIM(cr.title2)||' '||TRIM(cr.title3))||'-'||
        TRIM(sr.sec_no)||' '||TRIM(st.txt)||' '||sr.yr||' '||
        case 
            when TRIM(x) = TRIM(y) then x 
            else  x||' / '||y 
        end descr,
        TRIM(sr.sec_no)||'-'||TRIM(ir.lastname)||' '||TRIM(st.txt)||' '||sr.yr||' '||
        case 
            when TRIM(x) = TRIM(y) then x 
            else  x||' / '||y 
        end sectionname,
        sr.yr||';'||TRIM(sr.sess)||';'||TRIM(sr.crs_no)||';'||TRIM(sr.sec_no)||';'||TRIM(sr.cat)||';'||TRIM(cr.prog) sectionschoolcode,
        TRIM(sr.crs_no)||'-'||TRIM(sr.sec_no)||' '||TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) sectioncode,
        case 
            when TRIM(x) = TRIM(y) then x 
            else  x||' / '||y 
        end  secdescr,
        nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
        'Carthage College' School,
        TRIM(sr.sess)||' '||sr.yr||' '||TRIM(cr.prog) GradingPeriod, 'Cancelled' Sec_status
    FROM 
        sec_rec sr
    JOIN 
        crs_rec cr on cr.crs_no = sr.crs_no
        and cr.cat = sr.cat
    JOIN 
        id_rec ir on ir.id = sr.fac_id 
    JOIN 
        sess_table st on sr.sess = st.sess
    JOIN 
        dept_table dt on dt.dept = cr.dept
    JOIN 
        secmtg_rec mtg on mtg.crs_no = sr.crs_no
        AND mtg.sec_no = sr.sec_no
        AND trim(mtg.sess) = sr.sess 
        AND mtg.yr =  sr.yr
        AND mtg.cat = sr.cat
    LEFT JOIN
        (select  b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt as BLDG, a.room as ROOM,
            a.mtg_no as MaxMtgNo, 
            MAX(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int),'------- 0-0')) as x,
            MIN(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int),'------- 0-0')) as y	
            FROM  secmtg_rec b
            JOIN mtg_rec a on a.mtg_no = b.mtg_no
            AND a.yr = b.yr
            AND a.sess = b.sess
            LEFT JOIN bldg_table c 
            ON c.bldg = a.bldg
        GROUP BY b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt, a.room, a.mtg_no ) MeetPattern
        ON MeetPattern.crs_no = sr.crs_no
        AND MeetPattern.yr = sr.yr
        AND MeetPattern.MaxMtgNo = mtg.mtg_no 
    WHERE 
        sr.stat = 'X'
        AND sr.end_date > TODAY
        AND sr.stat_date > TODAY-4
'''
# fetch users
# Users are collected in a single query to get both Students and Faculty/Staff.
# The student query portion pulls all students with an academic record
# between the start of the current fiscal year (July 1) and the end of the current fiscal year.
# The Faculty/Staff portion should get all employees with active job records
# within the last year.
# There are enrollments for individuals who are not currently staff or faculty.
# If I filter to only users who were employed in the last year,
# I find enrollment records without a matching user. 
USERS = '''
    SELECT
    DISTINCT
       id_rec.firstname, addree_rec.alt_name preferred_first_name,
       id_rec.middlename, id_rec.lastname, '' name_prefix,
       trim(jenzprs_rec.host_username) username, TRIM(jenzprs_rec.e_mail) EMAIL,
       to_number(jenzprs_rec.host_id) UniqueID,
       CASE WHEN title1.hrpay NOT IN ('VEN', 'DPW', 'BIW', 'FV2', 'SUM', 'GRD')
           OR TLE.tle = 'Y'
           THEN 'FAC' ELSE 'STU' END AS ROLE,
       'Carthage College' school, jenzprs_rec.host_id schoology_id,
       CASE NVL(title1.job_title,'x') WHEN 'x' then '' ELSE trim(title1.job_title) END||
       CASE NVL(title2.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title2.job_title) END||
       CASE NVL(title3.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title3.job_title) END
       Position, '' pwd, '' gender, '' GradYr, '' additional_schools
   FROM jenzprs_rec
       LEFT JOIN jenzcst_rec
       ON jenzprs_rec.host_id = jenzcst_rec.host_id
       AND jenzcst_rec.status_code IN ('FAC', 'STF', 'STU', 'ADM')
           JOIN id_rec ON id_rec.id =  jenzprs_rec.host_id
           LEFT JOIN job_rec title1 ON title1.id = jenzprs_rec.host_id AND title1.title_rank = 1
               AND (title1.end_date IS NULL OR title1.end_date > current) AND title1.job_title IS NOT NULL
           LEFT JOIN job_rec title2 ON title2.id = jenzprs_rec.host_id AND title2.title_rank = 2
               AND (title2.end_date is null or title2.end_date > current) AND title2.job_title IS NOT NULL
           LEFT JOIN job_rec title3 ON title3.id = jenzprs_rec.host_id AND title3.title_rank = 3
               AND (title3.end_date is null or title3.end_date > current) AND title3.job_title IS NOT NULL
           LEFT JOIN job_rec title4 ON title4.id = jenzprs_rec.host_id AND title4.title_rank = 4
               AND (title4.end_date is null or title4.end_date > current) AND title4.job_title IS NOT NULL
           LEFT JOIN prog_enr_rec TLE
               ON TLE.id = jenzprs_rec.host_id
               AND TLE.acst= 'GOOD'
               AND TLE.tle = 'Y'
           LEFT JOIN addree_rec ON addree_rec.prim_id = jenzprs_rec.host_id
           AND addree_rec.style = 'N'
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
       GROUP BY id_rec.lastname, id_rec.firstname, preferred_first_name,
       id_rec.middlename, name_prefix, username, email, UniqueID, schoology_id,
       Position, title1.job_title, TLE.tle, title1.hrpay
       ORDER BY id_rec.lastname ASC, id_rec.firstname ASC, role ASC;
'''
# fetch enrollment
# This query should return all instructors and students enrolled in active courses
# with a start date less than six months from the current date.
ENROLLMENT = '''
    SELECT
        TRIM(jenzcrp_rec.course_code) CourseCode,
        left(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) SectionCode,
        TRIM(jenzcrs_rec.coursekey) SecSchoolCode,
        to_number(jenzcrp_rec.host_id) UniqueUserID,
        TRIM(jenzcrp_rec.status_code) EnrollmentType,
        TRIM(jenzcrp_rec.term_code)||' '||TRIM(sec_rec.subsess) GradePeriod,
        jenztrm_rec.start_date, 'Open'
    FROM
        jenzcrp_rec
    JOIN
        jenzcrs_rec ON jenzcrp_rec.course_code = jenzcrs_rec.course_code
        AND jenzcrp_rec.sec = jenzcrs_rec.sec
        AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    JOIN
        jenztrm_rec ON jenztrm_rec.term_code = jenzcrs_rec.term_code
    JOIN
        sec_rec ON
        jenzcrs_rec.sec =  sec_rec.sec_no
        AND TRIM(jenzcrs_rec.course_code) = TRIM(sec_rec.crs_no)||' ('||TRIM(sec_rec.cat)||')'
        AND LEFT (jenzcrs_rec.term_code,2) = TRIM(sec_rec.sess)
    WHERE
        jenztrm_rec.start_date <= ADD_MONTHS(today,6)
        AND
        jenztrm_rec.end_date >= ADD_MONTHS(today,-1)
    AND
    RIGHT(TRIM(jenzcrp_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')

    UNION ALL

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