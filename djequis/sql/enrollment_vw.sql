-- Grab enrollemnt data from the jenz mirror table, jenzcrp_rec.
-- Retrieve basic elements of data that can then be re-assembled as needed by downstream systems such as Schoology and Courseval.
select to_number(substr(jcp.term_code,4,4)) as year,
       substr(jcp.term_code,1,2) as sess, 
       substr(jcp.course_code,charindex('(',jcp.course_code)+1,4) as catalog,
       right(trim(jcp.term_code),4) as program,
       substr(jcp.course_code,1,charindex('(',jcp.course_code)-1) as course_no,
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
