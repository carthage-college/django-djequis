-- --------------------------------------------------
-- Users 1: remove carthage.edu from users.name
-- --------------------------------------------------
UPDATE
    Users
SET
    Users.Name = Left(Users.Name, InStr(Users.Name,"@car")-1)
WHERE
    ((Users.Name Like "%@carthage.edu") AND (Users.id Not In (449,455)));

-- equivalent SELECT statement
SELECT
    Users.name, Left( Users.Name, InStr(Users.Name,"@car") -1 )
FROM
    Users
WHERE
    ((Users.Name Like "%@carthage.edu") AND (Users.id Not In (449,455)));

-- --------------------------------------------------
-- Users 2: update email address if need be
-- --------------------------------------------------
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

-- equivalent SELECT statement
SELECT
    Users.id, Users.name, Users.EmailAddress, InStr(EmailAddress,"@")
FROM
    Users
WHERE
    (
        ((Users.EmailAddress Not Like "%@%") OR (Users.EmailAddress Is Null))
        AND
        (Users.id>12 And Users.id Not In (1,6,93,449,455,707))
        AND
        (Users.Name Like "%carthage%")
    );

-- --------------------------------------------------
-- Tickets 1: update TimeEstimated
-- iif ( condition, value_if_true, value_if_false )
-- --------------------------------------------------
UPDATE
    Tickets
SET
    Tickets.TimeEstimated = Tickets.TimeWorked + Tickets.TimeLeft + 1
WHERE (
    (Tickets.Status In ("open (Unchanged)","open","new","stalled"))
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

-- equivalent SELECT statement
SELECT
    Tickets.TimeWorked,
    Tickets.TimeLeft,
    Tickets.TimeWorked + Tickets.TimeLeft + 1 as TicketsTimeEstimated,
    Tickets.TimeEstimated
FROM
    Tickets
WHERE (
    (Tickets.Status In ("open (Unchanged)","open","new","stalled"))
AND
    (Tickets.Type <> "reminder")
AND
    (Tickets.TimeEstimated = 0 OR Tickets.TimeEstimated < (Tickets.TimeWorked + Tickets.TimeLeft))
);

-- --------------------------------------------------
-- Tickets 2: update TimeLeft
-- --------------------------------------------------
UPDATE
    Tickets
SET
    Tickets.TimeLeft = [TimeEstimated]-[TimeWorked]
WHERE
    Tickets.Status In ("open (Unchanged)","open","new","stalled")
AND
    Tickets.Type <> "reminder"

-- equivalent SELECT statement
SELECT
    Tickets.TimeWorked,
    Tickets.TimeLeft,
    TimeEstimated - TimeWorked as TicketsTimeLeft
FROM
    Tickets
WHERE
    Tickets.Status In ("open (Unchanged)","open","new","stalled")
AND
    Tickets.Type <> "reminder"

-- --------------------------------------------------
-- Tickets 3: update custom field 'Need by Date'
-- --------------------------------------------------
UPDATE
    Tickets
INNER JOIN
    custom_field_need_by_date ON Tickets.id = custom_field_need_by_date.TicketNumber
SET
    custom_field_need_by_date.NeedByDate = Format(CVDate(custom_field_need_by_date.NeedByDate),"mm/dd/yyyy")
WHERE
    (((Tickets.Status) Not In ("resolved","rejected")));

-- equivalent SELECT statement
SELECT
    custom_field_need_by_date.TicketNumber,
    Format(CVDate(custom_field_need_by_date.NeedByDate),"mm/dd/yyyy")
FROM
    Tickets
INNER JOIN
    custom_field_need_by_date ON Tickets.id = custom_field_need_by_date.TicketNumber
WHERE
    (((Tickets.Status) Not In ("resolved","rejected")));

-- --------------------------------------------------
-- Tickets 4: update custom field 'Percent Complete'
-- --------------------------------------------------
UPDATE
    Tickets
INNER JOIN
    custom_field_percent_complete ON Tickets.id = custom_field_percent_complete.TicketNumber
SET
    custom_field_percent_complete.PercentComplete = "100"
WHERE
    custom_field_percent_complete.PercentComplete <> "100"
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    CVDate([Resolved]) > #11/30/2015#
AND
    Tickets.Status In ("resolved");

-- equivalent SELECT statement


-- --------------------------------------------------
-- Tickets 5: update custom field Time Remaining
-- --------------------------------------------------

UPDATE
    Tickets
INNER JOIN
    custom_field_time_remaining ON Tickets.id = custom_field_time_remaining.TicketNumber
SET
    custom_field_time_remaining.TimeRemaining = "0"
WHERE
    custom_field_time_remaining.TimeRemaining <> "0"
AND
    Tickets.Queue In (26,49,45,44,39,50,7,32)
AND
    CVDate([Resolved]) > #11/30/2015#
AND
    Tickets.Status In ("resolved");

-- equivalent SELECT statement

