# fetch courses and sections
# This query should return all courses and sections active with a start date less
# than six months from the current date.
# Based on the dates for the terms courses and sections are made active
# or inactive automatically.
COURSES = '''
    SELECT 
        TRIM(jenzccd_rec.title) coursename, TRIM(jenzdpt_rec.descr) department,
        TRIM(jenzcrs_rec.course_code) coursecode, jenzcrs_rec.hrs credits,
        TRIM(jenzccd_rec.title)||'-'||TRIM(jenzcrs_rec.sec)||' '||  CASE
            WHEN TRIM(x) = TRIM(y) THEN x
            ELSE  x||' / '||y
        END descr,
        TRIM(jenzcrs_rec.sec)||'-'||TRIM(InstrName)||' '||CASE
            WHEN TRIM(x) = TRIM(y) THEN x
            ELSE  x||' / '||y
         END sectionname,
        TRIM(jenzcrs_rec.coursekey) secschoolcode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) sectioncode,
            CASE
            WHEN TRIM(x) = TRIM(y) THEN x
            ELSE  x||' / '||y END AS secdescr, nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location,
        'Carthage College' school, TRIM(jenzcrs_rec.term_code) gradingperiod
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
        AND TRIM(secmtg_rec.sess) = LEFT(jenzcrs_rec.term_code,2)
        AND secmtg_rec.yr =  SUBSTRING(jenzcrs_rec.term_code FROM 4 FOR 4)
        AND secmtg_rec.cat = crs_rec.cat
    JOIN
        (SELECT a.crs_no, a.sec_no, a.cat, a.yr, a.sess, c.lAStname AS InstrName, c.firstname, c.fullname, a.fac_id
        FROM sec_rec a, id_rec c
        WHERE c.id = a.fac_id) Instructor
        ON Instructor.sec_no = secmtg_rec.sec_no
        AND Instructor.crs_no = secmtg_rec.crs_no
        AND Instructor.cat = secmtg_rec.cat
        AND Instructor.yr = secmtg_rec.yr
        AND Instructor.sess = secmtg_rec.sess
    LEFT JOIN
        (SELECT b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt AS BLDG,
            a.room AS ROOM, a.mtg_no AS MaxMtgNo,
            MAX(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||CAST(beg_tm AS int)||'-'||CAST(END_tm AS int),'------- 0-0')) AS x,
            MIN(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||CAST(beg_tm AS int)||'-'||CAST(END_tm AS int),'------- 0-0')) AS y
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
        jenztrm_rec.start_date <= ADD_MONTHS(today,6)
        AND
        jenztrm_rec.start_date >= ADD_MONTHS(today,-1)
        AND right(TRIM(jenzcrs_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
        AND jenzccd_rec.title IS NOT NULL
    ORDER BY jenzcrs_rec.course_code
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
        id_rec.firstname, addree_rec.alt_name preferred_first_name, id_rec.middlename,
        id_rec.lastname, id_rec.title name_prefix, trim(jenzprs_rec.host_username) username,
        TRIM(jenzprs_rec.e_mail) email, to_number(jenzprs_rec.host_id) uniqueid,
        CASE WHEN NVL(MIN(jenzcst_rec.status_code),'x') = 'STU' THEN 'STU'
             WHEN NVL(MIN(jenzcst_rec.status_code),'x') = 'x' AND title1.job_title IS NULL THEN 'STU'
             ELSE 'FAC' END AS role,
        'Carthage College' school, jenzprs_rec.host_id schoology_id,
        CASE NVL(title1.job_title,'x') WHEN 'x' THEN '' ELSE TRIM(title1.job_title) END||
        CASE NVL(title2.job_title,'x') WHEN 'x' THEN '' ELSE '; '||TRIM(title2.job_title) END||
        CASE NVL(title3.job_title,'x') WHEN 'x' THEN '' ELSE '; '||TRIM(title3.job_title) END
        position, '' pwd, '' gender, '' gradyr, '' additional_schools
    FROM jenzprs_rec
        LEFT JOIN jenzcst_rec
        ON jenzprs_rec.host_id = jenzcst_rec.host_id
        AND jenzcst_rec.status_code IN ('FAC', 'STF', 'STU', 'ADM')
            JOIN id_rec ON id_rec.id = jenzprs_rec.host_id
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
        GROUP BY id_rec.lastname, id_rec.firstname, preferred_first_name, id_rec.middlename,
        name_prefix, username, email, UniqueID, schoology_id, Position, title1.job_title
        ORDER BY id_rec.lastname ASC, id_rec.firstname ASC, role ASC;
'''
# fetch enrollment
# This query should return all instructors and students enrolled in active courses
# with a start date less than six months from the current date.
ENROLLMENT = '''
    SELECT
        trim(jenzcrp_rec.course_code) coursecode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) sectioncode,
        trim(jenzcrs_rec.coursekey) secschoolcode, to_number(jenzcrp_rec.host_id) uniqueuserid,
        trim(jenzcrp_rec.status_code) enrollmenttype,
        trim(jenzcrp_rec.term_code) gradeperiod, jenztrm_rec.start_date
    FROM
        jenzcrp_rec
    JOIN
        jenzcrs_rec ON jenzcrp_rec.course_code = jenzcrs_rec.course_code
        AND jenzcrp_rec.sec = jenzcrs_rec.sec
        AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    JOIN
        jenztrm_rec on jenztrm_rec.term_code = jenzcrs_rec.term_code
    WHERE
        jenztrm_rec.start_date <= ADD_MONTHS(TODAY,6)
        AND
        jenztrm_rec.start_date >= ADD_MONTHS(TODAY,-1)
    AND RIGHT(trim(jenzcrp_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
    ORDER BY
        jenzcrp_rec.course_code
'''
# fetch crosslist courses
# this query returns two different sections that have the same meeting time
# and place but may have a different course number for a program with a start date
# less than six months from the current date.
CROSSLIST = '''
    SELECT secmtg_rec.mtg_no,
        MIN(mtg_rec.yr||';'||TRIM(mtg_rec.sess)||';'||TRIM(secmtg_rec.crs_no)||';'||TRIM(secmtg_rec.sec_no)||';'||TRIM(secmtg_rec.cat)||';'||crs_rec.prog) AS crls_code,
        MAX(mtg_rec.yr||';'||TRIM(mtg_rec.sess)||';'||TRIM(secmtg_rec.crs_no)||';'||TRIM(secmtg_rec.sec_no)||';'||TRIM(secmtg_rec.cat)||';'||crs_rec.prog) AS targ_code
    FROM
        secmtg_rec, mtg_rec, crs_rec
    WHERE
        secmtg_rec.mtg_no = mtg_rec.mtg_no
    AND
        crs_rec.crs_no = secmtg_rec.crs_no
    AND
        crs_rec.cat = secmtg_rec.cat
    AND
        (mtg_rec.yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN YEAR(TODAY) ELSE YEAR(TODAY)-1 END
    OR
        (mtg_rec.beg_date <= ADD_MONTHS(TODAY,6)
    AND
        mtg_rec.beg_date >= ADD_MONTHS(TODAY,-1)))
    GROUP BY
        secmtg_rec.mtg_no
    HAVING COUNT
        (secmtg_rec.mtg_no) > 1
    ORDER BY
        mtg_no
'''