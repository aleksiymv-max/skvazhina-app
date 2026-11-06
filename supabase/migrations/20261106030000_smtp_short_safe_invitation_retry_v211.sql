-- v2.11: Custom SMTP is accepting invites. Remove legacy 31-minute spacing.
-- Retain atomic per-request lock, short anti-duplicate spacing and 65-minute
-- provider 429 backoff in promysel_record_registration_invitation.
DO $m$
DECLARE old_ddl text; new_ddl text;
BEGIN
 SELECT pg_get_functiondef(p.oid) INTO old_ddl
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.proname='promysel_claim_registration_invitation'
   AND pg_get_function_identity_arguments(p.oid)='p_request_id bigint, p_actor uuid';
 IF old_ddl IS NULL OR
    (length(old_ddl)-length(replace(old_ddl, '31 minutes', '')))/length('31 minutes') <> 2
 THEN RAISE EXCEPTION 'Registration mail-gate function changed; aborting'; END IF;
 new_ddl:=replace(old_ddl, '31 minutes', '2 minutes');
 EXECUTE new_ddl;
 -- The old 31-minute global window is an artificial application throttle,
 -- not an actual 429. Existing provider 429 backoff is retained in job state.
 UPDATE public.promysel_invitation_mail_gate
 SET next_available_at=least(next_available_at,now()+interval '2 minutes'),
     updated_at=now()
 WHERE key='supabase-auth' AND next_available_at>now()+interval '2 minutes'
   AND NOT EXISTS (
     SELECT 1 FROM public.promysel_registration_invitation_jobs
     WHERE last_error_code IN ('over_email_send_rate_limit','email_rate_limit')
       AND next_attempt_at>now()
   );
END $m$;
