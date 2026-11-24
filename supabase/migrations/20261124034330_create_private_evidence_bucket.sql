-- Private Supabase Storage bucket for ORACLE CONTROL evidence objects.
-- Access is performed by the authenticated API using a server-only service key.
-- Never expose the service key in a browser bundle or client application.
insert into storage.buckets (id, name, public, file_size_limit)
values ('oracle-control-evidence', 'oracle-control-evidence', false, 26214400)
on conflict (id) do update
set public = false, file_size_limit = excluded.file_size_limit;
