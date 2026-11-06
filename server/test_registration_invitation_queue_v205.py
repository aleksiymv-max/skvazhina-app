"""Registration delivery regression: approvals independent of email sends."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
compat=(root/'supabase/functions/promysel-compat/index.ts').read_text()
admin=(root/'supabase/functions/promysel-admin/index.ts').read_text()
migration=(root/'supabase/migrations/20261105160500_registration_invitation_queue_v205.sql').read_text()
for label,source in [('chief API',compat),('admin API',admin)]:
    assert 'promysel_claim_registration_invitation' in source,label
    assert 'promysel_record_registration_invitation' in source,label
    assert 'over_email_send_rate_limit' in source,label
    assert 'invitationSent:false' in source,label
    assert 'invitationStatus:' in source,label
    assert 'p_status:"accepted"' in source,label
    assert 'p_status:"sent"' in source,label
    assert source.index('promysel_claim_registration_invitation') < source.index('inviteUserByEmail'),label
    # v2.12 added a safe "already registered" path that finalizes access before
    # marking its mail job accepted, without creating a new email. For genuinely
    # new invitations, the LAST accepted marker must precede finalization.
    assert source.rindex('p_status:"accepted"') < source.rindex('promysel_finish_registration_approval'),label
    assert 'claim?.status==="already_registered"' in source,label
assert 'next_available_at=now()+interval ' in migration
assert 'for update' in migration.lower()
assert 'status in(' in migration
assert 'revoke all on public.promysel_registration_invitation_jobs from public,anon,authenticated' in migration
assert 'grant select,insert,update on public.promysel_registration_invitation_jobs to service_role' in migration
assert 'grant execute on function public.promysel_claim_registration_invitation(bigint,uuid)' in migration
assert "action_required" in migration
print('PASS v2.05: approval decision durable, provider mail queued/throttled, delivery acceptance before membership finalization')
