section_school_code

jenz_course_rec

API "Course Section" endpoint

start with user_id (which is CX ID)

GET https://api.schoology.com/v1/users/{user_id}/grades

that will give us section_id, and with a timestamp we can use shell script


GET https://api.schoology.com/v1/sections/{id}
[section_id]
returns section_school_code

we need section_school_code to interact with CX.


test bed:

https://carthagetest.schoologytest.com/system_settings/integration/api
