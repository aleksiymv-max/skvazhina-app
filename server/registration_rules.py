"""Registration domain rules. Server is authoritative."""
ALLOWED_EMPLOYEE_ROLES={"operator","dispatcher","engineer"}
ADMIN_ROLE="admin"
CHIEF_ROLE="shopChief"

def validate_chief_application(data, field=None):
    email=(data.get("email") or "").strip().lower()
    name=(data.get("name") or "").strip()
    if data.get("role")!=CHIEF_ROLE: raise ValueError("Некорректная роль начальника")
    if "@" not in email or not name: raise ValueError("Заполните ФИО и e-mail")
    existing=data.get("fieldId")
    new_name=(data.get("newFieldName") or "").strip()
    if bool(existing)==bool(new_name): raise ValueError("Выберите существующее или укажите новое месторождение")
    if existing and (not field or not field.get("approved")): raise ValueError("Месторождение недоступно")
    return email,name

def validate_employee_application(data, field):
    role=data.get("role")
    if role not in ALLOWED_EMPLOYEE_ROLES: raise ValueError("Недопустимая производственная роль")
    if not field or not field.get("approved") or data.get("fieldId")!=field.get("id"): raise ValueError("Выберите подтвержденное месторождение")
    return True

def may_decide(actor, request):
    if request.get("status")!="pending": return False
    if request.get("requested_role")==CHIEF_ROLE:
        return actor.get("role")==ADMIN_ROLE
    return actor.get("role")==CHIEF_ROLE and actor.get("approved") and not actor.get("blocked") and request.get("field_id")==actor.get("field_id")

def public_field(field):
    return bool(field and field.get("approved"))

def can_login(user):
    return bool(user and user.get("approved") and not user.get("blocked"))
