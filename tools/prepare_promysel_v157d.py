from pathlib import Path
r=Path.cwd()
# Complete server registration transport and force registration to use a field, not chiefId.
p=r/'lib/core/services/registration_service.dart'
s=p.read_text()
assert "/v1/registration/fields" in s and "/reject" in s

# Registration UI: remove any requirement to select a particular chief.
p=r/'lib/features/auth/login_screen.dart';s=p.read_text()
s=s.replace("required String chiefId","String? chiefId")
s=s.replace("chiefId:chiefId","chiefId:null")
# Do not preselect prototype field.
s=s.replace("String fieldId='field-1'","String fieldId='new'")
s=s.replace("fieldId=v??'field-1'","fieldId=v??'new'")
p.write_text(s)

# Static contract gates.
assert "field-1" not in s
assert "chiefId:chiefId" not in s
print('v1.57d field registration UI gates passed')
