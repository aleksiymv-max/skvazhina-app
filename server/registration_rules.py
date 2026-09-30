"""Registration domain rules used by FastAPI routes.
No Flutter/UI permission is trusted here.
"""
ALLOWED_EMPLOYEE_ROLES={"operator","dispatcher","engineer"}
ADMIN_ROLE="admin"
CHIEF_ROLE="shopChief"

def validate_chief_application(data):
    email=(data.get("email") or "").strip().lower()
    name=(data.get("name") or "").strip()
    field=(data.get("newFieldName") or "").strip()
    if data.get("role")!=CHIEF_ROLE: raise ValueError("Некорректная роль начальника")
    if "@" not in email or not name or not field: raise ValueError("Заполните ФИО, e-mail и месторождение")
    return email,name,field

def validate_employee_application(data, chief):
    role=data.get("role")
    if role not in ALLOWED_EMPLOYEE_ROLES: raise ValueError("Недопустимая производственная роль")
    if not chief or not chief.get("approved") or chief.get("role")!=CHIEF_ROLE: raise ValueError("Начальник не подтвержден")
    if data.get("chiefId")!=chief.get("id") or data.get("fieldId")!=chief.get("field_id"): raise PermissionError("Начальник относится к другому месторождению")
    return True

def may_decide(actor, request):
    if request.get("status")!="pending": return False
    if request.get("requested_role")==CHIEF_ROLE:
        return actor.get("role")==ADMIN_ROLE
    return actor.get("role")==CHIEF_ROLE and request.get("chief_id")==actor.get("id") and request.get("field_id")==actor.get("field_id")

def public_field(field,chief):
    return bool(field and field.get("approved") and chief and chief.get("approved") and chief.get("role")==CHIEF_ROLE and field.get("chief_user_id")==chief.get("id"))

def can_login(user):
    return bool(user and user.get("approved") and not user.get("blocked"))
