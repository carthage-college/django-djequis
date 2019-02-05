
CREATE TABLE cx_sandbox:id_rec (
	id serial NOT NULL,
	prsp_no integer DEFAULT 0                                                                                                                                                                                                                                                               NOT NULL,
	fullname char(32) NOT NULL,
	name_sndx char(4) NOT NULL,
	lastname char(50) NOT NULL,
	firstname char(32) NOT NULL,
	middlename char(32) NOT NULL,
	suffixname char(10) NOT NULL,
	addr_line1 char(64),
	addr_line2 char(64),
	addr_line3 char(64),
	city char(50),
	st char(2),
	zip char(10) NOT NULL,
	ctry char(3),
	aa char(4),
	title char(4),
	suffix char(4),
	ss_no char(11) NOT NULL,
	phone char(12),
	phone_ext char(4),
	prev_name_id integer,
	mail char(1),
	sol char(1),
	pub char(1),
	correct_addr char(1),
	decsd char(1),
	add_date date,
	ofc_add_by char(4),
	upd_date date,
	valid char(1),
	purge_date date,
	cass_cert_date date,
	cc_username char(250),
	cc_password char(250),
	inquiry_no integer DEFAULT 0                                                                                                                                                                                                                                                               NOT NULL,
	PRIMARY KEY (id)
);
CREATE INDEX cx_sandbox:id_addr_line1 ON id_rec (addr_line1);
CREATE INDEX cx_sandbox:id_firstname ON id_rec (firstname);
CREATE INDEX cx_sandbox:id_fullname ON id_rec (fullname);
CREATE INDEX cx_sandbox:id_key1 ON id_rec (name_sndx,fullname);
CREATE INDEX cx_sandbox:id_lastname ON id_rec (lastname);
CREATE INDEX cx_sandbox:id_middlename ON id_rec (middlename);
CREATE INDEX cx_sandbox:id_prsp_no ON id_rec (prsp_no);
CREATE INDEX cx_sandbox:id_ss_no ON id_rec (ss_no);
CREATE INDEX cx_sandbox:id_valid ON id_rec (valid);
CREATE INDEX cx_sandbox:id_zip ON id_rec (zip);

