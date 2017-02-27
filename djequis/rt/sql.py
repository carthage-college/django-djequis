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
        (Users.EmailAddress Not Like "%@%")
        AND
        (Users.id>12 And Users.id Not In (1,6,93,449,455,707))
        AND
        ((Users.Name Like "%carthage%") OR (Users.EmailAddress Is Null))
    );


# tickets
UPDATE
    Tickets
SET
    Tickets.TimeEstimated = [TimeWorked]+[TimeLeft]+1
WHERE
    (((Tickets.Status) In ("open (Unchanged)","open","new","stalled"))
AND
    ((IIf([TimeEstimated]=0 Or [TimeEstimated]<[TimeWorked]+[TimeLeft],"DoIt","Skip"))="DoIt")
AND
    ((Tickets.Type)<>"reminder"));
