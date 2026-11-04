from pathlib import Path
x=Path('lib/features/auth/login_screen.dart').read_text(encoding='utf-8')
s=Path('lib/core/services/session_service.dart').read_text(encoding='utf-8')
r=Path('lib/core/services/registration_service.dart').read_text(encoding='utf-8')
assert 'SessionService.instance.addListener(_onFieldsUpdated)' in x
assert 'SessionService.instance.removeListener(_onFieldsUpdated)' in x
assert "_fieldManuallyChosen" in x
assert "options.first.id" in x
assert "onPressed:_fieldsLoading?null:_fetchFields" in x
assert "Сначала выберите действующее месторождение" in x
assert "RegistrationService.instance.fields()" in s
assert "/v1/registration/fields" in r
assert "role!=UserRole.shopChief" in x
print('PASS registration existing-field regression')
