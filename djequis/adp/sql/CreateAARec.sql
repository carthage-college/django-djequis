DROP TABLE IF EXISTS `aa_rec`;

CREATE TABLE aa_rec (
    id integer DEFAULT 0 NOT NULL,
    aa varchar(4) NOT NULL,
    beg_date date NOT NULL,
    end_date date,
    peren char(1),
    line1 varchar(64),
    line2 varchar(64),
    line3 varchar(64),
    city varchar(50),
    st varchar(2),
    zip varchar(10),
    ctry varchar(3),
    phone varchar(12),
    phone_ext varchar(4),
    ofc_add_by varchar(4),
    cass_cert_date date,
    aa_no integer NOT NULL,
    cell_carrier varchar(4),
    opt_out char(1),
    PRIMARY KEY (aa_no)
);
CREATE INDEX aa_id ON aa_rec (id);
CREATE INDEX aa_line1 ON aa_rec (line1);
CREATE UNIQUE INDEX aa_prim ON aa_rec (id,aa,beg_date);
CREATE INDEX aa_zip ON aa_rec (zip);