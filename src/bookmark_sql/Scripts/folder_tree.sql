CREATE OR REPLACE FUNCTION get_folder_tree(export_id integer)
RETURNS TABLE(id int, parent_id int, depth int, tree_name text, full_path text)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE folder_tree AS (
        SELECT
            f.id,
            f.browser_export_id,
            f.name,
            f.parent_id,
            0 AS depth,
            f.name::text AS path
        FROM folders f
        WHERE f.browser_export_id = export_id
          AND f.parent_id IS NULL
        UNION ALL
        SELECT
            c.id,
            c.browser_export_id,
            c.name,
            c.parent_id,
            p.depth + 1,
            p.path || ' / ' || c.name
        FROM folders c
        JOIN folder_tree p ON c.parent_id = p.id
        WHERE c.browser_export_id = p.browser_export_id
    )
    SELECT
        ft.id,
        ft.parent_id,
        ft.depth,
        repeat('  ', ft.depth) || ft.name AS tree_name,
        ft.path AS full_path
    FROM folder_tree ft
    ORDER BY ft.path;
$$;

-- Verify the function exists (should return one row):
-- SELECT proname, pronamespace::regnamespace AS schema
-- FROM pg_proc WHERE proname = 'get_folder_tree';

SELECT * FROM get_folder_tree(2);
