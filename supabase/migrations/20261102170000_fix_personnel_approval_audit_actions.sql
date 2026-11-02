-- The two-phase registration workflow records decisions and account creation separately.
-- Keep the existing audit whitelist; add the two actions used by the approved RPCs.
ALTER TABLE public.personnel_audit
  DROP CONSTRAINT IF EXISTS personnel_audit_action_check;
ALTER TABLE public.personnel_audit
  ADD CONSTRAINT personnel_audit_action_check CHECK (
    action = ANY (ARRAY[
      'approve'::text, 'reject'::text, 'role_change'::text,
      'block'::text, 'unblock'::text,
      'approve_request'::text, 'approved_account_created'::text
    ])
  );
