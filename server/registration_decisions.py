"""Transactional decisions for registration requests."""
from registration_rules import may_decide

class DecisionConflict(Exception): pass
class DecisionForbidden(Exception): pass

def decide_in_memory(actor, request, decision):
    # Mirrors the DB transaction contract: SELECT ... FOR UPDATE, then status check.
    if request.get("status")!="pending": raise DecisionConflict("Заявка уже обработана")
    if not may_decide(actor,request): raise DecisionForbidden("Нет прав на обработку заявки")
    if decision not in ("approved","rejected"): raise ValueError("Некорректное решение")
    request["status"]=decision
    request["approved_by"]=actor["id"]
    return request

def approval_transaction_sql():
    return """SELECT id,status,requested_role,field_id,creates_new_field
FROM registration_requests WHERE id=%s FOR UPDATE"""
