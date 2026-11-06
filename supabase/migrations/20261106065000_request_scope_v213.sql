-- v2.13: one security-invoker lookup for Supabase session, profile,
-- live memberships and permitted fields.
-- Claims MUST first be verified with supabase.auth.getClaims(jwt) (ES256).
-- The JWT session_id is checked against auth.sessions at EACH request;
-- revoked logins and membership changes remain effective immediately.
CREATE OR REPLACE FUNCTION public.promysel_request_scope_v213(
 p_user_id uuid,p_session_id uuid
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path TO ''
AS $function$
DECLARE
 v_user auth.users%rowtype;
 v_admin boolean;
 v_memberships jsonb;
 v_fields jsonb;
BEGIN
 IF p_user_id IS NULL OR p_session_id IS NULL THEN
   RETURN NULL;
 END IF;
 SELECT u.* INTO v_user FROM auth.users u
   WHERE u.id=p_user_id AND u.deleted_at IS NULL
     AND EXISTS(
       SELECT 1 FROM auth.sessions s
       WHERE s.id=p_session_id AND s.user_id=u.id
     );
 IF NOT FOUND THEN RETURN NULL; END IF;

 v_admin:=coalesce(v_user.raw_app_meta_data->>'system_admin'='true',false);

 SELECT coalesce(jsonb_agg(jsonb_build_object(
   'field_id',m.field_id,
   'role',m.role,
   'subrole',m.subrole,
   'display_name',m.display_name,
   'approved',m.approved,
   'blocked',m.blocked
 ) ORDER BY m.field_id),'[]'::jsonb)
 INTO v_memberships
 FROM public.field_memberships m
 JOIN public.oil_fields f ON f.id=m.field_id AND f.archived_at IS NULL
 WHERE m.user_id=p_user_id AND m.approved AND NOT m.blocked;

 IF v_admin THEN
   SELECT coalesce(jsonb_agg(f.id ORDER BY f.id),'[]'::jsonb)
     INTO v_fields FROM public.oil_fields f WHERE f.archived_at IS NULL;
 ELSE
   v_fields:='[]'::jsonb;
 END IF;

 RETURN jsonb_build_object(
   'user',jsonb_build_object(
     'id',v_user.id,
     'email',v_user.email,
     'app_metadata',coalesce(v_user.raw_app_meta_data,'{}'::jsonb),
     'user_metadata',coalesce(v_user.raw_user_meta_data,'{}'::jsonb)
   ),
   'memberships',v_memberships,
   'admin_field_ids',v_fields
 );
END $function$;

REVOKE ALL ON FUNCTION public.promysel_request_scope_v213(uuid,uuid)
 FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_request_scope_v213(uuid,uuid) TO service_role;
