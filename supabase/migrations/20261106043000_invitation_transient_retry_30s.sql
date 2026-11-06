-- Keep the existing 30-second interval between normal invitations.
-- Make transient non-429 delivery errors retry after 30 seconds rather than 15 min.
-- Preserve anti-duplicate locking, action_required and provider 429 backoff.
DO $patch$
DECLARE original_def text; revised_def text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO original_def
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='public'
    AND p.proname='promysel_record_registration_invitation'
    AND pg_get_function_identity_arguments(p.oid)=
      'p_request_id bigint, p_actor uuid, p_status text, p_user_id uuid, p_error_code text';
  IF original_def IS NULL THEN
    RAISE EXCEPTION 'Invitation record function was not found: no changes applied';
  END IF;
  IF (length(original_def)-length(replace(original_def,
      'else interval ''15 minutes'' end;', '')))
      /length('else interval ''15 minutes'' end;') <> 1 THEN
    RAISE EXCEPTION 'Unexpected retry implementation: no changes applied';
  END IF;
  IF position('then interval ''65 minutes''' in original_def)=0
    OR position('when p_status=''action_required'' then interval ''15 minutes''' in original_def)=0 THEN
    RAISE EXCEPTION 'Provider 429/configuration backoff changed: no changes applied';
  END IF;
  revised_def:=replace(original_def,
      'else interval ''15 minutes'' end;',
      'else interval ''30 seconds'' end;');
  EXECUTE revised_def;
  -- Existing non-provider transient failures may be retried sooner.
  UPDATE public.promysel_registration_invitation_jobs
     SET next_attempt_at=LEAST(next_attempt_at,now()+interval '30 seconds'),
         updated_at=now()
   WHERE status='retry'
     AND next_attempt_at>now()+interval '30 seconds'
     AND coalesce(last_error_code,'') NOT IN
       ('over_email_send_rate_limit','email_rate_limit');
END $patch$;
