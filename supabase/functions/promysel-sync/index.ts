import { createClient } from "npm:@supabase/supabase-js@2.57.0";
// Promysel v1 cloud delta transport. Old production server remains the fallback.
// This function deliberately does not accept legacy Beget tokens.
const cors: Record<string,string> = {
 "Access-Control-Allow-Origin":"*",
 "Access-Control-Allow-Methods":"GET,POST,OPTIONS",
 "Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info",
 "Content-Type":"application/json; charset=utf-8",
 "Cache-Control":"no-store"
};
function response(body:unknown,status=200):Response {return new Response(JSON.stringify(body),{status,headers:cors});}
const supported=new Set(["measurement","app_state","task","problem","annulus_pressure","training","notification","equipment","repair"]);
const fieldsOnly=(obj:unknown)=>obj!==null&&typeof obj==="object"&&!Array.isArray(obj);
Deno.serve(async (req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 const url=new URL(req.url),path=url.pathname;
 if(path.endsWith("/health")&&req.method==="GET")return response({status:"ok",service:"promysel-sync",stage:"requires-supabase-auth"});
 if(!path.endsWith("/v1/sync/pull")&&!path.endsWith("/v1/sync/push"))return response({detail:"Маршрут не найден"},404);
 const bearer=req.headers.get("authorization")??"";
 const token=bearer.startsWith("Bearer ")?bearer.slice(7).trim():"";
 if(!token)return response({detail:"Требуется вход через Supabase Auth"},401);
 const supabaseUrl=Deno.env.get("SUPABASE_URL")??"";
 const anonKey=Deno.env.get("SUPABASE_ANON_KEY")??"";
 if(!supabaseUrl||!anonKey)return response({detail:"Cloud environment is not configured"},503);
 const client=createClient(supabaseUrl,anonKey,{global:{headers:{Authorization:"Bearer "+token}},auth:{persistSession:false,autoRefreshToken:false}});
 const {data:auth,error:authError}=await client.auth.getUser(token);
 if(authError||!auth.user)return response({detail:"Недействительная сессия Supabase"},401);
 try{
   const body=req.method==="POST"?await req.json():null;
   const fieldId=String(req.method==="GET"?(url.searchParams.get("fieldId")??""):(fieldsOnly(body)?body.fieldId??"":"")).trim();
   if(!fieldId||fieldId.length>128)return response({detail:"Неверное месторождение"},400);
   const {data:membership,error:membershipError}=await client.from("field_memberships")
      .select("role,subrole,approved,blocked").eq("field_id",fieldId).eq("user_id",auth.user.id).maybeSingle();
   if(membershipError)return response({detail:"Проверка доступа к месторождению не удалась"},503);
   if(!membership||!membership.approved||membership.blocked)return response({detail:"Нет допуска к месторождению"},403);
   if(req.method==="GET"){
      const cursorText=url.searchParams.get("cursor")??"0";
      if(!/^\d{1,19}$/.test(cursorText))return response({detail:"Неверный курсор"},400);
      const deviceId=url.searchParams.get("deviceId")??"";
      if(deviceId.length>200)return response({detail:"Неверный идентификатор устройства"},400);
      const {data,error}=await client.from("sync_events")
        .select("sequence,event_key,event_type,client_updated_at,payload,device_id")
        .eq("field_id",fieldId).gt("sequence",Number(cursorText))
        .order("sequence",{ascending:true}).limit(250);
      if(error)throw error;
      const items=(data??[]).filter(x=>x.device_id!==deviceId).map(x=>({
        key:x.event_key,type:x.event_type,updatedAt:x.client_updated_at,payload:x.payload
      }));
      const next=data?.length?String(data[data.length-1].sequence):cursorText;
      return response({cursor:next,items});
   }
   if(req.method!=="POST")return response({detail:"Метод не поддерживается"},405);
   if(!fieldsOnly(body)||!Array.isArray(body.items)||body.items.length<1||body.items.length>100)
     return response({detail:"Список изменений должен содержать от 1 до 100 элементов"},400);
   const deviceId=String(body.deviceId??"").trim();
   if(!deviceId||deviceId.length>200)return response({detail:"Некорректное устройство"},400);
   if(JSON.stringify(body).length>1024*1024)return response({detail:"Максимальный размер запроса — 1 МБ"},413);
   const role=String(membership.role);
   const canWalk=["shopChief","engineer","operator"].includes(role);
   const canEditStructure=["shopChief","engineer","admin"].includes(role);
   const events=[];
   for(const item of body.items){
      if(!fieldsOnly(item)||!fieldsOnly(item.payload))return response({detail:"Некорректный формат изменения"},400);
      const type=String(item.type??""),key=String(item.key??"");
      if(!supported.has(type)||!key||key.length>300)return response({detail:"Некорректный тип или ключ изменения"},400);
      if(type==="measurement"&&!canWalk)return response({detail:"Нет права записывать обход"},403);
      // A full organization snapshot includes structures and personnel and must not be writable by an operator.
      if(type==="app_state"&&!canEditStructure)return response({detail:"Состояние месторождения изменяет только ИТР/начальник"},403);
      if(type==="app_state"&&item.payload.fieldId!==fieldId)return response({detail:"Снимок другого месторождения"},400);
      events.push({event_key:key,field_id:fieldId,device_id:deviceId,event_type:type,
        payload:item.payload,actor_id:auth.user.id,client_updated_at:item.updatedAt??null});
   }
   const {error}=await client.from("sync_events").upsert(events,{onConflict:"event_key",ignoreDuplicates:true});
   if(error)throw error;
   return response({accepted:events.map(x=>x.event_key),server_time:new Date().toISOString()});
 }catch(e){
   console.error("promysel-sync:",e instanceof Error?e.message:String(e));
   return response({detail:"Не удалось выполнить операцию с облачной базой"},500);
 }
});
