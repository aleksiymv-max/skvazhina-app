-- v2.13: service_role does not have SELECT on auth.users/auth.sessions.
-- Run this ONE guarded authorization lookup under postgres ownership.
-- It is executable ONLY through trusted service-role Edge Functions.
-- No Data API/browser grants and no direct auth-table grants are added.
DO $m$
DECLARE owner_name text;
BEGIN
 SELECT pg_get_userbyid(p.proowner) INTO owner_name
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.proname='promysel_request_scope_v213';
 IF owner_name IS DISTINCT FROM 'postgres' THEN
  RAISE EXCEPTION 'Unexpected ownership of request scope; aborting';
 END IF;
END $m$;
ALTER FUNCTION public.promysel_request_scope_v213(uuid,uuid) SECURITY DEFINER;
ALTER FUNCTION public.promysel_request_scope_v213(uuid,uuid) SET search_path = '';
REVOKE ALL ON FUNCTION public.promysel_request_scope_v213(uuid,uuid)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_request_scope_v213(uuid,uuid) TO service_role;
