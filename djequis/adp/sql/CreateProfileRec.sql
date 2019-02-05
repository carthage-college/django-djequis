
CREATE TABLE cx_sandbox:profile_rec (
	id integer NOT NULL,
	ethnic_code char(2),
	sex char(1),
	mrtl char(1),
	birth_date date,
	age smallint,
	birthplace_city char(24),
	birthplace_st char(2),
	birthplace_ctry char(3),
	res_st char(2),
	res_cty char(4),
	citz char(4),
	visa_code char(4),
	prof_visa_date date,
	prof_visa_no char(10),
	res_ctry char(3),
	vet char(1),
	handicap_code char(2),
	denom_code char(4),
	church_id integer,
	occ char(4),
	news1_id integer,
	news2_id integer,
	prof_last_upd_date date,
	lang char(1),
	prof_res_code char(5),
	prof_res_date date,
	prof_vet_chap char(4),
	grp_no smallint,
	priv_code char(4),
	decsd_date date,
	milit_code char(8),
	milit_rank char(4),
	photo byte(2147483647),
	race char(2),
	hispanic char(1),
	confirm_date date
);
CREATE INDEX cx_sandbox:profile_birth_date ON profile_rec (birth_date);
CREATE INDEX cx_sandbox:profile_church_id ON profile_rec (church_id);
CREATE UNIQUE INDEX cx_sandbox:profile_id ON profile_rec (id);

