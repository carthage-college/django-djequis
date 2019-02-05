
CREATE TABLE cx_sandbox:hrpay_table (
	hrpay char(3) NOT NULL,
	txt char(24),
	prd char(2),
	subs char(4),
	def_hrs char(1),
	ck_frm char(14),
	ck_doc_code char(2),
	dirdep_frm char(14),
	dirdep_doc_code char(2),
	dirdep char(1),
	unempl_stat char(1),
	w2_frm char(14) NOT NULL,
	cks_per_yr integer,
	enable_web_time char(1),
	active_date date,
	inactive_date date,
	hr_start_date date
);

