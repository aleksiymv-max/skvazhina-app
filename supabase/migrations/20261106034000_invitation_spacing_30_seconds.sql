-- Requested short term SMTP invite queue pacing: 30 seconds per claim.
-- Strictly preserve per-request lease and provider 429 retry/backoff.
DO $migration$
DECLARE original_definition text; patched_definition text; matching_count int;
BEGIN
 SELECT pg_get_functiondef(p.oid) INTO original_definition
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public'
   AND p.proname='promysel_claim_registration_invitation'
   AND pg_get_function_identity_arguments(p.oid)='p_request_id bigint, p_actor uuid';
 IF original_definition IS NULL THEN
   RAISE EXCEPTION 'Registration mail claim procedure absent';
 END IF;
 matching_count:=(length(original_definition)
   -length(replace(original_definition, 'interval ''2 minutes''', '')))
   /length('interval ''2 minutes''');
 IF matching_count<>2 THEN
   RAISE EXCEPTION 'Expected two artificial 2-minute mail delays; found %',matching_count;
 END IF;
 patched_definition:=replace(original_definition,
   'interval ''2 minutes''','interval ''30 seconds''');
 EXECUTE patched_definition;
 -- No outstanding provider rate limit: shorten only the ordinary global budget.
 -- Explicit 65-minute 429 backoffs and the 90-second sending lease are untouched.
 IF NOT EXISTS (
   SELECT 1 FROM public.promysel_registration_invitation_jobs
   WHERE last_error_code IN ('over_email_send_rate_limit','email_rate_limit')
     AND next_attempt_at>now()
 ) THEN
   UPDATE public.promysel_invitation_mail_gate
   SET next_available_at=least(next_available_at,now()+interval '30 seconds'),
       updated_at=now()
   WHERE key='supabase-auth'
     AND next_available_at>now()+interval '30 seconds';
 END IF;
END $migration$;