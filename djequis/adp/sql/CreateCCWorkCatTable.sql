DROP TABLE IF EXISTS `cc_work_cat_table`;

CREATE TABLE cc_work_cat_table (
    work_cat_code varchar(4) NOT NULL,
    work_cat_descr varchar(24),
    active_date date,
    inactive_date date
);
CREATE UNIQUE INDEX tcc_work_cat ON cc_work_cat_table (work_cat_code);