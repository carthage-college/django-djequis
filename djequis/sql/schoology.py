# fetch courses and sections
# This query should return all courses and sections active from July to July
# of the current fiscal year.
# Based on the dates for the terms courses and sections are made active
# or inactive automatically.
COURSES = '''
    SELECT 
        TRIM(jenzccd_rec.title) Coursename, TRIM(jenzdpt_rec.descr) Department,
        TRIM(jenzcrs_rec.course_code) CourseCode, jenzcrs_rec.hrs Credits,
        TRIM(jenzccd_rec.title)||'-'||TRIM(jenzcrs_rec.sec)||' '||
        CASE
            WHEN TRIM(x) = TRIM(y) THEN x
            ELSE  x||' / '||y
        END  descr,
        TRIM(jenzcrs_rec.sec)||'-'||TRIM(InstrName)||' '||
        CASE
            WHEN TRIM(x) = TRIM(y) THEN x
            ELSE  x||' / '||y
        END SectiONName,
        TRIM(jenzcrs_rec.coursekey) SecSchoolCode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) SectiONCode,
            CASE 
                WHEN TRIM(x) = TRIM(y) THEN x
                ELSE  x||' / '||y
            END AS SecDescr,
        nvl(TRIM(bldg)||' '||TRIM(ROOM),'TBA') location, 'Carthage College' School,
        TRIM(jenzcrs_rec.term_code) GradingPeriod
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
        (SELECT b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt AS BLDG, a.room AS ROOM,
            a.mtg_no AS MaxMtgNo,
            max(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cASt(beg_tm AS int)||'-'||cASt(END_tm AS int),'------- 0-0')) AS x,
            min(TRIM(b.crs_no)||'-'||b.sec_no||'-'||nvl(TRIM(days)||' '||cASt(beg_tm AS int)||'-'||cASt(END_tm AS int),'------- 0-0')) AS y
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
        jenztrm_rec.start_date >= CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        THEN TO_DATE(YEAR(TODAY)-1 || '-07-01', '%Y-%m-%d')
        ELSE  TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') END
        AND  jenztrm_rec.start_date < CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        THEN TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        ELSE  TO_DATE(YEAR(TODAY)+1 || '-07-01', '%Y-%m-%d') END
        AND RIGHT(TRIM(jenzcrs_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
        AND jenzccd_rec.title IS NOT NULL
    ORDER BY jenzcrs_rec.course_code
'''
# fetch users
# Users are collected in a single query to get both Students and Faculty/Staff.
# The student query portion pulls all students with an academic record between
# the start of the current fiscal year (July 1) and the end of
# the current fiscal year.
# The Faculty/Staff portion should get all employees with active job records
# within the last year.
# There are enrollments for individuals who are not currently staff or faculty.
# If I filter to only users who were employed in the last year,
# I find enrollment records without a matching user. 
USERS = '''
    SELECT DISTINCT
        id_rec.firstname, addree_rec.alt_name preferred_first_name, id_rec.middlename,
        id_rec.lastname, id_rec.title name_prefix, TRIM(jenzprs_rec.host_username) username,
        TRIM(jenzprs_rec.e_mail) EMAIL, jenzprs_rec.host_id UniqueID,
        CASE
            WHEN jenzcst_rec.STATUS_CODE = 'STU' THEN 'STU' ELSE 'FAC'
        END AS ROLE,
        'Carthage College' school, jenzprs_rec.host_id schoology_id,
        CASE NVL(title1.job_title,'x') WHEN 'x' THEN '' ELSE trim(title1.job_title) END||
        CASE NVL(title2.job_title,'x') WHEN 'x' THEN '' ELSE '; '||trim(title2.job_title) END||
        CASE NVL(title3.job_title,'x') WHEN 'x' THEN '' ELSE '; '||trim(title3.job_title) END
        Position, '' pwd, '' gender, '' GradYr, '' additional_schools
    FROM jenzprs_rec
        LEFT JOIN jenzcst_rec
        ON jenzprs_rec.host_id = jenzcst_rec.host_id
        AND jenzcst_rec.status_code IN ('FAC', 'STF', 'STU', 'ADM')
            JOIN id_rec ON id_rec.id = jenzprs_rec.host_id
            LEFT JOIN job_rec title1 ON title1.id = jenzprs_rec.host_id
                AND title1.title_rank = 1
                AND (title1.end_date IS NULL OR title1.end_date > current)
            LEFT JOIN job_rec title2 ON title2.id = jenzprs_rec.host_id
                AND title2.title_rank = 2
                AND (title2.end_date IS NULL OR title2.end_date > current)
            LEFT JOIN job_rec title3 ON title3.id = jenzprs_rec.host_id
                AND title3.title_rank = 3
                AND (title3.end_date IS NULL OR title3.end_date > current)
            LEFT JOIN job_rec title4 ON title4.id = jenzprs_rec.host_id
                AND title4.title_rank IS NULL
                AND (title4.end_date IS NULL OR title4.end_date > current)
            LEFT JOIN addree_rec ON addree_rec.prim_id = jenzprs_rec.host_id
                AND addree_rec.style = 'N'
    WHERE jenzprs_rec.host_id IN
        (
            SELECT to_number(host_id) AS UID
                FROM jenzcrp_rec
            UNION All
            SELECT cx_id AS UID
                FROM provsndtl_rec
                WHERE subsys = 'MSTR'
                    AND action = 'Active'
                    AND roles NOT IN ('Contractor')
        )
    ORDER BY id_rec.lastname, id_rec.firstname;
'''
# fetch enrollment
# This query should return all instructors and students enrolled in
# active courses July-July for the current fiscal year.
ENROLLMENT = '''
   SELECT
        jenzcrp_rec.course_code CourseCode,
        LEFT(jenzcrs_rec.course_code,8)||'-'||TRIM(jenzcrs_rec.sec)||' '||TRIM(jenzcrs_rec.term_code) SectionCode,
        jenzcrs_rec.coursekey SecSchoolCode, jenzcrp_rec.host_id UniqueUserID,
        jenzcrp_rec.status_code EnrollmentType, jenzcrp_rec.term_code GradePeriod
    FROM
        jenzcrp_rec
    JOIN
        jenzcrs_rec ON jenzcrp_rec.course_code = jenzcrs_rec.course_code
        AND jenzcrp_rec.sec = jenzcrs_rec.sec
        AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    JOIN
        jenztrm_rec ON jenztrm_rec.term_code = jenzcrs_rec.term_code
    WHERE
        jenztrm_rec.start_date >= CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        THEN TO_DATE(YEAR(TODAY)-1 || '-07-01', '%Y-%m-%d')
        ELSE  TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') END
        AND  jenztrm_rec.start_date < CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        THEN TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')
        ELSE  TO_DATE(YEAR(TODAY)+1 || '-07-01', '%Y-%m-%d') END
    AND right(trim(jenzcrp_rec.term_code),4) NOT IN ('PRDV','PARA','KUSD')
    ORDER BY
        jenzcrp_rec.course_code
'''
