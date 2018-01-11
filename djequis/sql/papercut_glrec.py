GET_GL_ACCTS = '''
    SELECT
        fund, func, obj, TRIM(acct_descr1) as acct_descr
    FROM
        gla_rec
    WHERE
        fscl_yr = CASE WHEN TODAY < TO_DATE(YEAR(TODAY) || '-07-01', '%Y-%m-%d')    THEN MOD(YEAR(TODAY) - 1, 100) || MOD(YEAR(TODAY), 100)
                                                                                    ELSE MOD(YEAR(TODAY), 100) || MOD(YEAR(TODAY) + 1, 100)
                  END
    AND ((obj= 73140 AND fund IN (1,2))
    OR (func = 856 AND fund <> 1))
    ORDER BY
        func
'''