-- Scoped task provenance can be created only by the trusted, authenticated
-- Edge service role; anonymous/normal signed-in clients still have no write grant.
GRANT INSERT ON public.promysel_task_scopes TO service_role;
REVOKE INSERT,UPDATE,DELETE ON public.promysel_task_scopes FROM PUBLIC,anon,authenticated;
