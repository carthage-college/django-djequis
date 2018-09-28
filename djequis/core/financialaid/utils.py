import time


def csv_gen(sqlresults, writer, test=False):

    headerdate = time.strftime('%Y%m%d')
    # if on command line --test is used then header will be printed
    if test:
        #header = ["File Name", "School OPEID", "File Date"]
        # writes file header
        #writer.writerow(header)
        # displays file header elements
        #header_detail = ("CCM", "00383900", headerdate)
        # writes file header elements
        #writer.writerow(header_detail)
        # if on command line --test is used then loan header will be printed
        loan_header = [
            "School OPEID", "Academic Year", "Student SSN",
            "Student First Name", "Student Last Name", "School Student ID",
            "Student Address Line 1", "Student Address Line 2",
            "Student Address Line 3", "Student City", "Student State",
            "Student Zip", "Student Country", "Student Email Address",
            "Private Loan Name 1", "Private Loan Amount 1",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 1", "Private Loan Name 2", "Private Loan Amount 2",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 2", "Private Loan Name 3", "Private Loan Amount 3",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 3", "Private Loan Name 4", "Private Loan Amount 4",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 4", "Private Loan Name 5", "Private Loan Amount 5",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 5", "Private Loan Name 6", "Private Loan Amount 6",
            "Private Loan Interest Rate", "Repayment Length", 
            "Loan Date 6", "Institutional Loan Name 1",
            "Institutional Loan Amount","Institutional Loan Interest Rate",
            "Repayment Length", "Loan Date", "Institutional Loan Name 2",
            "Institutional Loan Amount","Institutional Loan Interest Rate",
            "Repayment Length", "Loan Date", "Institutional Loan Name 3",
            "Institutional Loan Amount","Institutional Loan Interest Rate",
            "Repayment Length", "Loan Date", "Institutional Loan Name 4",
            "Institutional Loan Amount","Institutional Loan Interest Rate",
            "Repayment Length", "Loan Date",
            "Institutional Loan Name 5", "Institutional Loan Amount",
            "Institutional Loan Interest Rate", "Repayment Length",
            "Loan Date", "Institutional Loan Name 6",
            "Institutional Loan Amount","Institutional Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 1",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 2",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 3",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 4",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 5",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "State Loan Name 6",
            "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length", "Loan Date", "Tuition", "Tuition Fees",
            "Room & Board", "Books & Supplies", "Transportation",
            "Other Education Costs", "Personal Education Costs",
            "Loan Fees","Institutional Grants","Institutional Scholarship",
            "Federal Grants", "State Grants", "Other Scholarships"
        ]
        # writes loan header elements
        writer.writerow(loan_header)
    # displays file header elements
    header_detail = ("CCM", "00383900", headerdate)
    # writes file header elements
    writer.writerow(header_detail)
    #######################################################################
    # loops through maxaidcount to dynamically add file detail header for
    # loans. It will add as many extra loans as found in the max aid count
    #######################################################################
    currentID = 0 # initializing currentID 0
    loanCount = 0 # initializing loanCount 0
    maxaidcount = 18 # set maxaid count
    for row in sqlresults:
        if row['student_id_number'] != currentID:
            if currentID != 0:
                # loops through maxaidcount to add private loans
                for i in range (loanCount, maxaidcount):
                    # creates spacing in between private loan data and
                    # other loan information
                    csv_line += ("", "0.00", "", "", "")
                # adds other loan information
                csv_line += csv_end
                writer.writerow(csv_line)
            currentID = row["student_id_number"]
            loanCount = 0
            ###############################################################
            # writes non-dynamic detail file data of the student record
            # adds each financial aid loan record to same row for student
            # The % .2f is to keep the decimal format
            ###############################################################
            csv_line = (
                row['opeid'],row['acadyear'],row['social_security_number'],
                row['student_first_name'], row['student_last_name'],
                row['student_id_number'], row['student_address_line_1'],
                row['student_address_line_2'],row['student_address_line_3'],
                row['student_city'], row['student_state_code'],
                row['student_postal_code'], row['student_country_code'],
                row['student_email']
            )
            # adds other loan information
            csv_end = (
                ("{0:.2f}".format(0.00 if row['c_tufe'] is None else row['c_tufe'])),
                "0.00",
                ("{0:.2f}".format(0.00 if row['c_rmbd'] is None else row['c_rmbd'])),
                ("{0:.2f}".format(0.00 if row['c_book'] is None else row['c_book'])),
                ("{0:.2f}".format(0.00 if row['c_tran'] is None else row['c_tran'])),
                ("{0:.2f}".format(0.00 if row['c_misc'] is None else row['c_misc'])),
                "0.00",
                ("{0:.2f}".format(0.00 if row['c_loan'] is None else row['c_loan'])),
                ("{0:.2f}".format(0.00 if row['c_instgrants'] is None else row['c_instgrants'])),
                ("{0:.2f}".format(0.00 if row['c_instscholar'] is None else row['c_instscholar'])),
                ("{0:.2f}".format(0.00 if row['c_fedgrants'] is None else row['c_fedgrants'])),
                ("{0:.2f}".format(0.00 if row['c_stegrants'] is None else row['c_stegrants'])),
                ("{0:.2f}".format(0.00 if row['c_outsideaid'] is None else row['c_outsideaid']))
            )

        csv_line += (
            row['loan_name'],
            ("{0:.2f}".format(0.00 if row['aid_amount'] is None else row['aid_amount'])),
            "", "", row['loan_date']
        )
        loanCount = loanCount +1
    # writes the last line for the last student loan record
    for i in range (loanCount, maxaidcount):
        # creates spacing in between private loan data and
        # other loan information
        csv_line += ("", "0.00", "", "", "")
    csv_line += csv_end
    writer.writerow(csv_line)
