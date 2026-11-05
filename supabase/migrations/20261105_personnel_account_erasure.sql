-- Personnel account erasure v1.93. Historical production records and chat message text
-- are retained but the departed author's auth UUID becomes NULL.
-- Employee-specific access, presence and chat membership are cascaded.
-- No existing rows are deleted by this migration.
SET lock_timeout = '5s';
ALTER TABLE public.field_records ALTER COLUMN created_by DROP NOT NULL;
ALTER TABLE public.field_records DROP CONSTRAINT IF EXISTS field_records_created_by_fkey;
ALTER TABLE public.field_records ADD CONSTRAINT field_records_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.field_records DROP CONSTRAINT IF EXISTS field_records_owner_id_fkey;
ALTER TABLE public.field_records ADD CONSTRAINT field_records_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.measurement_corrections ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE public.measurement_corrections DROP CONSTRAINT IF EXISTS measurement_corrections_actor_id_fkey;
ALTER TABLE public.measurement_corrections ADD CONSTRAINT measurement_corrections_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.personnel_audit ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE public.personnel_audit DROP CONSTRAINT IF EXISTS personnel_audit_actor_id_fkey;
ALTER TABLE public.personnel_audit ADD CONSTRAINT personnel_audit_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.personnel_audit DROP CONSTRAINT IF EXISTS personnel_audit_target_user_id_fkey;
ALTER TABLE public.personnel_audit ADD CONSTRAINT personnel_audit_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.record_action_audit ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE public.record_action_audit DROP CONSTRAINT IF EXISTS record_action_audit_actor_id_fkey;
ALTER TABLE public.record_action_audit ADD CONSTRAINT record_action_audit_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.registration_requests DROP CONSTRAINT IF EXISTS registration_requests_decided_by_fkey;
ALTER TABLE public.registration_requests ADD CONSTRAINT registration_requests_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.registration_requests DROP CONSTRAINT IF EXISTS registration_requests_requested_by_fkey;
ALTER TABLE public.registration_requests ADD CONSTRAINT registration_requests_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.sync_events ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE public.sync_events DROP CONSTRAINT IF EXISTS sync_events_actor_id_fkey;
ALTER TABLE public.sync_events ADD CONSTRAINT sync_events_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.walk_measurements ALTER COLUMN actor_id DROP NOT NULL;
ALTER TABLE public.walk_measurements DROP CONSTRAINT IF EXISTS walk_measurements_actor_id_fkey;
ALTER TABLE public.walk_measurements ADD CONSTRAINT walk_measurements_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.promysel_chat_messages ALTER COLUMN sender_id DROP NOT NULL;
ALTER TABLE public.promysel_chat_messages DROP CONSTRAINT IF EXISTS promysel_chat_messages_sender_id_fkey;
ALTER TABLE public.promysel_chat_messages ADD CONSTRAINT promysel_chat_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.promysel_chat_rooms ALTER COLUMN created_by DROP NOT NULL;
ALTER TABLE public.promysel_chat_rooms DROP CONSTRAINT IF EXISTS promysel_chat_rooms_created_by_fkey;
ALTER TABLE public.promysel_chat_rooms ADD CONSTRAINT promysel_chat_rooms_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.promysel_chat_members DROP CONSTRAINT IF EXISTS promysel_chat_members_user_id_fkey;
ALTER TABLE public.promysel_chat_members ADD CONSTRAINT promysel_chat_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.promysel_daily_presence ALTER COLUMN changed_by DROP NOT NULL;
ALTER TABLE public.promysel_daily_presence DROP CONSTRAINT IF EXISTS promysel_daily_presence_changed_by_fkey;
ALTER TABLE public.promysel_daily_presence ADD CONSTRAINT promysel_daily_presence_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.promysel_daily_presence DROP CONSTRAINT IF EXISTS promysel_daily_presence_user_id_fkey;
ALTER TABLE public.promysel_daily_presence ADD CONSTRAINT promysel_daily_presence_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE app_private.admin_setup_invites DROP CONSTRAINT IF EXISTS admin_setup_invites_used_by_fkey;
ALTER TABLE app_private.admin_setup_invites ADD CONSTRAINT admin_setup_invites_used_by_fkey FOREIGN KEY (used_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.personnel_audit DROP CONSTRAINT IF EXISTS personnel_audit_request_id_fkey;
ALTER TABLE public.personnel_audit ADD CONSTRAINT personnel_audit_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.registration_requests(id) ON DELETE SET NULL;
COMMENT ON COLUMN public.promysel_chat_messages.sender_id IS 'NULL means that the sender account was permanently removed; message retained for other participants';
