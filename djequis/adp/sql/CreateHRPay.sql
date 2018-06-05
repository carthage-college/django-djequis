DROP TABLE IF EXISTS `hrpay_table`;

CREATE TABLE hrpay_table (
    hrpay varchar(3) NOT NULL,
    txt varchar(24),
    prd varchar(2),
    subs varchar(4),
    def_hrs char(1),
    ck_frm varchar(14),
    ck_doc_code varchar(2),
    dirdep_frm varchar(14),
    dirdep_doc_code varchar(2),
    dirdep char(1),
    unempl_stat char(1),
    w2_frm varchar(14) NOT NULL,
    cks_per_yr integer,
    enable_web_time char(1),
    active_date date,
    inactive_date date,
    hr_start_date date
);
CREATE UNIQUE INDEX thrpay_prim ON hrpay_table (hrpay);