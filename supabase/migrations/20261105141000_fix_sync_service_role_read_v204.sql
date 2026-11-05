-- 2026-11-05: Production hotfix for v2.04 sync/pull HTTP 500.
-- The Edge Function uses the service-role client to validate field-scoped
-- histories against this table. v2.04 originally created the table without
-- granting its SELECT privilege. Service role has BYPASSRLS but still needs
-- SQL SELECT permission to access new custom tables.
-- No user-facing SELECT grant, no RLS relaxation, no data modification.
grant select on table public.promysel_task_scopes to service_role;

do $$
begin
  if not has_table_privilege('service_role','public.promysel_task_scopes','select')
    then raise exception 'Missing canonical task ownership read permission';
  end if;
  if has_table_privilege('anon','public.promysel_task_scopes','select')
     or has_table_privilege('authenticated','public.promysel_task_scopes','select')
    then raise exception 'Task ownership table must not be directly readable by app users';
  end if;
end $$;
