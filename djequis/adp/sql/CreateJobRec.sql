
CREATE TABLE cx_sandbox:job_rec (
	job_no serial NOT NULL,
	tpos_no integer,
	descr char(32),
	hrclass char(4),
	bjob_no integer,
	id integer DEFAULT 0                                                                                                                                                                                                                                                              ,
	hrpay char(3),
	supervisor_no integer,
	reports_to integer,
	hrstat char(4),
	pseudo_serial integer,
	egp_type char(1),
	hrdiv char(4),
	hrdept char(4),
	comp_beg_date date,
	comp_end_date date,
	app_inactive_date date,
	beg_date date,
	end_date date,
	active_ctrct char(1),
	ctrct_stat char(10),
	excl_srvc_hrs char(1),
	excl_web_time char(1),
	job_title char(255),
	title_rank char(1),
	worker_ctgry char(4)
);
CREATE INDEX cx_sandbox:job_key1 ON job_rec (hrpay);
CREATE INDEX cx_sandbox:job_key2 ON job_rec (id,hrpay,tpos_no,egp_type);
CREATE INDEX cx_sandbox:job_key3 ON job_rec (hrpay,id);
CREATE UNIQUE INDEX cx_sandbox:job_prim ON job_rec (job_no);

