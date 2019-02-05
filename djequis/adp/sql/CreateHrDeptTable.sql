
CREATE TABLE cx_sandbox:hrdept_table (
	hrdept char(4) NOT NULL,
	hrdiv char(4),
	descr char(32),
	beg_date date,
	end_date date
);
CREATE UNIQUE INDEX cx_sandbox:thrdept_prim ON hrdept_table (hrdept,hrdiv);

