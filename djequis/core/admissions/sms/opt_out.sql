select * from aa_rec where opt_out is not null and opt_out <> ""
select * from aa_rec where opt_out = 'N'
select * from aa_rec where opt_out = 'Y' or opt_out= '1'

select * from aa_rec where phone=''

select * from ctc_rec where resrc="TEXTOUT";
select * from ctc_rec where ctc_no=<college id>
