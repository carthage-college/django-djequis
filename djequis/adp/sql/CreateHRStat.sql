DROP TABLE IF EXISTS `hrstat_table`;

CREATE TABLE hrstat_table (
    hrstat varchar(4) NOT NULL,
    txt varchar(24),
    active_date date,
    inactive_date date
);
CREATE UNIQUE INDEX thrstat_prim ON hrstat_table (hrstat);