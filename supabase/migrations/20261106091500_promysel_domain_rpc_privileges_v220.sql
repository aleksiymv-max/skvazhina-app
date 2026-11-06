-- v2.20: domain sync repair (2026-11-06).
-- Problem: service_role cannot SELECT auth.users inside an INVOKER RPC.
-- The function is owned by postgres and is exposed ONLY to service_role.
-- Do not grant service_role direct access to auth.users.
BEGIN;
ALTER FUNCTION public.promysel_commit_sync_domain(
  text,text,text,text,uuid,bigint,jsonb
) SECURITY DEFINER;
ALTER FUNCTION public.promysel_commit_sync_domain(
  text,text,text,text,uuid,bigint,jsonb
) SET search_path = '';
REVOKE ALL ON FUNCTION public.promysel_commit_sync_domain(
  text,text,text,text,uuid,bigint,jsonb
) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_commit_sync_domain(
  text,text,text,text,uuid,bigint,jsonb
) TO service_role;
COMMIT;