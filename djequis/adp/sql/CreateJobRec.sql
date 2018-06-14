DROP TABLE IF EXISTS `job_rec`;

CREATE TABLE job_rec (
    job_no integer NOT NULL,
    tpos_no integer,
    descr varchar(32),
    hrclass varchar(4),
    bjob_no integer,
    id integer DEFAULT 0,
    hrpay varchar(3),
    supervisor_no integer,
    hrstat varchar(4),
    pseudo_serial integer,
    egp_type char(1),
    hrdiv varchar(4),
    hrdept varchar(4),
    comp_beg_date date,
    comp_end_date date,
    app_inactive_date date,
    beg_date date,
    end_date date,
    active_ctrct char(1),
    ctrct_stat varchar(10),
    excl_srvc_hrs char(1) DEFAULT 'N',
    excl_web_time char(1) DEFAULT 'N',
    job_title varchar(255),
    job_title2 varchar(255),
    title_rank char(1)
);
CREATE INDEX job_key1 ON job_rec (hrpay);
CREATE INDEX job_key2 ON job_rec (id,hrpay,tpos_no,egp_type);
CREATE INDEX job_key3 ON job_rec (hrpay,id);
CREATE UNIQUE INDEX job_prim ON job_rec (job_no);