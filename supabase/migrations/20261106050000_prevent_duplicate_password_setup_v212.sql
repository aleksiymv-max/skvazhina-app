-- v2.12 Prevent repeated onboarding from overwriting an existing user's password.
-- An email click may auto-create a session; only an actual password hash or
-- server-maintained password_changed_at marker counts as first setup complete.
DO $sql$
DECLARE old_claim text;new_claim text;old_approval text;new_approval text;
BEGIN
 SELECT pg_get_functiondef(p.oid) INTO old_claim
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.proname='promysel_claim_registration_invitation';
 IF old_claim IS NULL OR position('if v_request.invitation_sent_at is not null or v_job.status=''sent'' then' in old_claim)=0
 THEN RAISE EXCEPTION 'Unexpected claim function; refusing unsafe change'; END IF;
 new_claim:=replace(old_claim,
   ' v_chief boolean:=false;',
   ' v_chief boolean:=false; v_existing_active uuid;');
 IF new_claim=old_claim THEN RAISE EXCEPTION 'Claim declaration changed'; END IF;
 new_claim:=replace(new_claim,
 ' if v_request.invitation_sent_at is not null or v_job.status=''sent'' then',
 ' -- Active account: never send an invitation or recovery reset merely because a request was approved.
   select u.id into v_existing_active from auth.users u
    where lower(u.email)=lower(v_request.email) and u.deleted_at is null
      and (coalesce(length(u.encrypted_password),0)>0
           or nullif(u.raw_app_meta_data->>''password_changed_at'','''') is not null)
    limit 1;
   if v_existing_active is not null then
     return jsonb_build_object(''canSend'',false,''status'',''already_registered'',
       ''acceptedUserId'',v_existing_active);
   end if;
   if v_request.invitation_sent_at is not null or v_job.status=''sent'' then');
 EXECUTE new_claim;

 -- A prior re-approval must not create another oil field for the same chief.
 SELECT pg_get_functiondef(p.oid) INTO old_approval
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.proname='promysel_start_registration_approval';
 IF old_approval IS NULL OR position('target_field=''field-''||gen_random_uuid()::text;' in old_approval)=0
 THEN RAISE EXCEPTION 'Unexpected chief approval function; refusing unsafe change'; END IF;
 new_approval:=replace(old_approval,
    'target_field=''field-''||gen_random_uuid()::text;
     insert into public.oil_fields(id,name) values(target_field,btrim(r.proposed_field_name));',
    'if r.approved_field_id is not null then
       select f.id into target_field from public.oil_fields f
        where f.id=r.approved_field_id and f.archived_at is null;
       if target_field is null then
         raise exception ''Existing approved field unavailable: contact administrator'';
       end if;
     else
       target_field=''field-''||gen_random_uuid()::text;
       insert into public.oil_fields(id,name) values(target_field,btrim(r.proposed_field_name));
     end if;');
 IF new_approval=old_approval THEN RAISE EXCEPTION 'Chief field reuse anchor changed'; END IF;
 EXECUTE new_approval;
END $sql$;

-- Only the trusted backend can query initial-password readiness;
-- the result never exposes a password hash or password material.
CREATE OR REPLACE FUNCTION public.promysel_initial_password_status(p_user_id uuid)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO ''
AS $function$
DECLARE u auth.users%rowtype; ready boolean; approved boolean;
BEGIN
 SELECT * INTO u FROM auth.users WHERE id=p_user_id AND deleted_at IS NULL;
 IF NOT FOUND THEN RETURN jsonb_build_object('userExists',false,'passwordSet',false,'approved',false); END IF;
 ready:=coalesce(length(u.encrypted_password),0)>0
        OR nullif(u.raw_app_meta_data->>'password_changed_at','') IS NOT NULL;
 SELECT EXISTS(
   SELECT 1 FROM public.registration_requests r
   WHERE lower(r.email)=lower(u.email) AND r.state='approved'
     AND r.approved_field_id IS NOT NULL
 ) INTO approved;
 RETURN jsonb_build_object('userExists',true,'passwordSet',ready,'approved',approved);
END $function$;
REVOKE ALL ON FUNCTION public.promysel_initial_password_status(uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_initial_password_status(uuid) TO service_role;
