-- --------------------------------------------------
-- remove carthage.edu from users.name
-- --------------------------------------------------
UPDATE
    Users
SET
    Users.Name = Left(Users.Name, InStr(Users.Name,"@car")-1)
WHERE
    ((Users.Name Like "%@carthage.edu") AND (Users.id Not In (449,455)));

SELECT
    Users.name, Left( Users.Name, InStr(Users.Name,"@car") -1 )
FROM
    Users
WHERE
    ((Users.Name Like "%@carthage.edu") AND (Users.id Not In (449,455)));

-- --------------------------------------------------
-- update email address if need be
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
-- Tickets: update TimeEstimated
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


UPDATE
    Tickets
SET
    Tickets.TimeLeft = [TimeEstimated]-[TimeWorked]
WHERE (
    (Tickets.Status In ("open (Unchanged)","open","new","stalled"))
AND
    (Tickets.Type <> "reminder")
)
