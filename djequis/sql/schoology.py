# fetch courses
COURSES = '''
    select 
    trim(jenzccd_rec.title) Coursename,  
    trim(jenzdpt_rec.descr) Department,
    trim(jenzcrs_rec.course_code) CourseCode,  
    jenzcrs_rec.hrs Credits, 
    trim(jenzccd_rec.title)||'-'||trim(jenzcrs_rec.sec)||' '||case when trim(x) = '------- 0-0' and trim(y) = '------- 0-0' then ''
         when trim(x) = trim(y) then x 
         else  x||' / '||y end  descr,
    --jenzccd_rec.descr descr,
    trim(jenzcrs_rec.sec)||'-'||trim(InstrName)||' '||case when trim(x) = '------- 0-0' and trim(y) = '------- 0-0' then ''
         when trim(x) = trim(y) then x 
         else  x||' / '||y end SectionName, 
    trim(jenzcrs_rec.coursekey) SecSchoolCode, 
    left(jenzcrs_rec.course_code,8)||'-'||trim(jenzcrs_rec.sec)||' '||trim(jenzcrs_rec.term_code) SectionCode,  -- Use this one
    case when trim(x) = '------- 0-0' and trim(y) = '------- 0-0' then ''
         when trim(x) = trim(y) then x 
         else  x||' / '||y end as SecDescr, 
    trim(bldg)||' '||trim(ROOM) location,
    'Carthage College' School,
    trim(jenzcrs_rec.term_code) GradingPeriod
    from jenzcrs_rec 
    join crs_rec on trim(jenzcrs_rec.course_code) = trim(crs_rec.crs_no)||' ('||trim(crs_rec.cat)||')'
    join Jenzccd_rec on Jenzccd_rec.course_code = jenzcrs_rec.course_code 
    join jenztrm_rec on jenztrm_rec.term_code = jenzcrs_rec.term_code
    join jenzcrp_rec on jenzcrp_rec.course_code = jenzcrs_rec.course_code
    and jenzcrp_rec.sec = jenzcrs_rec.sec 
    AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    join id_rec on id_Rec.id = jenzcrp_rec.host_id
    ----left join disc_table on disc_table.disc = left(jenzcrs_rec.course_code,4)
    left join jenzdpt_rec on jenzdpt_rec.dept_code = jenzccd_rec.dept_code
    left join jenzsch_rec on jenzsch_rec.term_code = jenzcrs_rec.term_code
    and jenzsch_rec.sec = jenzcrs_rec.sec
    and jenzsch_rec.course_code = jenzcrs_rec.course_code
    join secmtg_rec on secmtg_rec.crs_no = crs_rec.crs_no
    and secmtg_rec.sec_no = jenzcrs_rec.sec
    and trim(secmtg_rec.sess) = left(jenzcrs_rec.term_code,2) 
    and secmtg_rec.yr =  SUBSTRING(jenzcrs_rec.term_code FROM 4 FOR 4)
    and secmtg_rec.cat = crs_rec.cat
    join (select a.crs_no, a.sec_no, a.cat, a.yr, a.sess, c.lastname as InstrName, c.firstname, c.fullname, a.fac_id
    from sec_rec a, id_rec c
    where c.id = a.fac_id) Instructor
    on Instructor.sec_no = secmtg_rec.sec_no
    and Instructor.crs_no = secmtg_rec.crs_no
    and Instructor.cat = secmtg_rec.cat
    and Instructor.yr = secmtg_rec.yr
    and Instructor.sess = secmtg_rec.sess
    join
    (select  b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt as BLDG, a.room as ROOM,
    max(a.mtg_no) as MaxMtgNo,
    max(b.crs_no||'-'||b.sec_no||'-'||trim(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int)) as x,
    min(b.crs_no||'-'||b.sec_no||'-'||trim(days)||' '||cast(beg_tm as int)||'-'||cast(end_tm as int)) as y
    from mtg_rec a, secmtg_rec b, bldg_table c
    where a.mtg_no = b.mtg_no
    and a.bldg = c.bldg
    group by b.crs_no, b.yr, b.sec_no, b.cat, b.sess, c.txt, a.room ) MeetPattern
    on MeetPattern.crs_no = crs_rec.crs_no
    and MeetPattern.yr = left(jenzcrs_rec.coursekey,4)
    and MeetPattern.MaxMtgNo = secmtg_rec.mtg_no
    where jenztrm_rec.start_date >= add_months(today,-1) and jenztrm_rec.end_date <= add_months(today,+5)
    --where jenztrm_rec.start_date < today and jenztrm_rec.end_date > today
    and jenzcrp_rec.status_code = '1PR'
    --and trim(jenzcrs_rec.course_code) = 'NEU 675R  S (UG17)'
    and id_rec.id in
    (select id from aa_rec
    where aa in ('EML1')
    and line1 in ('ahenle@carthage.edu', 'bcarlson1@carthage.edu', 'dbrownholland@carthage.edu', 'lchristoun@carthage.edu', 'apustina@carthage.edu',
    'adassow@carthage.edu', 'bzopf@carthage.edu', 'dcooksnyder@carthage.edu', 'ewheeler@carthage.edu', 'aduncan@carthage.edu',
    'jseymour@carthage.edu', 'ksconzert@carthage.edu', 'skonrad@carthage.edu', 'hyaple@carthage.edu',
    'lhuaracha@carthage.edu', 'npilarski@carthage.edu', 'jshields@carthage.edu', 'dschowalter@carthage.edu', 'abarnhart@carthage.edu',
    'fhicks@carthage.edu', 'cgrugel@carthage.edu', 'csabbar@carthage.edu'))
    
    order by jenzcrs_rec.term_code
'''
# fetch users
USERS = '''
    select distinct id_rec.firstname, addree_rec.alt_name preferred_first_name, id_rec.middlename, id_rec.lastname, 
    id_rec.title name_prefix, 
    trim(jenzprs_rec.host_username) username, TRIM(jenzprs_rec.e_mail) EMAIL,
    jenzprs_rec.host_id UniqueID, 
    jenzcst_rec.status_code role, 
    'Carthage College' school, 
    jenzprs_rec.host_id schoology_id, 
    CASE NVL(title1.job_title,'x') WHEN 'x' then '' ELSE trim(title1.job_title) END||  
    CASE NVL(title2.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title2.job_title) END||  
    CASE NVL(title3.job_title,'x') WHEN 'x' then '' ELSE '; '||trim(title3.job_title) END 
    Postition,
    '' pwd, '' gender, '' GradYr, '' additional_schools
    from jenzprs_rec
    join jenzcst_rec 
        on jenzprs_rec.host_id = jenzcst_rec.host_id
        and jenzcst_rec.status_code in ('FAC','STU')
    left join id_rec on id_rec.id =  jenzprs_rec.host_id
    left join job_rec title1 on title1.id = jenzprs_rec.host_id and title1.title_rank = 1 and (title1.end_date is null or title1.end_date > current) 
    left join job_rec title2 on title2.id = jenzprs_rec.host_id and title2.title_rank = 2 and (title2.end_date is null or title2.end_date > current)
    left join job_rec title3 on title3.id = jenzprs_rec.host_id and title3.title_rank = 3 and (title3.end_date is null or title3.end_date > current)
    left join addree_rec on addree_rec.prim_id = jenzprs_rec.host_id and addree_rec.style = 'N'
    --This will filter users to those who have enrollments in the selected time frame
    and jenzprs_rec.host_id in 
    (select ID from
    (select distinct ID from job_rec, hrdept_table, hrstat_table
    where job_rec.hrdept = hrdept_table.hrdept 
    and hrstat_table.hrstat = job_rec.hrstat
    and hrstat_table.inactive_date is null
    and job_rec.end_date is null and hrdept_table.end_date is null
    and hrpay not in ('VEN', 'DPW', 'GRD','K97', 'SUM')
    and hrstat_table.hrstat not in ('LV', 'DA', 'SA', 'STU', 'HR', 'HRPT', 'VEND') )
    union
    (select id from
    stu_acad_rec ACADREC inner join acad_cal_rec CALREC on CALREC.sess = ACADREC.sess and CALREC.yr = ACADREC.yr and CALREC.prog = ACADREC.prog 
    and CALREC.acyr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')	THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                END) )
    and (addree_rec.inactive_date is null or addree_rec.inactive_date > current) 
    --and id_rec.id in (729329) 
    --E:   This does prevent a small number of records from pulling if enabled
    order by jenzprs_rec.host_id
    --If an individual is both FAC and STU this will create two records.
    --May have to use another table to determine role
'''
# fetch enrollment
ENROLLMENT = '''
    select 
    jenzcrp_rec.course_code CourseCode, 
    left(jenzcrs_rec.course_code,8)||'-'||trim(jenzcrs_rec.sec)||' '||trim(jenzcrs_rec.term_code) SectionCode,
    jenzcrs_rec.coursekey SecSchoolCode,
    jenzcrp_rec.host_id UniqueUserID, 
    jenzcrp_rec.status_code EnrollmentType, 
    jenzcrp_rec.term_code GradePeriod
    from jenzcrp_rec
    join 
    jenzcrs_rec on jenzcrp_rec.course_code = jenzcrs_rec.course_code 
    and jenzcrp_rec.sec = jenzcrs_rec.sec 
    AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    join jenztrm_rec on jenztrm_rec.term_code = jenzcrs_rec.term_code
    --and trim(jenzcrs_rec.course_code) = 'NEU 675R  S (UG17)'
    where jenzcrs_rec.coursekey in (
    select 
    trim(jenzcrs_rec.coursekey) SecSchoolCode
    from jenzcrs_rec 
    join crs_rec on trim(jenzcrs_rec.course_code) = trim(crs_rec.crs_no)||' ('||trim(crs_rec.cat)||')'
    join jenztrm_rec on jenztrm_rec.term_code = jenzcrs_rec.term_code
    join jenzcrp_rec on jenzcrp_rec.course_code = jenzcrs_rec.course_code
    and jenzcrp_rec.sec = jenzcrs_rec.sec 
    AND jenzcrp_rec.term_code = jenzcrs_rec.term_code
    join id_rec on id_Rec.id = jenzcrp_rec.host_id
    where jenztrm_rec.start_date >= add_months(today,-1) and jenztrm_rec.end_date <= add_months(today,+5)
    --where jenztrm_rec.start_date < today and jenztrm_rec.end_date > today
    and jenzcrp_rec.status_code = '1PR'
    and id_rec.id in
    (select id from aa_rec
    where aa in ('EML1')
    and line1 in ('ahenle@carthage.edu', 'bcarlson1@carthage.edu', 'dbrownholland@carthage.edu', 'lchristoun@carthage.edu', 'apustina@carthage.edu',
    'adassow@carthage.edu', 'bzopf@carthage.edu', 'dcooksnyder@carthage.edu', 'ewheeler@carthage.edu', 'aduncan@carthage.edu',
    'jseymour@carthage.edu', 'ksconzert@carthage.edu', 'skonrad@carthage.edu', 'hyaple@carthage.edu',
    'lhuaracha@carthage.edu', 'npilarski@carthage.edu', 'jshields@carthage.edu', 'dschowalter@carthage.edu', 'abarnhart@carthage.edu',
    'fhicks@carthage.edu', 'cgrugel@carthage.edu', 'csabbar@carthage.edu')))
    order by coursecode
'''