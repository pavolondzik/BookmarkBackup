SELECT
    schemaname,
    relname AS table_name,
    n_live_tup AS estimated_rows
FROM pg_stat_all_tables
WHERE schemaname = 'public'
ORDER BY relname;


select *
from folders;


select b.*
from folders f
inner join bookmarks b on b.folder_id = f.id
where f.name = 'Byt'

select *
from users

select * 
from devices

select *
from browsers

select *
from browser_exports 


select *
from bookmarks
limit 50;