-- Temporary requested fast-retry mode for onboarding email delivery.
-- This changes only application-managed cooldowns, NEVER Supabase Auth quotas.
-- The per-request 90-second in-flight lease and atomic sending lock remain intact.
DO $patch$
DECLARE current_def text; changed_def text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO current_def
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='public'
    AND p.proname='promysel_record_registration_invitation';
  IF current_def IS NULL THEN
    RAISE EXCEPTION 'Invitation delivery function not found: no changes';
  END IF;
  IF (length(current_def)-length(replace(current_def,'65 minutes','')))
        /length('65 minutes')<>2
     OR position('when p_status=''action_required'' then interval ''15 minutes''' in current_def)=0
     OR position('else interval ''30 seconds'' end;' in current_def)=0 THEN
    RAISE EXCEPTION 'Delivery rate-limit source changed: no changes applied';
  END IF;
  changed_def:=replace(current_def,'65 minutes','30 seconds');
  changed_def:=replace(changed_def,
    'when p_status=''action_required'' then interval ''15 minutes''',
    'when p_status=''action_required'' then interval ''30 seconds''');
  EXECUTE changed_def;

  -- Do not mutate "sending" records or send mail as part of this change.
  -- Only shorten previously scheduled local application cooldowns.
  UPDATE public.promysel_invitation_mail_gate
     SET next_available_at=LEAST(next_available_at,now()+interval '30 seconds'),
         updated_at=now()
   WHERE key='supabase-auth' AND next_available_at>now()+interval '30 seconds';
  UPDATE public.promysel_registration_invitation_jobs
     SET next_attempt_at=LEAST(next_attempt_at,now()+interval '30 seconds'),
         updated_at=now()
   WHERE status IN ('queued','retry','action_required')
     AND next_attempt_at>now()+interval '30 seconds';
END $patch$;
