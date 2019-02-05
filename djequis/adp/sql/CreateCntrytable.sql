

CREATE TABLE cx_sandbox:ctry_table (
	ctry char(3) NOT NULL,
	txt char(25),
	ctry_code char(2) NOT NULL,
	usps_code char(2) NOT NULL,
	active_date date,
	inactive_date date,
	web_ord smallint DEFAULT 99                                                                                                                                                                                                                                                              NOT NULL,
	web_display char(1)
);
CREATE UNIQUE INDEX cx_sandbox:tctry_ctry ON ctry_table (ctry);
CREATE INDEX cx_sandbox:tctry_usps_code ON ctry_table (usps_code);

