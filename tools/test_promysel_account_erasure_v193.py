#!/usr/bin/env python3
"""Static contracts for employee Auth deletion, legacy cleanup and scoped UI."""
from pathlib import Path
service=Path('lib/core/services/registration_service.dart').read_text(encoding='utf-8')
session=Path('lib/core/services/session_service.dart').read_text(encoding='utf-8')
admin=Path('lib/features/admin/admin_home_screen.dart').read_text(encoding='utf-8')
personnel=Path('lib/features/organization/personnel_screen.dart').read_text(encoding='utf-8')
checks={
 'chief delete includes the exact field':"'fieldId':fieldId" in service,
 'chief delete includes exact name':"'confirmName':exactName" in service,
 'chief no longer uses bodiless delete':"http.delete(u('/v1/users/'+id),headers:{'authorization':'Bearer '+token})" not in service,
 'chief performs online token refresh':'await ensureFreshToken();\n  final activeToken=api.token;' in session,
 'chief sends server-validated field and name':"currentFieldId??'',target.name" in session,
 'admin legacy route present':"/v1/admin/removed-users/cleanup" in service,
 'admin legacy requires both email fields':"'confirmEmail':confirmEmail" in service,
 'admin legacy requires admin token':"adminCleanupDeletedAccount(_adminToken()" in session,
 'admin form has two email fields':admin.count('keyboardType:TextInputType.emailAddress')>=2,
 'admin UI advertises actual account deletion':"Учётная запись удалена" in admin,
 'chief UI advertises reusable email':"почта доступна для новой регистрации" in personnel,
 'production history remains':"История измерений сохранится" in admin
}
assert all(checks.values()),[k for k,v in checks.items() if not v]
print(f'PASS {len(checks)} v1.93 Flutter account deletion contracts')
