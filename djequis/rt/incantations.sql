-----------------------------------------------------
-- Users 1: remove carthage.edu from users.name
-----------------------------------------------------

-- Original MS Access SQL
-- ANSI/ISO SQL for MySQL is the same as MS Access SQL here
UPDATE
    Users
SET
    Users.Name = Left(Users.Name, InStr(Users.Name,"@car")-1)
WHERE
    ((Users.Name Like "%@carthage.edu") AND (Users.id Not In (449,455)));

-- Equivalent SELECT statement
SELECT
    Users.name, Left( Users.Name, InStr(Users.Name,'@car') -1 )
FROM
    Users
WHERE
    ((Users.Name Like '%@carthage.edu') AND (Users.id Not In (449,455)));

-----------------------------------------------------
-- Users 2: update email address if need be
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Users
SET
    Users.EmailAddress = Trim([Name]) & IIf(InStr(1,[EmailAddress],"@",0)>0,"","@carthage.edu")
WHERE
    (
        (Users.EmailAddress Not Like "*@*")
        AND
        (Users.id>12 And Users.id Not In (1,6,93,449,455,707))
        AND
        ((Users.Name Not Like "*carthage*") OR (Users.EmailAddress Is Null))
    );

-- ANSI/ISO SQL for MySQL
UPDATE
    Users
SET
    Users.EmailAddress = Users.Name
    -- & IIf(InStr(1,[EmailAddress],"@",0)>0,"","@carthage.edu")
    -- Not certain if you can do this in standard SQL
WHERE
    (
        ((Users.EmailAddress Not Like '%@%') OR (Users.EmailAddress Is Null))
        AND
        (Users.id>12 And Users.id Not In (1,6,93,449,455,707))
        AND
        (Users.Name Like '%carthage%')
    );

-- Equivalent SELECT statement
SELECT
    Users.id, Users.name, Users.EmailAddress, InStr(EmailAddress,'@')
FROM
    Users
WHERE
    (
        ((Users.EmailAddress Not Like '%@%') OR (Users.EmailAddress Is Null))
        AND
        (Users.id>12 And Users.id Not In (1,6,93,449,455,707))
        AND
        (Users.Name Like '%carthage%')
    );

-----------------------------------------------------
-- Tickets 1: update TimeEstimated
-- iif ( condition, value_if_true, value_if_false )
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Tickets
SET
    Tickets.TimeEstimated = Tickets.TimeWorked + Tickets.TimeLeft + 1
WHERE (
    (Tickets.Status In ('open (Unchanged)','open','new','stalled'))
AND
    (
        (
            IIf (
                Tickets.TimeEstimated=0 Or Tickets.TimeEstimated < Tickets.TimeWorked + Tickets.TimeLeft,"DoIt","Skip"
            )
        )="DoIt"
    )
AND
    (Tickets.Type <> "reminder")
);

-- ANSI/ISO SQL for MySQL
UPDATE
    Tickets
SET
    Tickets.TimeEstimated = Tickets.TimeWorked + Tickets.TimeLeft + 1
WHERE (
    (Tickets.Status In ('open (Unchanged)','open','new','stalled'))
AND
    -- (
    --    (
    --        IIf (
    --            Tickets.TimeEstimated=0 Or Tickets.TimeEstimated < Tickets.TimeWorked + Tickets.TimeLeft,"DoIt","Skip"
    --        )
    --    )="DoIt"
    -- )
    -- Not certain if you can do this in standard SQL
AND
    (Tickets.Type <> "reminder")
);

-- Equivalent SELECT statement
SELECT
    Tickets.TimeWorked,
    Tickets.TimeLeft,
    Tickets.TimeWorked + Tickets.TimeLeft + 1 as TicketsTimeEstimated,
    Tickets.TimeEstimated
FROM
    Tickets
WHERE (
    (Tickets.Status In ('open (Unchanged)','open','new','stalled'))
AND
    (Tickets.Type <> 'reminder')
AND
    (Tickets.TimeEstimated = 0 OR Tickets.TimeEstimated < (Tickets.TimeWorked + Tickets.TimeLeft))
);

-----------------------------------------------------
-- Tickets 2: update TimeLeft
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Tickets
SET
    Tickets.TimeLeft = [TimeEstimated]-[TimeWorked]
WHERE
    Tickets.Status In ("open (Unchanged)","open","new","stalled")
AND
    Tickets.Type <> "reminder";

-- ANSI/ISO SQL for MySQL
UPDATE
    Tickets
SET
    Tickets.TimeLeft = Tickets.TimeEstimated - Tickets.TimeWorked
WHERE
    Tickets.Status In ("open (Unchanged)","open","new","stalled")
AND
    Tickets.Type <> "reminder";

-- Equivalent SELECT statement
SELECT
    Tickets.TimeWorked,
    Tickets.TimeLeft,
    Tickets.TimeEstimated - Tickets.TimeWorked as TicketsTimeLeft
FROM
    Tickets
WHERE
    Tickets.Status In ('open (Unchanged)','open','new','stalled')
AND
    Tickets.Type <> 'reminder';

-----------------------------------------------------
-- Tickets 3: update custom field 'Need by Date'
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Tickets
INNER JOIN
    Qcstm00016PullNeedByDate
ON
    Tickets.id = Qcstm00016PullNeedByDate.TicktNo
SET
    Qcstm00016PullNeedByDate.cNeedByDate = Format(CVDate([cNeedByDate]),"mm/dd/yyyy")
WHERE
    (((Tickets.Status) Not In ("resolved","rejected")));

-- ANSI/ISO SQL for MySQL
-- custom_field_need_by_date is a view in the rt4 database (see rt/views.sql)
UPDATE
    Tickets
INNER JOIN
    custom_field_need_by_date
ON
    Tickets.id = custom_field_need_by_date.TicketNumber
SET
    custom_field_need_by_date.NeedByDate =
    DATE_FORMAT(
        STR_TO_DATE(
            custom_field_need_by_date.NeedByDate, '%m/%d/%Y'
        ),
        '%m/%d/%Y'
    )
WHERE
    Tickets.Status Not In ("resolved","rejected");

-- Equivalent SELECT statement
SELECT
    custom_field_need_by_date.TicketNumber,
    DATE_FORMAT(
        STR_TO_DATE(
            custom_field_need_by_date.NeedByDate, '%m/%d/%Y'
        ),
        '%m/%d/%Y'
    )
FROM
    Tickets
INNER JOIN
    custom_field_need_by_date
ON
    Tickets.id = custom_field_need_by_date.TicketNumber
WHERE
    Tickets.Status Not In ('resolved','rejected')

-----------------------------------------------------
-- Tickets 4: update custom field 'Percent Complete'
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Tickets
INNER JOIN
    Qcstm00054PullPercntComplt
ON
    Tickets.id = Qcstm00054PullPercntComplt.TicktNo
SET
    Qcstm00054PullPercntComplt.cPercntComplt = "100"
WHERE (
    ((Qcstm00054PullPer cntComplt.cPercntCo mplt)<>"100")
AND
    ((Tickets.Queue) In (26,49,45,44,39,50,7, 32))
AND
    ((CVDate([Resolved])) >#11/30/2015#)
AND
    ((Tickets.Status) In ("resolved"))
);

-- ANSI/ISO SQL for MySQL
-- custom_field_percent_complete is a view in the rt4 database
-- (see rt/views.sql)
UPDATE
    Tickets
INNER JOIN
    custom_field_percent_complete
ON
    Tickets.id = custom_field_percent_complete.TicketNumber
SET
    custom_field_percent_complete.PercentComplete = '100'
WHERE
    custom_field_percent_complete.PercentComplete <> '100'
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    Tickets.Resolved > '2015-11-30'
AND
    Tickets.Status In ('resolved');

-- Equivalent SELECT statement
SELECT
    custom_field_percent_complete.PercentComplete
FROM
    Tickets
INNER JOIN
    custom_field_percent_complete
ON
    Tickets.id = custom_field_percent_complete.TicketNumber
WHERE
    custom_field_percent_complete.PercentComplete <> '100'
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    Tickets.Resolved > '2015-11-30'
AND
    Tickets.Status In ('resolved');

-----------------------------------------------------
-- Tickets 5: update custom field Time Remaining
-----------------------------------------------------

-- Original MS Access SQL
UPDATE
    Tickets
INNER JOIN
    Qcstm00059PullTimeRemaing
ON
    Tickets.id = Qcstm00059PullTimeRemaing.TicktNo
SET
    Qcstm00059PullTimeRemaing.cTimeReaming = "0"
WHERE (
    ((Qcstm00059PullTimeRemaing.cTimeReaming)<>"0")
AND
    ((Tickets.Queue) In (26,49,45,44,39,50,7,32))
AND
    ((CVDate([Resolved]))>#11/30/2015#)
AND
    ((Tickets.Status) In ("resolved"))
);

-- ANSI/ISO SQL for MySQL
-- custom_field_time_remaining is a view in the rt4 database (see rt/views.sql)
UPDATE
    Tickets
INNER JOIN
    custom_field_time_remaining
ON
    Tickets.id = custom_field_time_remaining.TicketNumber
SET
    custom_field_time_remaining.TimeRemaining = '0'
WHERE
    custom_field_time_remaining.TimeRemaining <> '0'
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    Tickets.Resolved > '2015-11-30'
AND
    Tickets.Status In ('resolved');

-- Equivalent SELECT statement
SELECT
    custom_field_time_remaining.TimeRemaining, Tickets.Resolved
FROM
    Tickets
INNER JOIN
    custom_field_time_remaining
ON
    Tickets.id = custom_field_time_remaining.TicketNumber
WHERE
    custom_field_time_remaining.TimeRemaining <> '0'
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    Tickets.Resolved > '2015-11-30'
AND
    Tickets.Status In ('resolved');
