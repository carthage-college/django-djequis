DROP TABLE IF EXISTS `func_table`;

CREATE TABLE func_table (
    func varchar(3) NOT NULL,
    txt varchar(24),
    def_desc varchar(12),
    prim_resp_id integer,
    sec_resp_id integer,
    bgt_dsply char(1),
    active_date date,
    inactive_date date
);
CREATE UNIQUE INDEX tfunc_func ON func_table (func);