
CREATE TABLE cx_sandbox:dept_table (
	dept char(4) NOT NULL,
	txt char(24),
	div char(4) NOT NULL,
	head_id integer,
	active_date date,
	inactive_date date,
	web_display char(1)
);
CREATE UNIQUE INDEX cx_sandbox:tdept_dept ON dept_table (dept);
CREATE INDEX cx_sandbox:tdept_div ON dept_table (div);

