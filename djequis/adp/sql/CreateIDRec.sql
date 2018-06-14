DROP TABLE IF EXISTS `id_rec`;

CREATE TABLE id_rec (
    id integer PRIMARY KEY NOT NULL,
    prsp_no integer DEFAULT 0  NOT NULL,
    fullname varchar(32) NOT NULL,
    name_sndx varchar(4) NOT NULL,
    lastname varchar(50) NOT NULL,
    firstname varchar(32) NOT NULL,
    middlename varchar(32) NOT NULL,
    suffixname varchar(10) NOT NULL,
    addr_line1 varchar(64),
    addr_line2 varchar(64),
    addr_line3 varchar(64),
    city varchar(50),
    st varchar(2),
    zip varchar(10) NOT NULL,
    ctry varchar(3),
    aa varchar(4),
    title varchar(4),
    suffix varchar(4),
    ss_no varchar(11) NOT NULL,
    phone varchar(12),
    phone_ext varchar(4),
    prev_name_id integer,
    mail char(1),
    sol char(1),
    pub char(1),
    correct_addr char(1),
    decsd char(1),
    add_date date,
    ofc_add_by varchar(4),
    upd_date date,
    valid char(1),
    purge_date date,
    cass_cert_date date,
    cc_username varchar(250),
    cc_password varchar(250),
    inquiry_no integer
);