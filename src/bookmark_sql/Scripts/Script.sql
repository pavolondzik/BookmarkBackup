SELECT
    schemaname,
    relname AS table_name,
    n_live_tup AS estimated_rows
FROM pg_stat_all_tables
WHERE schemaname = 'public'
ORDER BY relname;


select *
from folders;

select *
from bookmarks;

