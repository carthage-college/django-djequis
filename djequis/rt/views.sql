-- custom field view for 'need by date'
DROP VIEW IF EXISTS custom_field_need_by_date;
CREATE VIEW
    custom_field_need_by_date AS
SELECT
    ObjectCustomFieldValues.ObjectId AS TicketNumber,
    ObjectCustomFieldValues.Content AS NeedByDate
FROM
    ObjectCustomFieldValues
WHERE
    ObjectCustomFieldValues.CustomField = 16
AND
    ObjectCustomFieldValues.Disabled <> 1;

-- custom field view for 'percent complete'
DROP VIEW IF EXISTS custom_field_percent_complete;
CREATE VIEW
    custom_field_percent_complete AS
SELECT
    ObjectCustomFieldValues.ObjectId AS TicketNumber,
    ObjectCustomFieldValues.Content AS PercentComplete
FROM
    ObjectCustomFieldValues
WHERE
    ObjectCustomFieldValues.CustomField = 54
AND
    ObjectCustomFieldValues.Disabled <> 1;

-- custom field view for 'time remaining'
DROP VIEW IF EXISTS custom_field_time_remaining;
CREATE VIEW
    custom_field_time_remaining AS
SELECT
    ObjectCustomFieldValues.ObjectId AS TicketNumber,
    ObjectCustomFieldValues.Content AS TimeRemaining
FROM
    ObjectCustomFieldValues
WHERE
    ObjectCustomFieldValues.CustomField  = 59
AND
    ObjectCustomFieldValues.Disabled <> 1;

-- custom field view ''
