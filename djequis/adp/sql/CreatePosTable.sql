DROP TABLE IF EXISTS `pos_table`;

CREATE TABLE pos_table (
    tpos_no integer NOT NULL,
    class_no integer DEFAULT 0,
    pcn_aggr varchar(40),
    pcn_01 varchar(3) NOT NULL,
    pcn_02 varchar(5) NOT NULL,
    pcn_03 varchar(5) NOT NULL,
    pcn_04 varchar(5) NOT NULL,
    descr varchar(32),
    ofc varchar(4),
    tcompplan_no integer DEFAULT 0,
    func_area varchar(4),
    bpos_no integer DEFAULT 0 NOT NULL,
    supervisor_no integer,
    eeo_code varchar(2),
    tsoc2010 varchar(7),
    tenure_track char(1),
    fte float DEFAULT 0.00,
    grp_pos char(1),
    max_jobs integer,
    hrpay varchar(3),
    assgn varchar(4),
    active_date date,
    inactive_date date,
    pseudo_serial integer,
    prev_pos varchar(8) NOT NULL,
    rank varchar(8),
    hradjexcl char(1)
);
CREATE INDEX tpos_key1 ON pos_table (prev_pos);
CREATE UNIQUE INDEX tpos_prim ON pos_table (tpos_no);