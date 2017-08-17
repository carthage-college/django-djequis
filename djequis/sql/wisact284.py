def getaid(dispersed):
    if dispersed:
        amt_stat_values = ("'AD'")
    else:
        amt_stat_values = ("'AA','AD','AP','EA'")
        # SQL for Wisconsin ACT 284
        WIS_ACT_284_SQL = '''
            select distinct
                '00383900' AS OPEID,
                '20' || left(T1.fa_yr, 2) || '-20' || right(T1.fa_yr, 2) as AcadYear,
                REPLACE(ID_Record.ss_no, '-', '') as Social_Security_Number,
                TRIM(ID_Record.firstname) as Student_First_Name,
                TRIM(ID_Record.lastname) as Student_Last_Name,
                T1.id as Student_ID_Number,
                TRIM(ID_Record.addr_line1) as Student_Address_Line_1,
                TRIM(ID_Record.addr_line2) as Student_Address_Line_2,
                TRIM(ID_Record.addr_line3) as Student_Address_Line_3,
                TRIM(ID_Record.city) as Student_City,
                TRIM(ID_Record.st) as Student_State_Code,
                TRIM(ID_Record.zip) as Student_Postal_Code,
                TRIM(ID_Record.ctry) as Student_Country_Code,
                TRIM(Alternate_Address_Record.line1) as Student_email,
                TRIM(T1.aid) as Aid_Code,
                TRIM(Aid_Record_Aid_Table.txt) as Loan_name,
                SUM(T1.amt) as Aid_Amount,
                AidOther.c_InstGrants,
                AidOther.c_InstScholar,
                AidOther.c_FedGrants,
                AidOther.c_SteGrants,
                AidOther.c_OutsideAid,
                CAST(YEAR(loan_rec.beg_date) AS VARCHAR(4)) ||
                case  when MONTH(loan_rec.beg_date)<10 then '0' ||
                CAST(MONTH(loan_rec.beg_date) AS VARCHAR(2)) else
                CAST(MONTH(loan_rec.beg_date) AS VARCHAR(2)) end ||
                case  when DAY(loan_rec.beg_date)<10 then '0' ||
                CAST(DAY(loan_rec.beg_date) AS VARCHAR(2)) else
                CAST(DAY(loan_rec.beg_date) AS VARCHAR(2)) end  as Loan_Date,
                BudgetSummary.c_TUFE,
                BudgetSummary.c_RMBD,
                BudgetSummary.c_BOOK,
                BudgetSummary.c_TRAN,
                BudgetSummary.c_MISC,
                BudgetSummary.c_LOAN
            from aid_rec T1 inner join aid_table Aid_Record_Aid_Table on T1.aid = Aid_Record_Aid_Table.aid
             inner join
            (select distinct
                Aid_Record.id as Student_ID_Number,
                SUM(case when ((Aid_Record_Aid_Table.txt like '%Grant%') and (Aid_Record_Aid_Table.frm_code in ('INSF','INSU','PCAR','PMRT','PCEI'))) then Aid_Record.amt else 0 end) as c_InstGrants,
                SUM(case when ((not (Aid_Record_Aid_Table.txt like '%Grant%')) and (Aid_Record_Aid_Table.frm_code in ('INSF','INSU','PCAR','PMRT','PCEI'))) then Aid_Record.amt else 0 end) as c_InstScholar,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('PFGR')) then Aid_Record.amt else 0 end) as c_FedGrants,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('PSGR')) then Aid_Record.amt else 0 end) as c_SteGrants,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('POUT')) then Aid_Record.amt else 0 end) as c_OutsideAid
            from
                aid_rec Aid_Record,
                aid_table Aid_Record_Aid_Table
            where
                (Aid_Record.id > 0) and
                (Aid_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                   ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                    END) and
                (Aid_Record.stat in ('A')) and
                (Aid_Record.amt_stat in ({0})) and
                (Aid_Record.amt > 0) and
                (Aid_Record.aid = Aid_Record_Aid_Table.aid)
            group by Student_ID_Number) AidOther on T1.id = AidOther.Student_ID_Number
                left join loandisb_rec on T1.aid_no = loandisb_rec.aid_no
                left join loan_rec on loandisb_rec.loan_no = loan_rec.loan_no
                left join
                    (select distinct
                    case when NOIM.id_number is not null then NOIM.id_number else IM.id_number end as id_number,
                    case when NOIM.budget_code is not null then NOIM.budget_code else IM.budget_code end as budget_code,
                    case when NOIM.c_TUFE is not null then NOIM.c_TUFE else IM.c_TUFE end as c_TUFE,
                    case when NOIM.c_RMBD is not null then NOIM.c_RMBD else IM.c_RMBD end as c_RMBD,
                    case when NOIM.c_BOOK is not null then NOIM.c_BOOK else IM.c_BOOK end as c_BOOK,
                    case when NOIM.c_TRAN is not null then NOIM.c_TRAN else IM.c_TRAN end as c_TRAN,
                    case when NOIM.c_MISC is not null then NOIM.c_MISC else IM.c_MISC end as c_MISC,
                    case when NOIM.c_LOAN is not null then NOIM.c_LOAN else IM.c_LOAN end as c_LOAN
            from
                (select header.id_number, header.budget_code,
                sum(detail.c_TUFE) as c_TUFE, sum(detail.c_RMBD) as c_RMBD,
                sum(detail.c_BOOK) as c_BOOK, sum(detail.c_TRAN) as c_TRAN,
                sum(detail.c_MISC) as c_MISC, sum(detail.c_LOAN) as c_LOAN
            from
                (select distinct
                Financial_Aid_Budget_Record.fabgt_no as FA_Budget_Number,
                Financial_Aid_Budget_Record.bgt_code as Budget_Code,
                Financial_Aid_Budget_Record.id as ID_Number
            from
                fabgt_rec Financial_Aid_Budget_Record
            where Financial_Aid_Budget_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                     ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                      END
            and Financial_Aid_Budget_Record.bgt_code = 'TRAD IM') as header
            inner join
            (select distinct
                T1.fabgt_no as FA_Budget_Number,
                SUM(case when (T1.faitem = 'TUFE') then T1.amt else 0 end) as c_TUFE,
                SUM(case when (T1.faitem = 'RMBD') then T1.amt else 0 end) as c_RMBD,
                SUM(case when (T1.faitem = 'BOOK') then T1.amt else 0 end) as c_BOOK,
                SUM(case when (T1.faitem = 'TRAN') then T1.amt else 0 end) as c_TRAN,
                SUM(case when (T1.faitem = 'MISC') then T1.amt else 0 end) as c_MISC,
                SUM(case when (T1.faitem = 'LOAN') then T1.amt else 0 end) as c_LOAN
            from 
                fabgtdtl_rec T1
                group by FA_Budget_Number) as detail on header.fa_budget_number = detail.fa_budget_number
                group by header.id_number, header.budget_code) IM 
            full join
            (select header.id_number, header.budget_code, sum(detail.c_TUFE) as c_TUFE,
                sum(detail.c_RMBD) as c_RMBD, sum(detail.c_BOOK) as c_BOOK,
                sum(detail.c_TRAN) as c_TRAN, sum(detail.c_MISC) as c_MISC,
                sum(detail.c_LOAN) as c_LOAN
            from
            (select distinct
                Financial_Aid_Budget_Record.fabgt_no as FA_Budget_Number,
                Financial_Aid_Budget_Record.bgt_code as Budget_Code,
                Financial_Aid_Budget_Record.id as ID_Number
            from 
                fabgt_rec Financial_Aid_Budget_Record
                where Financial_Aid_Budget_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                         ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                          END
                and Financial_Aid_Budget_Record.bgt_code <> 'TRAD IM') as header
            inner join
            (select distinct
                T1.fabgt_no as FA_Budget_Number,
                SUM(case when (T1.faitem = 'TUFE') then T1.amt else 0 end) as c_TUFE,
                SUM(case when (T1.faitem = 'RMBD') then T1.amt else 0 end) as c_RMBD,
                SUM(case when (T1.faitem = 'BOOK') then T1.amt else 0 end) as c_BOOK,
                SUM(case when (T1.faitem = 'TRAN') then T1.amt else 0 end) as c_TRAN,
                SUM(case when (T1.faitem = 'MISC') then T1.amt else 0 end) as c_MISC,
                SUM(case when (T1.faitem = 'LOAN') then T1.amt else 0 end) as c_LOAN
            from 
                fabgtdtl_rec T1
            group by FA_Budget_Number) as detail on header.fa_budget_number = detail.fa_budget_number
            group by header.id_number, header.budget_code) NOIM on NOIM.id_number = IM.id_number)
               BudgetSummary on T1.id = BudgetSummary.id_number
            inner join aa_rec Alternate_Address_Record on T1.id = Alternate_Address_Record.id
            inner join id_rec ID_Record on T1.id = ID_Record.id
                where
                    (T1.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                               ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                END) and
                    (T1.stat in ('A')) and
                    (T1.amt_stat in ({0})) and
                    (T1.amt > 0) and
                    (Aid_Record_Aid_Table.dsl_loan_type = 'AL') and
                    (Alternate_Address_Record.aa = 'EML1')
                group by 
                    T1.id,
                    T1.aid,
                    Aid_Record_Aid_Table.txt,
                    Loan_Date,
                    BudgetSummary.c_TUFE, BudgetSummary.c_RMBD, BudgetSummary.c_BOOK,
                    BudgetSummary.c_TRAN, BudgetSummary.c_MISC, BudgetSummary.c_LOAN,
                    Student_email,
                    Social_Security_Number,
                    Student_First_Name,
                    Student_Last_Name,
                    Student_Address_Line_1,
                    Student_Address_Line_2,
                    Student_Address_Line_3,
                    Student_City,
                    Student_State_Code,
                    Student_Postal_Code,
                    Student_Country_Code,
                    AidOther.c_InstGrants,
                    AidOther.c_InstScholar,
                    AidOther.c_FedGrants,
                    AidOther.c_SteGrants,
                    AidOther.c_OutsideAid,
                    AcadYear
            order by t1.id
        '''.format(amt_stat_values)
        return WIS_ACT_284_SQL

def getaidcount(dispersed):
    if dispersed:
        amt_stat_values = ("'AD'")
    else:
        amt_stat_values = ("'AA','AD','AP','EA'")
        # SQL to get the highest number of loans
        MAX_LOANS_SQL = '''
            select student_id_number, count(loan_name) as number_of_loans
            from (
                select distinct
                '00383900' AS OPEID,
                '20' || left(T1.fa_yr, 2) || '-20' || right(T1.fa_yr, 2) as AcadYear,
                REPLACE(ID_Record.ss_no, '-', '') as Social_Security_Number,
                TRIM(ID_Record.firstname) as Student_First_Name,
                TRIM(ID_Record.lastname) as Student_Last_Name,
                T1.id as Student_ID_Number,
                TRIM(ID_Record.addr_line1) as Student_Address_Line_1,
                TRIM(ID_Record.addr_line2) as Student_Address_Line_2,
                TRIM(ID_Record.addr_line3) as Student_Address_Line_3,
                TRIM(ID_Record.city) as Student_City,
                TRIM(ID_Record.st) as Student_State_Code,
                TRIM(ID_Record.zip) as Student_Postal_Code,
                TRIM(ID_Record.ctry) as Student_Country_Code,
                TRIM(Alternate_Address_Record.line1) as Student_email,
                TRIM(T1.aid) as Aid_Code,
                TRIM(Aid_Record_Aid_Table.txt) as Loan_name,
                SUM(T1.amt) as Aid_Amount,
                AidOther.c_InstGrants,
                AidOther.c_InstScholar,
                AidOther.c_FedGrants,
                AidOther.c_SteGrants,
                AidOther.c_OutsideAid,
                CAST(YEAR(loan_rec.beg_date) AS VARCHAR(4)) ||
                case  when MONTH(loan_rec.beg_date)<10 then '0' ||
                CAST(MONTH(loan_rec.beg_date) AS VARCHAR(2)) else
                CAST(MONTH(loan_rec.beg_date) AS VARCHAR(2)) end ||
                case  when DAY(loan_rec.beg_date)<10 then '0' ||
                CAST(DAY(loan_rec.beg_date) AS VARCHAR(2)) else
                CAST(DAY(loan_rec.beg_date) AS VARCHAR(2)) end  as Loan_Date,
                BudgetSummary.c_TUFE,
                BudgetSummary.c_RMBD,
                BudgetSummary.c_BOOK,
                BudgetSummary.c_TRAN,
                BudgetSummary.c_MISC,
                BudgetSummary.c_LOAN
            from aid_rec T1 inner join aid_table Aid_Record_Aid_Table on T1.aid = Aid_Record_Aid_Table.aid
             inner join
            (select distinct
                Aid_Record.id as Student_ID_Number,
                SUM(case when ((Aid_Record_Aid_Table.txt like '%Grant%') and (Aid_Record_Aid_Table.frm_code in ('INSF','INSU','PCAR','PMRT','PCEI'))) then Aid_Record.amt else 0 end) as c_InstGrants,
                SUM(case when ((not (Aid_Record_Aid_Table.txt like '%Grant%')) and (Aid_Record_Aid_Table.frm_code in ('INSF','INSU','PCAR','PMRT','PCEI'))) then Aid_Record.amt else 0 end) as c_InstScholar,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('PFGR')) then Aid_Record.amt else 0 end) as c_FedGrants,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('PSGR')) then Aid_Record.amt else 0 end) as c_SteGrants,
                SUM(case when (Aid_Record_Aid_Table.frm_code in ('POUT')) then Aid_Record.amt else 0 end) as c_OutsideAid
            from
                aid_rec Aid_Record,
                aid_table Aid_Record_Aid_Table
            where
                (Aid_Record.id > 0) and
                (Aid_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                   ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                    END) and
                (Aid_Record.stat in ('A')) and
                (Aid_Record.amt_stat in ({0})) and
                (Aid_Record.amt > 0) and
                (Aid_Record.aid = Aid_Record_Aid_Table.aid)
            group by Student_ID_Number) AidOther on T1.id = AidOther.Student_ID_Number
                left join loandisb_rec on T1.aid_no = loandisb_rec.aid_no
                left join loan_rec on loandisb_rec.loan_no = loan_rec.loan_no
                left join
                    (select distinct
                    case when NOIM.id_number is not null then NOIM.id_number else IM.id_number end as id_number,
                    case when NOIM.budget_code is not null then NOIM.budget_code else IM.budget_code end as budget_code,
                    case when NOIM.c_TUFE is not null then NOIM.c_TUFE else IM.c_TUFE end as c_TUFE,
                    case when NOIM.c_RMBD is not null then NOIM.c_RMBD else IM.c_RMBD end as c_RMBD,
                    case when NOIM.c_BOOK is not null then NOIM.c_BOOK else IM.c_BOOK end as c_BOOK,
                    case when NOIM.c_TRAN is not null then NOIM.c_TRAN else IM.c_TRAN end as c_TRAN,
                    case when NOIM.c_MISC is not null then NOIM.c_MISC else IM.c_MISC end as c_MISC,
                    case when NOIM.c_LOAN is not null then NOIM.c_LOAN else IM.c_LOAN end as c_LOAN
            from
                (select header.id_number, header.budget_code,
                sum(detail.c_TUFE) as c_TUFE, sum(detail.c_RMBD) as c_RMBD,
                sum(detail.c_BOOK) as c_BOOK, sum(detail.c_TRAN) as c_TRAN,
                sum(detail.c_MISC) as c_MISC, sum(detail.c_LOAN) as c_LOAN
            from
                (select distinct
                Financial_Aid_Budget_Record.fabgt_no as FA_Budget_Number,
                Financial_Aid_Budget_Record.bgt_code as Budget_Code,
                Financial_Aid_Budget_Record.id as ID_Number
            from
                fabgt_rec Financial_Aid_Budget_Record
            where Financial_Aid_Budget_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                     ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                      END
            and Financial_Aid_Budget_Record.bgt_code = 'TRAD IM') as header
            inner join
            (select distinct
                T1.fabgt_no as FA_Budget_Number,
                SUM(case when (T1.faitem = 'TUFE') then T1.amt else 0 end) as c_TUFE,
                SUM(case when (T1.faitem = 'RMBD') then T1.amt else 0 end) as c_RMBD,
                SUM(case when (T1.faitem = 'BOOK') then T1.amt else 0 end) as c_BOOK,
                SUM(case when (T1.faitem = 'TRAN') then T1.amt else 0 end) as c_TRAN,
                SUM(case when (T1.faitem = 'MISC') then T1.amt else 0 end) as c_MISC,
                SUM(case when (T1.faitem = 'LOAN') then T1.amt else 0 end) as c_LOAN
            from 
                fabgtdtl_rec T1
                group by FA_Budget_Number) as detail on header.fa_budget_number = detail.fa_budget_number
                group by header.id_number, header.budget_code) IM 
            full join
            (select header.id_number, header.budget_code, sum(detail.c_TUFE) as c_TUFE,
                sum(detail.c_RMBD) as c_RMBD, sum(detail.c_BOOK) as c_BOOK,
                sum(detail.c_TRAN) as c_TRAN, sum(detail.c_MISC) as c_MISC,
                sum(detail.c_LOAN) as c_LOAN
            from
            (select distinct
                Financial_Aid_Budget_Record.fabgt_no as FA_Budget_Number,
                Financial_Aid_Budget_Record.bgt_code as Budget_Code,
                Financial_Aid_Budget_Record.id as ID_Number
            from 
                fabgt_rec Financial_Aid_Budget_Record
                where Financial_Aid_Budget_Record.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                                                         ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                                          END
                and Financial_Aid_Budget_Record.bgt_code <> 'TRAD IM') as header
            inner join
            (select distinct
                T1.fabgt_no as FA_Budget_Number,
                SUM(case when (T1.faitem = 'TUFE') then T1.amt else 0 end) as c_TUFE,
                SUM(case when (T1.faitem = 'RMBD') then T1.amt else 0 end) as c_RMBD,
                SUM(case when (T1.faitem = 'BOOK') then T1.amt else 0 end) as c_BOOK,
                SUM(case when (T1.faitem = 'TRAN') then T1.amt else 0 end) as c_TRAN,
                SUM(case when (T1.faitem = 'MISC') then T1.amt else 0 end) as c_MISC,
                SUM(case when (T1.faitem = 'LOAN') then T1.amt else 0 end) as c_LOAN
            from 
                fabgtdtl_rec T1
            group by FA_Budget_Number) as detail on header.fa_budget_number = detail.fa_budget_number
            group by header.id_number, header.budget_code) NOIM on NOIM.id_number = IM.id_number)
               BudgetSummary on T1.id = BudgetSummary.id_number
            inner join aa_rec Alternate_Address_Record on T1.id = Alternate_Address_Record.id
            inner join id_rec ID_Record on T1.id = ID_Record.id
                where
                    (T1.fa_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d') THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                               ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                                END) and
                    (T1.stat in ('A')) and
                    (T1.amt_stat in ({0})) and
                    (T1.amt > 0) and
                    (Aid_Record_Aid_Table.dsl_loan_type = 'AL') and
                    (Alternate_Address_Record.aa = 'EML1')
                group by 
                    T1.id,
                    T1.aid,
                    Aid_Record_Aid_Table.txt,
                    Loan_Date,
                    BudgetSummary.c_TUFE, BudgetSummary.c_RMBD, BudgetSummary.c_BOOK,
                    BudgetSummary.c_TRAN, BudgetSummary.c_MISC, BudgetSummary.c_LOAN,
                    Student_email,
                    Social_Security_Number,
                    Student_First_Name,
                    Student_Last_Name,
                    Student_Address_Line_1,
                    Student_Address_Line_2,
                    Student_Address_Line_3,
                    Student_City,
                    Student_State_Code,
                    Student_Postal_Code,
                    Student_Country_Code,
                    AidOther.c_InstGrants,
                    AidOther.c_InstScholar,
                    AidOther.c_FedGrants,
                    AidOther.c_SteGrants,
                    AidOther.c_OutsideAid,
                    AcadYear
            order by t1.id
            ) alldata
            group by student_id_number
            order by number_of_loans desc
        '''.format(amt_stat_values)
        return MAX_LOANS_SQL