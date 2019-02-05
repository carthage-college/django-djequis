
CREATE TABLE cx_sandbox:obj_table (
	obj char(5) NOT NULL,
	txt char(24),
	def_desc char(12),
	prim_resp_id integer,
	sec_resp_id integer,
	bgt_dsply char(1),
	active_date date,
	inactive_date date
);
CREATE UNIQUE INDEX cx_sandbox:tobj_obj ON obj_table (obj);

