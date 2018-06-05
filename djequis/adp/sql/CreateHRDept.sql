DROP TABLE IF EXISTS `hrdept_table`;

CREATE TABLE hrdept_table (
    hrdept varchar(4) NOT NULL,
    hrdiv varchar(4),
    descr varchar(32),
    beg_date date,
    end_date date
);
CREATE UNIQUE INDEX thrdept_prim ON hrdept_table (hrdept,hrdiv);