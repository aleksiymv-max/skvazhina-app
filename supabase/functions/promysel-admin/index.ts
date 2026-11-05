import { createClient } from "npm:@supabase/supabase-js@2.57.0";
const project="https://xptmcufhuvtcunqzlsme.supabase.co";
const cors={"Access-Control-Allow-Origin":"*","Vary":"Origin","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
const json=(v:unknown,status=200)=>new Response(JSON.stringify(v),{status,headers:cors});
type AuthUser={id:string,app_metadata?:Record<string,unknown>,email?:string};
Deno.serve(async (request:Request)=>{
 if(request.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 const route=new URL(request.url).pathname.split("/").filter(Boolean).at(-1)??"";
 const bearer=request.headers.get("authorization")??"";
 const token=bearer.startsWith("Bearer ")?bearer.slice(7).trim():"";
 if(!token)return json({detail:"Требуется вход через Supabase Auth"},401);
 const url=Deno.env.get("SUPABASE_URL")??"",anon=Deno.env.get("SUPABASE_ANON_KEY")??"";
 const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
 if(!url||!anon||!service)return json({detail:"Сервер авторизации не настроен"},503);
 const client=createClient(url,anon,{global:{headers:{Authorization:"Bearer "+token}},auth:{persistSession:false,autoRefreshToken:false}});
 const {data,error}=await client.auth.getUser(token);
 if(error||!data.user)return json({detail:"Неверная или истекшая сессия"},401);
 const actor:AuthUser=data.user;
 const elevated=actor.app_metadata?.system_admin===true;
 const admin=createClient(url,service,{auth:{persistSession:false,autoRefreshToken:false}});
 try{
  if(request.method==="GET"&&route==="directory"){
   const {data,error}=await admin.from("oil_fields").select("id,name").order("name").limit(200);
   if(error)throw error;
   return json({items:data??[]});
  }
  if(request.method==="GET"&&route==="pending"){
   const fieldId=new URL(request.url).searchParams.get("fieldId")?.trim()??"";
   if(!fieldId&&!elevated)return json({detail:"Не выбрано месторождение"},400);
   if(!elevated){
     const {data:membership,error:membershipError}=await admin.from("field_memberships")
       .select("role,approved,blocked").eq("user_id",actor.id).eq("field_id",fieldId).maybeSingle();
     if(membershipError)throw membershipError;
     if(!membership||membership.role!=="shopChief"||!membership.approved||membership.blocked)
       return json({detail:"Только начальник цеха рассматривает заявки сотрудников"},403);
   }
   let q=admin.from("registration_requests")
    .select("id,requested_by,field_id,proposed_field_name,requested_role,requested_subrole,full_name,email,state,created_at")
    .or("state.eq.pending,and(state.eq.approved,approved_field_id.not.is.null,invitation_sent_at.is.null)").order("created_at",{ascending:true}).limit(100);
   if(!elevated)q=q.eq("field_id",fieldId);
   const {data,error}=await q;
   if(error)throw error;
   return json({items:data??[]});
  }
  if(request.method!=="POST")return json({detail:"Метод не поддерживается"},405);
  const body=await request.json();
  if(!body||typeof body!=="object"||Array.isArray(body))return json({detail:"Некорректный запрос"},400);
  // First-run bootstrap: no user gets administrator privileges by self-registration.
  // The service-only PostgreSQL RPC verifies the one-time invite and confirmed e-mail atomically.
  if(route==="claim-bootstrap"){
    const setupCode=typeof body.code==="string"?body.code:"";
    if(setupCode.length<20||setupCode.length>200)return json({detail:"Некорректный код настройки"},400);
    const {data,error}=await admin.rpc("promysel_claim_initial_admin",{p_actor:actor.id,p_code:setupCode});
    if(error)return json({detail:error.message},403);
    return json(data);
  }
  if(route==="first-password"){
    // Never trust user-editable metadata for access; use Auth's app_metadata and re-check
    // the current temporary password before setting the new password server-side.
    if(request.method!=="POST")return json({detail:"Метод не поддерживается"},405);
    if(actor.app_metadata?.must_change_password!==true)return json({detail:"Первичная смена пароля уже выполнена"},409);
    const oldPassword=typeof body.currentPassword==="string"?body.currentPassword:"";
    const newPassword=typeof body.newPassword==="string"?body.newPassword:"";
    if(oldPassword.length<8||newPassword.length<12||newPassword.length>128||oldPassword===newPassword)
      return json({detail:"Новый пароль должен отличаться от временного и содержать 12–128 символов"},400);
    if(!actor.email)return json({detail:"Не указан адрес учётной записи"},400);
    const verifier=createClient(url,anon,{auth:{persistSession:false,autoRefreshToken:false}});
    const {error:verificationError}=await verifier.auth.signInWithPassword({email:actor.email,password:oldPassword});
    if(verificationError)return json({detail:"Неверный временный пароль"},401);
    const metadata={...actor.app_metadata,must_change_password:false,password_changed_at:new Date().toISOString()};
    const {error:changeError}=await admin.auth.admin.updateUserById(actor.id,{
      password:newPassword,app_metadata:metadata
    });
    if(changeError)return json({detail:"Пароль не изменён. Проверьте требования безопасности: "+changeError.message},400);
    return json({status:"password_changed",mustChangePassword:false});
  }
  if(actor.app_metadata?.must_change_password===true)
    return json({detail:"Сначала необходимо изменить временный пароль"},403);
  if(route==="task-complete"||route==="problem-application"){
    const recordId=String(body.recordId??"").trim();
    if(!recordId||recordId.length>300)return json({detail:"Некорректный номер записи"},400);
    const operation=route==="task-complete"?"promysel_mark_task_done":"promysel_submit_problem_application";
    const {data,error}=await admin.rpc(operation,{p_record:recordId,p_actor:actor.id});
    if(error)return json({detail:error.message},403);
    return json(data);
  }
  if(route==="approve"||route==="reject"){
   const n=Number(body.requestId);
   if(!Number.isSafeInteger(n)||n<=0)return json({detail:"Некорректный номер заявки"},400);
   if(route==="reject"){
      const {data,error}=await admin.rpc("promysel_reject_registration",{
        p_request_id:n,p_actor:actor.id,p_note:String(body.note??"").slice(0,1000)
      });
      if(error)return json({detail:error.message},403);
      return json(data);
   }
   const {data:decision,error:decisionError}=await admin.rpc("promysel_start_registration_approval",{
     p_request_id:n,p_actor:actor.id
   });
   if(decisionError)return json({detail:decisionError.message},403);
   const {data:claim,error:claimError}=await admin.rpc("promysel_claim_registration_invitation",{
     p_request_id:n,p_actor:actor.id
   });
   if(claimError){
     console.error("admin invite claim",claimError.code??"unknown");
     return json({status:"approved",invitationSent:false,
       detail:"Заявка согласована. Не удалось проверить очередь приглашений."},202);
   }
   if(claim?.status==="sent")return json({status:"approved",invitationSent:true});
   const acceptedId=String(claim?.acceptedUserId??"");
   if(!claim?.canSend&&!acceptedId)return json({status:"approved",invitationSent:false,
     invitationStatus:String(claim?.status??"queued"),nextRetryAt:claim?.nextRetryAt??null,
     detail:"Заявка согласована. Отправка приглашения ожидает очереди либо настройки SMTP."},202);
   let userId=acceptedId;
   if(!userId){
     userId=String(decision?.existingUserId??"");
     let deliveryError:unknown=null;
     if(!userId){
       const {data:invited,error:inviteError}=await admin.auth.admin.inviteUserByEmail(
         String(decision.email),{
         data:{full_name:decision.fullName},
         redirectTo:"https://promysel-app.tuqo.ru/finish-registration.html"
       });
       if(inviteError||!invited?.user)deliveryError=inviteError??new Error("invite_user_missing");
       else userId=invited.user.id;
     }else{
       const {error:resetError}=await client.auth.resetPasswordForEmail(String(decision.email),{
         redirectTo:"https://promysel-app.tuqo.ru/finish-registration.html"
       });
       if(resetError)deliveryError=resetError;
     }
     if(deliveryError){
       const e=deliveryError&&typeof deliveryError==="object"
         ?deliveryError as Record<string,unknown>:{};
       const message=String(e.message??"").toLowerCase();
       const code=e.status===429||message.includes("rate limit")
         ?"over_email_send_rate_limit":message.includes("not authorized")||message.includes("smtp")
         ?"email_configuration_required":"mail_delivery_failed";
       const type=code==="email_configuration_required"?"action_required":"retry";
       const {error:recordError}=await admin.rpc("promysel_record_registration_invitation",{
         p_request_id:n,p_actor:actor.id,p_status:type,p_error_code:code
       });
       if(recordError)console.warn("admin invitation retry bookkeeping",recordError.code??"unknown");
       return json({status:"approved",invitationSent:false,invitationStatus:type,
         detail:"Заявка согласована. Письмо в очереди отправки; проверьте почтовые ограничения."},202);
     }
     if(!userId)return json({status:"approved",invitationSent:false,
       detail:"Письмо в процессе отправки. Сотрудник ещё не активирован."},202);
     const {error:recordError}=await admin.rpc("promysel_record_registration_invitation",{
       p_request_id:n,p_actor:actor.id,p_status:"accepted",p_user_id:userId
     });
     if(recordError){
       console.error("admin invite accepted bookkeeping",recordError.code??"unknown");
       return json({status:"approved",invitationSent:false,
         detail:"Письмо принято, завершение учётной записи ожидает повторной проверки."},202);
     }
   }
   const {data:finalized,error:finalizeError}=await admin.rpc("promysel_finish_registration_approval",{
     p_request_id:n,p_actor:actor.id,p_user_id:userId
   });
   if(finalizeError){
     console.error("admin invite finalization",finalizeError.code??"unknown");
     return json({status:"approved",invitationSent:true,invitationStatus:"accepted",
       detail:"Письмо отправлено, но активация сотрудника не завершена."},202);
   }
   const {error:completionError}=await admin.rpc("promysel_record_registration_invitation",{
     p_request_id:n,p_actor:actor.id,p_status:"sent",p_user_id:userId
   });
   if(completionError)console.warn("admin invite completion bookkeeping",completionError.code??"unknown");
   return json({...finalized,invitationSent:true,invitationStatus:"sent",
     detail:"Согласование завершено. Письмо передано почтовому сервису."});
  }
  if(route==="change-role"){
   const field=String(body.fieldId??""),target=String(body.userId??""),role=String(body.role??"");
   if(!field||!target||!role)return json({detail:"Недостаточно данных"},400);
   const {data,error}=await admin.rpc("promysel_change_role",{
     p_field:field,p_actor:actor.id,p_target:target,p_role:role,p_subrole:body.subrole??null
   });
   if(error)return json({detail:error.message},403);
   return json(data);
  }
  if(route==="block-worker"){
   const field=String(body.fieldId??""),target=String(body.userId??"");
   if(!field||!target||typeof body.blocked!=="boolean")return json({detail:"Недостаточно данных"},400);
   const {data,error}=await admin.rpc("promysel_set_worker_blocked",{
     p_field:field,p_actor:actor.id,p_target:target,p_blocked:body.blocked
   });
   if(error)return json({detail:error.message},403);
   return json(data);
  }
  return json({detail:"Маршрут не найден"},404);
 }catch(e){console.error("promysel-admin:",e instanceof Error?e.message:String(e));return json({detail:"Ошибка обработки запроса"},500)}
});
