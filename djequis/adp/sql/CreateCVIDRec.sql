DROP TABLE IF EXISTS `cvid_rec`;

CREATE TABLE cvid_rec (
    old_id varchar(20),
    old_id_num integer,
    adp_id varchar(20),
    ssn varchar(11),
    cx_id integer primary key DEFAULT 0 NOT NULL,
    cx_id_char varchar(15),
    ldap_name varchar(128),
    ldap_add_date date,
    adp_associate_id varchar(25)
);