DROP TABLE IF EXISTS `hrdiv_table`;

CREATE TABLE hrdiv_table (
    hrdiv varchar(4) NOT NULL,
    descr varchar(32),
    beg_date date,
    end_date date
);
CREATE UNIQUE INDEX thrdiv_prim ON hrdiv_table (hrdiv);