DROP TABLE IF EXISTS `profile_rec`;

CREATE TABLE profile_rec (
    id integer DEFAULT 0 NOT NULL,
    ethnic_code varchar(2),
    sex char(1) DEFAULT 'U',
    mrtl char(1),
    birth_date date,
    age smallint,
    birthplace_city varchar(24),
    birthplace_st varchar(2),
    birthplace_ctry varchar(3),
    res_st varchar(2),
    res_cty varchar(4),
    citz varchar(4),
    visa_code varchar(4),
    prof_visa_date date,
    prof_visa_no varchar(10),
    res_ctry varchar(3),
    vet char(1) DEFAULT 'N',
    handicap_code varchar(2),
    denom_code varchar(4),
    church_id integer DEFAULT 0 NOT NULL,
    occ varchar(4),
    news1_id integer,
    news2_id integer,
    prof_last_upd_date date,
    lang char(1) DEFAULT 'Y',
    prof_res_code varchar(5),
    prof_res_date date,
    prof_vet_chap varchar(4),
    grp_no smallint,
    priv_code varchar(4),
    decsd_date date,
    milit_code varchar(8),
    milit_rank varchar(4),
    photo varchar(768),
    race varchar(2),
    hispanic char(1),
    confirm_date date
);
CREATE INDEX profile_birth_date ON profile_rec (birth_date);
CREATE INDEX profile_church_id ON profile_rec (church_id);
CREATE UNIQUE INDEX profile_id ON profile_rec (id);