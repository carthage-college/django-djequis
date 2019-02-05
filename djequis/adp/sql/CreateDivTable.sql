
CREATE TABLE cx_sandbox:div_table (
	div char(4) NOT NULL,
	txt char(24),
	head_id integer,
	active_date date,
	inactive_date date
);
CREATE UNIQUE INDEX cx_sandbox:tdiv_div ON div_table (div);

