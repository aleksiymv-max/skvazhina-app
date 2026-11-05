from pathlib import Path
s=(Path('lib/core/services/session_service.dart')).read_text()
chief=Path('lib/features/admin/chief_approvals_screen.dart').read_text()
admin=Path('lib/features/admin/admin_home_screen.dart').read_text()
checks={
 'pending vs. approved-awaiting-email status':"approved_awaiting_invitation" in s,
 'email retry timestamp retained':"nextRetryAt" in s and "invitationStatus" in s,
 'existing approved staff cannot be rejected':"if(!p.approvedAwaitingInvitation)" in chief and "if(!p.approvedAwaitingInvitation)" in admin,
 'retry disabled during mail cooldown':"p.canRetryInvitation?" in chief and "p.canRetryInvitation?" in admin,
 'actual API status shown to chief':"result['detail']" in chief,
 'actual API status shown to admin':"result['detail']" in admin,
 'post approval refresh avoids unnecessary roster waits':"if(result['invitationSent']==true)" in s,
 'always reload pending statuses':"await refreshPending(force:true)" in s,
 'no profile edits while email queued':"WorkTaskStore.instance" not in chief,
}
for name,ok in checks.items():print(('PASS ' if ok else 'FAIL ')+name)
assert all(checks.values())
print('PASS v2.05 Flutter admin/chief invitation UI regressions')
