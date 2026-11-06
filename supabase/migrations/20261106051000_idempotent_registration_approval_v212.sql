-- v2.12 approval is idempotent: a second tap does not throw or send mail.
-- Keep the original administrator/shop-chief authorization and row lock.
DO $body$
DECLARE original text;patched text;
BEGIN
 SELECT pg_get_functiondef(p.oid) INTO original
 FROM pg_proc p JOIN pg_namespace n ON p.pronamespace=n.oid
 WHERE n.nspname='public' AND p.proname='promysel_start_registration_approval';
 IF original IS NULL THEN RAISE EXCEPTION 'Registration approval function missing'; END IF;
 IF position('if not found or (r.state <> ''pending'' and not (r.state=''approved'' and r.invitation_sent_at is null)) then' in original)=0
 THEN RAISE EXCEPTION 'Approval guard changed; refusing unsafe patch'; END IF;
 patched:=replace(original,
   'if not found or (r.state <> ''pending'' and not (r.state=''approved'' and r.invitation_sent_at is null)) then',
   'if not found or r.state not in (''pending'',''approved'') then');
 EXECUTE patched;
END $body$;
