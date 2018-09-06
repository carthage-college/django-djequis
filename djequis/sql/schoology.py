# fetch courses and sections
# This query should return all courses and sections active with a start date less
# than six months from the current date.
# Based on the dates for the terms courses and sections are made active
# or inactive automatically.
COURSES = '''
    SELECT 
        TRIM(jenzccd_rec.title) Coursename, TRIM(jenzdpt_rec.descr) Department,
        TRIM(jenzcrs_rec.course_code) CourseCode, jenzcrs_rec.hrs Credits, 
        TRIM(jenzccd_rec.title)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(st.txt)||' '||secmtg_rec.yr||' '|| CASE
            WHEN TRIM(x) = trim(y) THEN x
            ELSE  x||' / '||y
        END  descr,
        TRIM(jenzcrs_rec.sec)||'-'||TRIM(InstrName)||' '||TRIM(st.txt)||' '||secmtg_rec.yr||' '|| CASE
            WHEN trim(x) = trim(y) THEN x
            ELSE  x||' / '||y
         END SectionName, TRIM(jenzcrs_rec.coursekey) SecSchoolCode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) SectionCode,
            CASE
            WHEN trim(x) = trim(y) THEN x
            ELSE  x||' / '||y END AS SecDescr,
        NVL(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
        'Carthage College' School,
        TRIM(jenzcrs_rec.term_code)||' '||Instructor.subsess GradingPeriod
    FROM
        jenzcrs_rec
    JOIN
        crs_rec ON TRIM(jenzcrs_rec.course_code) = TRIM(crs_rec.crs_no)||' ('||TRIM(crs_rec.cat)||')'
    JOIN
        Jenzccd_rec ON Jenzccd_rec.course_code = jenzcrs_rec.course_code
    JOIN
        jenztrm_rec ON jenztrm_rec.term_code = jenzcrs_rec.term_code
    LEFT JOIN
        jenzdpt_rec ON jenzdpt_rec.dept_code = jenzccd_rec.dept_code
    LEFT JOIN
        jenzsch_rec ON jenzsch_rec.term_code = jenzcrs_rec.term_code
        AND jenzsch_rec.sec = jenzcrs_rec.sec
        AND jenzsch_rec.course_code = jenzcrs_rec.course_code
    JOIN
        secmtg_rec ON secmtg_rec.crs_no = crs_rec.crs_no
        AND secmtg_rec.sec_no = jenzcrs_rec.sec
        AND trim(secmtg_rec.sess) = LEFT(jenzcrs_rec.term_code,2)
        AND secmtg_rec.yr =  SUBSTRING(jenzcrs_rec.term_code FROM 4 FOR 4)
        AND secmtg_rec.cat = crs_rec.cat
    JOIN
        (SELECT a.crs_no, a.sec_no, a.cat, a.yr, a.sess, a.subsess,
        c.lastname AS InstrName, c.firstname, c.fullname, a.fac_id
        FROM sec_rec a, id_rec c
        WHERE c.id = a.fac_id) Instructor
        ON Instructor.sec_no = secmtg_rec.sec_no
        AND Instructor.crs_no = secmtg_rec.crs_no
        AND Instructor.cat = secmtg_rec.cat
        AND Instructor.yr = secmtg_rec.yr
        AND Instructor.sess = secmtg_rec.sess
     JOIN sess_table st ON
        st.sess = secmtg_rec.sess 
    LEFT JOIN
        (SELECT  b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt AS BLDG,
        a.room AS ROOM, a.mtg_no as MaxMtgNo,
        MAX(TRIM(b.crs_no)||'-'||b.sec_no||'-'||NVL(TRIM(DAYS)||' '||CAST(beg_tm AS INT)||'-'||CAST(end_tm AS INT),'------- 0-0')) AS x,
        MIN(TRIM(b.crs_no)||'-'||b.sec_no||'-'||NVL(TRIM(DAYS)||' '||CAST(beg_tm AS INT)||'-'||CAST(end_tm AS INT),'------- 0-0')) AS y
        FROM  secmtg_rec b
        JOIN mtg_rec a ON a.mtg_no = b.mtg_no
        AND a.yr = b.yr
        AND a.sess = b.sess
        LEFT JOIN bldg_table c
        ON c.bldg = a.bldg
        GROUP BY b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt, a.room, a.mtg_no ) MeetPattern
        ON MeetPattern.crs_no = crs_rec.crs_no
        AND MeetPattern.yr = LEFT(jenzcrs_rec.coursekey,4)
        AND MeetPattern.MaxMtgNo = secmtg_rec.mtg_no
    WHERE 
        jenztrm_rec.start_date <= ADD_MONTHS(TODAY,6)
        AND 
        jenztrm_rec.start_date >= ADD_MONTHS(TODAY,-1)
        AND RIGHT(TRIM(jenzcrs_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
        AND jenzccd_rec.title IS NOT NULL
    ORDER BY jenzcrs_rec.course_code;
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
    SELECT DISTINCT
        id_rec.firstname, addree_rec.alt_name preferred_first_name, id_rec.middlename, id_rec.lastname,
        id_rec.title name_prefix, TRIM(jenzprs_rec.host_username) username,
        TRIM(jenzprs_rec.e_mail) EMAIL, to_number(jenzprs_rec.host_id) UniqueID,
        CASE
            WHEN nvl(title1.hrpay, '') IN ('','DPW')
                AND trim(NVL(title1.job_title, '')) = ''
                AND trim(NVL(title2.job_title, '')) = ''
                AND trim(NVL(title3.job_title, '')) = ''
                AND trim(NVL(title4.job_title, '')) = ''
            THEN 'STU'
            ELSE 'FAC' END AS ROLE,
        'Carthage College' school,
        jenzprs_rec.host_id schoology_id,
        CASE NVL(title1.job_title,'x') WHEN 'x' THEN '' ELSE trim(title1.job_title) END ||
        CASE NVL(title2.job_title,'x') WHEN 'x' THEN '' ELSE '; '||trim(title2.job_title) END||
        CASE NVL(title3.job_title,'x') WHEN 'x' THEN '' ELSE '; '||trim(title3.job_title) END||
        CASE NVL(title4.job_title,'x') WHEN 'x' THEN '' ELSE '; '||trim(title4.job_title) END
        Position, '' pwd, '' gender, '' GradYr, '' additional_schools
    FROM jenzprs_rec
        LEFT JOIN jenzcst_rec
        ON jenzprs_rec.host_id = jenzcst_rec.host_id
        AND jenzcst_rec.status_code IN ('FAC', 'STF', 'STU', 'ADM')
            JOIN id_rec ON id_rec.id =  jenzprs_rec.host_id
            LEFT JOIN job_rec title1 ON title1.id = jenzprs_rec.host_id AND title1.title_rank = 1
                AND (title1.end_date IS NULL OR title1.end_date > current) AND title1.job_title IS NOT NULL
            LEFT JOIN job_rec title2 ON title2.id = jenzprs_rec.host_id AND title2.title_rank = 2
                AND (title2.end_date IS NULL OR title2.end_date > current) AND title2.job_title IS NOT NULL
            LEFT JOIN job_rec title3 ON title3.id = jenzprs_rec.host_id AND title3.title_rank = 3
                AND (title3.end_date IS NULL OR title3.end_date > current) AND title3.job_title IS NOT NULL
            LEFT JOIN job_rec title4 ON title4.id = jenzprs_rec.host_id AND title4.title_rank = 4
                AND (title4.end_date IS NULL OR title4.end_date > current) AND title4.job_title IS NOT NULL
            LEFT JOIN addree_rec ON addree_rec.prim_id = jenzprs_rec.host_id AND addree_rec.style = 'N'
    WHERE jenzprs_rec.host_id IN
        (
            SELECT to_number(host_id) as UID
                FROM jenzcrp_rec
            UNION All
            SELECT cx_id as UID
                FROM provsndtl_rec
                WHERE subsys = 'MSTR'
                    AND action = 'Active'
                    AND roles NOT IN ('Contractor')
        )
    GROUP BY
        id_rec.lastname, id_rec.firstname, preferred_first_name, id_rec.middlename,
        name_prefix, username, email, UniqueID,
        schoology_id,
        title1.job_title, title2.job_title, title3.job_title,
        title4.job_title, jenzcst_rec.status_code, title1.hrpay
    ORDER BY id_rec.lastname ASC, id_rec.firstname ASC, ROLE ASC;
'''
# fetch enrollment
# This query should return all instructors and students enrolled in active courses
# with a start date less than six months from the current date.
ENROLLMENT = '''
    SELECT
        TRIM(jenzcrp_rec.course_code) CourseCode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||trim(jenzcrs_rec.sec)||' '||trim(jenzcrs_rec.term_code) SectionCode,
        TRIM(jenzcrs_rec.coursekey) SecSchoolCode,
        TO_NUMBER(jenzcrp_rec.host_id) UniqueUserID,
        TRIM(jenzcrp_rec.status_code) EnrollmentType,
        TRIM(jenzcrp_rec.term_code)||' '||trim(sec_rec.subsess) GradePeriod,
        jenztrm_rec.start_date
    FROM jenzcrp_rec
    JOIN jenzcrs_rec ON jenzcrp_rec.course_code = jenzcrs_rec.course_code
        AND jenzcrp_rec.sec = jenzcrs_rec.sec
        AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    JOIN jenztrm_rec ON jenztrm_rec.term_code = jenzcrs_rec.term_code
    JOIN sec_rec on
        jenzcrs_rec.sec =  sec_rec.sec_no
        AND trim(jenzcrs_rec.course_code) = trim(sec_rec.crs_no)||' ('||trim(sec_rec.cat)||')'
        AND LEFT (jenzcrs_rec.term_code,2) = trim(sec_rec.sess)
    WHERE jenztrm_rec.start_date <= ADD_MONTHS(TODAY,6)
        AND jenztrm_rec.start_date >= ADD_MONTHS(TODAY,-1)
        AND RIGHT(TRIM(jenzcrp_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
    ORDER BY
        jenzcrp_rec.course_code
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
    ORDER BY q1.mtg_no
'''