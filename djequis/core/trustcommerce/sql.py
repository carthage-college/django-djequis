PCE_TRANSACTIONS = '''
    SELECT
        activities.name as activity,
        transactions.activityID,
        transactions.amt,
        transactions.comment1 as comment1,
        transactions.comment2 as StuID,
        transactions.datecreated as datecreated,
        transactions.name,
        transactions.respmsg as result,
        transactions.pnref,
        activities.webtranscode  as SelWTCode,
        "tcpayflow" as datasource
    FROM
        transactions, activities
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.result=0
    AND
        transactions.dateexported is null
    ORDER BY
        transactions.activityID
'''
PCE_TRANSACTIONS_ACTIVITY = '''
    SELECT
        activities.name as activity,
        activities.ID as activityID,
        transactions.id as RecID,
        transactions.activityID,
        transactions.amt,
        transactions.comment1 as comment1,
        transactions.comment2 as StuID,
        transactions.datecreated,
        transactions.name,
        transactions.respmsg as result,
        transactions.pnref,
        activities.webtranscode as webtranscode,
        activities.subsID as subsID,
        "tcpayflow" as datasource
    FROM
        transactions, activities
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.result=0
    AND
        transactions.dateexported is null
    AND
        activities.name='{activity}'
    ORDER BY
        transactions.activityID
'''
PCE_TRANSACTIONS_CHECKED = '''
    SELECT
        activities.name as activity,
        activities.ID as activityID,
        transactions.id as RecID,
        concat(cast(left(activities.orderacct,7) as char(7)), cast(right(activities.orderacct,4) as char(4))) as acct,
        transactions.activityID,
        transactions.amt,
        transactions.comment1 as comment1,
        transactions.comment2 as StuID,
        transactions.datecreated,
        transactions.name,
        transactions.respmsg as result,
        transactions.pnref,
        activities.webtranscode as webtranscode,
        activities.subsID as subsID,
        "tcpayflow" as datasource
    FROM
        transactions, activities
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.id in ({CheckedVal})
'''
PSM_TRANSACTIONS = '''
    SELECT
        processors_order.operator as activity,
        processors_activity.ID as activityID,
        processors_order.total as amt,
        processors_order.comments as comment1,
        "Comment2" as StuID,
        processors_order.time_stamp as datecreated,
        processors_order.cc_name as name,
        processors_order.status as result,
        processors_order.transid as pnref,
        processors_activity.webtranscode as SelWTCode,
        "djforms_on_psm" as datasource
    FROM
        processors_order, processors_activity
    WHERE
       processors_activity.name = processors_order.operator
    AND
        status="approved"
    AND
        export_date is null
    AND
        operator in ("DJSoccerCamp", "DJTinueEnrichmentReg")
    ORDER BY
        activityID
'''
PSM_TRANSACTIONS_ACTIVITIES = '''
    SELECT
        processors_order.operator as activity,
        processors_activity.ID as activityID,
        processors_order.total as amt,
        processors_order.comments as comment1,
        "StuID" as StuID,
        processors_order.time_stamp as datecreated,
        processors_order.cc_name as name,
        processors_order.status as result,
        processors_order.transid as pnref,
        processors_activity.subsid as subsID,
        processors_activity.webtranscode as SelWTCode,
        processors_activity.webtranscode as webtranscode,
        "djforms_on_psm" as datasource
    FROM
        processors_order, processors_activity
    WHERE
       processors_activity.name = processors_order.operator
    AND
        processors_order.status="approved"
    AND
        processors_order.export_date is null
    AND
        processors_order.operator='{activity}'
'''
PSM_TRANSACTIONS_CHECKED = '''
    SELECT
        processors_order.operator as activity,
        processors_order.id as RecID,
        processors_activity.ID as activityID,
        processors_order.total as amt,
        processors_order.comments as comment1,
        concat(cast(left(processors_activity.orderacct,7) as char(7)), cast(right(processors_activity.orderacct,4) as char(4))) as acct,
        "Comment2" as StuID,
        processors_order.time_stamp as datecreated,
        processors_order.cc_name as name,
        processors_order.cc_4_digits as ccnum,
        processors_order.status as result,
        processors_order.transid as pnref,
        processors_activity.subsid as subsID,
        processors_activity.webtranscode as SelWTCode,
        processors_activity.webtranscode as webtranscode,
        "djforms_on_psm" as datasource
    FROM
        processors_order, processors_activity
    WHERE
       processors_activity.name = processors_order.operator
    AND
      processors_order.id in ({CheckedVal})
'''
NEW_TRANSACTIONS = '''
    SELECT * FROM pce_transactions
    UNION
    SELECT * FROM psm_transactions
    ORDER BY activity, datecreated
'''