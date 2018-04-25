UPDATE_GRADE = '''
    UPDATE
        cw_rec
    SET
        cw_rec.grd = '{grade}'
    WHERE
        jenzcrs_rec.coursekey = '{coursekey}'
    AND
        cw_rec.id = {student_number}
    AND
        cw_rec.yr = SUBSTRING(jenzcrs_rec.coursekey FROM 1 FOR 4)
    AND
        cw_rec.cat =  SUBSTRING(jenzcrs_rec.coursekey FROM length(trim(coursekey))-8 FOR 4)
    AND
        cw_rec.sess =  SUBSTRING(jenzcrs_rec.coursekey FROM 6 FOR 2)
    AND
        cw_rec.prog = right(trim(jenzcrs_rec.coursekey),4)
    AND
        cw_rec.crs_no = SUBSTRING(jenzcrs_rec.coursekey FROM 9 for INSTR(jenzcrs_rec.coursekey,';',9)-9)
    AND
        cw_rec.sec = SUBSTRING(jenzcrs_rec.coursekey FROM length(trim(jenzcrs_rec.coursekey))-11 FOR 2)
    AND
        cw_rec.stat IN ('R', 'A', 'T','N','I')  --Registered
'''.format
