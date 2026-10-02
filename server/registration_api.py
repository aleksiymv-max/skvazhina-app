"""FastAPI registration router. Mount with app.include_router(router)."""
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
router=APIRouter(prefix='/v1')
_service=None; _actor=None

def configure(service,actor_provider):
 global _service,_actor;_service=service;_actor=actor_provider
def service():
 if _service is None: raise RuntimeError('registration API is not configured')
 return _service
def actor():
 if _actor is None: raise HTTPException(503,'Авторизация сервера не настроена')
 return _actor()

class Application(BaseModel):
 name:str; email:str; role:str; subrole:str|None=None; fieldId:str|None=None; newFieldName:str|None=None
class Decision(BaseModel):
 role:str|None=None; subrole:str|None=None
class Login(BaseModel):
 login:str; password:str
class PasswordChange(BaseModel):
 password:str

@router.get('/registration/fields')
def fields(): return {'items':service().directory()}
@router.post('/registration/apply')
def apply(x:Application):
 try:return service().apply(x.model_dump())
 except (ValueError,PermissionError) as e:raise HTTPException(400,str(e))
@router.get('/registration/pending')
def pending(a=Depends(actor)):return {'items':service().pending(a)}
@router.post('/registration/{request_id}/approve')
def approve(request_id:str,x:Decision,a=Depends(actor)):
 try:return service().decide(a,request_id,True,x.role,x.subrole)
 except PermissionError as e:raise HTTPException(403,str(e))
 except (RuntimeError,ValueError) as e:raise HTTPException(409,str(e))
@router.post('/registration/{request_id}/reject')
def reject(request_id:str,a=Depends(actor)):
 try:return service().decide(a,request_id,False)
 except PermissionError as e:raise HTTPException(403,str(e))
 except (RuntimeError,ValueError) as e:raise HTTPException(409,str(e))
@router.post('/auth/login')
def login(x:Login):
 try:return service().login(x.login,x.password)
 except PermissionError as e:raise HTTPException(401,str(e))
@router.post('/auth/first-password')
def first_password(x:PasswordChange,a=Depends(actor)):
 if len(x.password)<8:raise HTTPException(400,'Пароль должен содержать не менее 8 символов')
 try:return service().change_password(a,x.password)
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(409,str(e))
