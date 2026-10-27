import { createClient } from "npm:@supabase/supabase-js@2.57.0";
const project="https://xptmcufhuvtcunqzlsme.supabase.co";
const cors={"Access-Control-Allow-Origin":project,"Vary":"Origin","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
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
    .eq("state","pending").order("created_at",{ascending:true}).limit(100);
   if(!elevated)q=q.eq("field_id",fieldId);
   const {data,error}=await q;
   if(error)throw error;
   return json({items:data??[]});
  }
  if(request.method!=="POST")return json({detail:"Метод не поддерживается"},405);
  const body=await request.json();
  if(!body||typeof body!=="object"||Array.isArray(body))return json({detail:"Некорректный запрос"},400);
  if(route==="approve"||route==="reject"){
   const n=Number(body.requestId);
   if(!Number.isSafeInteger(n)||n<=0)return json({detail:"Некорректный номер заявки"},400);
   const op=route==="approve"?"promysel_approve_registration":"promysel_reject_registration";
   const vars=route==="approve"?{p_request_id:n,p_actor:actor.id}:{p_request_id:n,p_actor:actor.id,p_note:String(body.note??"").slice(0,1000)};
   const {data,error}=await admin.rpc(op,vars);
   if(error)return json({detail:error.message},error.code==="42501"?403:409);
   return json(data);
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
