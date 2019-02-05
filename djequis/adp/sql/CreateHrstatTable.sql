
CREATE TABLE cx_sandbox:hrstat_table (
	hrstat char(4) NOT NULL,
	txt char(24),
	active_date date,
	inactive_date date
);
CREATE UNIQUE INDEX cx_sandbox:thrstat_prim ON hrstat_table (hrstat);

