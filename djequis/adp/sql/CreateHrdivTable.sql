
CREATE TABLE cx_sandbox:hrdiv_table (
	hrdiv char(4) NOT NULL,
	descr char(32),
	beg_date date,
	end_date date
);
CREATE UNIQUE INDEX cx_sandbox:thrdiv_prim ON hrdiv_table (hrdiv);

