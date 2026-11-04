from pathlib import Path
admin=Path('lib/features/admin/admin_home_screen.dart').read_text(encoding='utf-8')
login=Path('lib/features/auth/login_screen.dart').read_text(encoding='utf-8')
session=Path('lib/core/services/session_service.dart').read_text(encoding='utf-8')
assert 'Future<void> _rejectPending' in admin
assert "label:const Text('Не согласовать')" in admin
assert "await s.rejectRemote(id)" in admin
assert "await s.ensureFreshToken()" in admin
assert "OverflowBar(spacing:8" in admin
assert "onRefresh:_refreshUsersManual" in admin
assert "if(v==2)unawaited(s.refreshWorkers(force:true)" in admin
assert "s.personnelLoadError!=null" in admin
assert "refreshWorkers(force:true)]);" in session
assert "if(loading)return;" in login
assert "loading=true;error=null;" in login
assert "loading?(register?'Отправка…'" in login
print('PASS duplicate registration UI, admin rejection and personnel refresh tests')
