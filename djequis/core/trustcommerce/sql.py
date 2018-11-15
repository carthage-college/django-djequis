from djequis.core.trustcommerce.views import *

# Query for main page home.html
PCE_SUMMARY = '''
    SELECT activities.name as activity, transactions.activityID as id, 
        count(activities.name) as activity_count
    FROM `transactions`, `activities`
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.result=0
    AND
        transactions.dateexported is null
    GROUP BY activities.name, transactions.activityID
'''

PSM_SUMMARY = '''
    SELECT
        processors_order.operator as activity,
        processors_activity.ID as activityID, count(processors_order.operator) as activity_count
    FROM
        `processors_order`, `processors_activity`
    WHERE
       processors_activity.name = processors_order.operator
    AND
        status="approved"
    AND
        export_date is null
    AND
        operator in ("DJSoccerCamp", "DJTinueEnrichmentReg")
    GROUP BY
        processors_order.operator, processors_activity.ID 
'''


# Query for second step, details.html
PCE_TRANSACTIONS_ACTIVITY = '''
    SELECT
        activities.name as activity,
        transactions.activityID,
        transactions.id as RecID,
        transactions.amt,
        transactions.comment1 as comment1,
        transactions.comment2 as StuID,
        transactions.datecreated as datecreated,
        transactions.name,
        transactions.respmsg as result,
        transactions.pnref,
        activities.webtranscode  as SelWTCode,
        "tcpayflow" as datasource
    FROM `transactions`, `activities`
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.result=0
    AND
        transactions.dateexported is null
    AND
        transactions.activityID = {0}
'''


PSM_TRANSACTIONS_ACTIVITY = '''
    SELECT
        processors_order.operator as activity,
        processors_activity.ID as activityID,
        processors_order.id as RecID,
        processors_order.total as amt,
        processors_order.comments as comment1,
        processors_order.billingid as StuID,
        processors_order.time_stamp as datecreated,
        processors_order.cc_name as name,
        processors_order.status as result,
        processors_order.transid as pnref,
        processors_activity.webtranscode as SelWTCode,
        "djforms_on_psm" as datasource
    FROM
        `processors_order`, `processors_activity`
    WHERE
       processors_activity.name = processors_order.operator
    AND
        status="approved"
    AND
        export_date is null
    AND
        operator in ("DJSoccerCamp", "DJTinueEnrichmentReg")
    AND        
        processors_activity.ID = {0}
    '''



# Query for third step, return only checked values
PCE_TRANSACTIONS_CHECKED = '''
    SELECT
        activities.name as activity,
        activities.ID as activityID,
        transactions.id as RecID,
        concat(cast(left(activities.orderacct,7) as char(7)), cast(right(activities.orderacct,4) as char(4))) as acct,
        transactions.amt,
        transactions.comment1 as comment1,
        transactions.comment2 as StuID,
        transactions.datecreated,
        transactions.name,
        transactions.respmsg as result,
        transactions.pnref,
        activities.webtranscode as webtranscode,
        activities.subsID as subsID,
        activities.webtranscode as SelWTCode,
        '' as ccnum,
        "tcpayflow" as datasource
    FROM
        transactions, activities
    WHERE
        transactions.activityID = activities.id
    AND
        transactions.id in ({0})
    AND
        activities.ID = ({1})
'''


PSM_TRANSACTIONS_CHECKED = '''
    SELECT
        processors_order.operator as activity,
        processors_activity.ID as activityID,
        processors_order.id as RecID,
        concat(cast(left(processors_activity.orderacct,7) as char(7)), cast(right(processors_activity.orderacct,4) as char(4))) as acct,
        processors_order.total as amt,
        processors_order.comments as comment1,
        "Comment2" as StuID,
        processors_order.time_stamp as datecreated,
        processors_order.cc_name as name,
        processors_order.status as result,
        processors_order.transid as pnref,
        processors_activity.webtranscode as webtranscode,
        processors_activity.subsid as subsID,
        processors_activity.webtranscode as SelWTCode,
        processors_order.cc_4_digits as ccnum,
        "djforms_on_psm" as datasource
    FROM
        processors_order, processors_activity
    WHERE
       processors_activity.name = processors_order.operator
    AND
      processors_order.id in ({0})
    AND
      processors_activity.ID = ({1})
'''


NEW_TRANSACTIONS = '''
    SELECT * FROM pce_transactions
    UNION
    SELECT * FROM psm_transactions
    ORDER BY activity, datecreated
'''



