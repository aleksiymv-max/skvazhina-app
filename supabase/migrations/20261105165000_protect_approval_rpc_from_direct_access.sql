-- v2.05 security hardening: user-controlled p_actor must never be
-- directly callable through public PostgREST RPC. Only the trusted Edge
-- Functions, operating as service_role after bearer authentication, may
-- invoke these privileged approval procedures.
begin;
revoke all on function public.promysel_start_registration_approval(bigint,uuid)
 from public,anon,authenticated;
grant execute on function public.promysel_start_registration_approval(bigint,uuid)
 to service_role;
revoke all on function public.promysel_finish_registration_approval(bigint,uuid,uuid)
 from public,anon,authenticated;
grant execute on function public.promysel_finish_registration_approval(bigint,uuid,uuid)
 to service_role;
revoke all on function public.promysel_reject_registration(bigint,uuid,text)
 from public,anon,authenticated;
grant execute on function public.promysel_reject_registration(bigint,uuid,text)
 to service_role;
commit;