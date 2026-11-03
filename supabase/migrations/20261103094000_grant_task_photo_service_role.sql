-- Fix 2026-11-03 production HTTP 500 in promysel-task-photos/register.
-- PostgreSQL newly created tables did not inherit service_role privileges.
-- The Edge Function validates Supabase Auth JWT, field membership and task
-- access before using this database role.
-- Do not grant access to anon/authenticated; keep RLS enabled and bucket private.
grant select,insert,update,delete on table public.promysel_task_photo_registry to service_role;
grant select,insert,update,delete on table public.promysel_task_photos to service_role;
