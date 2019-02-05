
CREATE TABLE cx_sandbox:pos_table (
	tpos_no serial NOT NULL,
	class_no integer DEFAULT 0                                                                                                                                                                                                                                                              ,
	pcn_aggr char(40),
	pcn_01 char(3) NOT NULL,
	pcn_02 char(5) NOT NULL,
	pcn_03 char(5) NOT NULL,
	pcn_04 char(5) NOT NULL,
	descr char(32),
	ofc char(4),
	tcompplan_no integer DEFAULT 0                                                                                                                                                                                                                                                              ,
	func_area char(4),
	bpos_no integer DEFAULT 0                                                                                                                                                                                                                                                               NOT NULL,
	supervisor_no integer,
	eeo_code char(2),
	tsoc2010 char(7),
	tenure_track char(1),
	fte float DEFAULT 0.00                                                                                                                                                                                                                                                           ,
	grp_pos char(1),
	max_jobs integer,
	hrpay char(3),
	assgn char(4),
	active_date date,
	inactive_date date,
	pseudo_serial integer,
	prev_pos char(8) NOT NULL,
	rank char(8),
	hradjexcl char(1)
);
CREATE INDEX cx_sandbox:tpos_key1 ON pos_table (prev_pos);
CREATE UNIQUE INDEX cx_sandbox:tpos_prim ON pos_table (tpos_no);

