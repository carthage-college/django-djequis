# --------------------------------------------------
# Tickets 3: update custom field 'Need by Date'
# --------------------------------------------------
TICKETS_UPDATE_3 = '''
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
        Tickets.Status Not In ('resolved','rejected')
'''

# equivalent SELECT statement
TICKETS_SELECT_3 = '''
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
'''

# --------------------------------------------------
# Tickets 4: update custom field 'Percent Complete'
# --------------------------------------------------
TICKETS_UPDATE_4 = '''
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
'''

# equivalent SELECT statement
TICKETS_SELECT_4 = '''
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
'''

# --------------------------------------------------
# Tickets 5: update custom field Time Remaining
# --------------------------------------------------
TICKETS_UPDATE_5 = '''
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
        Tickets.Status In ('resolved')
'''

# equivalent SELECT statement
TICKETS_SELECT_5 = '''
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
        Tickets.Status In ('resolved')
'''
