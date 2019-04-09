drop procedure if exists this_is_it ;

create procedure this_is_it(this CHAR(3), that CHAR(4), other CHAR(3))

select * from table
where column1 = this and
column2 = that and
column3 = other;

end procedure;

grant execute on this_is_it to public;
/*
execute procedure this_is_it("A","B","C") ;
*/
