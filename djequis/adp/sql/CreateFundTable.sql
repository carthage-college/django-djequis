
CREATE TABLE cx_sandbox:fund_table (
	fund char(1) NOT NULL,
	txt char(24),
	def_desc char(12),
	prim_resp_id integer,
	sec_resp_id integer,
	upd_date date,
	bgt_dsply char(1),
	active_date date,
	inactive_date date
);
CREATE UNIQUE INDEX cx_sandbox:tfund_fund ON fund_table (fund);

