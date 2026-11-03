import { createClient } from "npm:@supabase/supabase-js@2.57.0";

// Private task photo API: Supabase Auth bearer + membership + task/phase authorization.
// Never expose the service role to clients or use a public Storage bucket.
const cors: Record<string,string> = {
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info",
  "Access-Control-Allow-Methods":"GET,POST,OPTIONS",
  "Content-Type":"application/json; charset=utf-8",
  "Cache-Control":"no-store",
};
const response=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:cors});
const url=Deno.env.get("SUPABASE_URL")??"";
const publicKey=Deno.env.get("SUPABASE_ANON_KEY")??"";
const serverKey=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
const bucket="promysel-task-photos";
const VALID_ID=/^[a-zA-Z0-9_-]{1,128}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const MIMES=new Set(["image/jpeg","image/png","image/webp"]);
type Row=Record<string,any>;
function text(x:unknown,n=128){return typeof x==="string"?x.trim().slice(0,n):"";}
function authorizedRead(actor:string,member:Row,task:Row){
  return member.role==="shopChief" || task.created_by===actor ||
    (task.target_type==="personal"?task.target_id===actor:
      ["operator","engineer","shopChief","dispatcher"].includes(member.role));
}
function authorizedWrite(actor:string,member:Row,task:Row,phase:string){
  if(phase==="assignment")return task.created_by===actor;
  if(phase!=="completion")return false;
  return task.target_type==="personal" ? task.target_id===actor :
    ["operator","engineer","shopChief","dispatcher"].includes(member.role);
}
function imageMagic(bytes:Uint8Array,mime:string) {
 if(mime==="image/jpeg")return bytes.length>3&&bytes[0]===0xff&&bytes[1]===0xd8&&bytes[2]===0xff;
 if(mime==="image/png")return bytes.length>8&&[137,80,78,71,13,10,26,10].every((b,i)=>bytes[i]===b);
 if(mime==="image/webp")return bytes.length>12&&String.fromCharCode(...bytes.slice(0,4))==="RIFF"&&String.fromCharCode(...bytes.slice(8,12))==="WEBP";
 return false;
}
Deno.serve(async(req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 if(!url||!publicKey||!serverKey)return response({detail:"Сервер фотографий не настроен"},503);
 const route=new URL(req.url).pathname.replace(/^.*?\/promysel-task-photos/,"")||"/";
 if(route==="/health"&&req.method==="GET")return response({status:"ok",service:"promysel-task-photos"});
 const authorization=req.headers.get("authorization")??"";
 const token=authorization.startsWith("Bearer ")?authorization.substring(7).trim():"";
 if(!token)return response({detail:"Для загрузки фотографий необходимо войти"},401);
 const guest=createClient(url,publicKey,{auth:{persistSession:false,autoRefreshToken:false}});
 const admin=createClient(url,serverKey,{auth:{persistSession:false,autoRefreshToken:false}});
 try{
  const {data:auth,error:authError}=await guest.auth.getUser(token);
  if(authError||!auth.user)return response({detail:"Сессия истекла. Войдите повторно."},401);
  const user=auth.user;
  if(user.app_metadata?.must_change_password===true)return response({detail:"Сначала измените временный пароль"},403);
  const actor=user.id;
  const memberCache=new Map<string,Row|null>();
  async function memberOf(fieldId:string):Promise<Row|null>{
   if(memberCache.has(fieldId))return memberCache.get(fieldId)??null;
   const {data,error}=await admin.from("field_memberships")
    .select("role,subrole,field_id,approved,blocked")
    .eq("user_id",actor).eq("field_id",fieldId).eq("approved",true).eq("blocked",false).maybeSingle();
   if(error)throw error;memberCache.set(fieldId,data);return data;
  }
  async function snapshot(fieldId:string):Promise<Row|null>{
   const {data,error}=await admin.from("sync_events").select("payload")
     .eq("field_id",fieldId).eq("event_type","app_state")
     .order("sequence",{ascending:false}).limit(1).maybeSingle();
   if(error)throw error;
   return data?.payload && typeof data.payload==="object"?data.payload:null;
  }
  async function findTask(fieldId:string,taskId:string){
   const {data,error}=await admin.from("promysel_task_photo_registry")
    .select("field_id,task_id,created_by,target_type,target_id")
    .eq("field_id",fieldId).eq("task_id",taskId).maybeSingle();
   if(error)throw error;
   if(data)return data as Row;
   // Legacy tasks were stored in the app_state snapshot. Import only if a
   // previously authorized sync event actually contains this exact task.
   const state=await snapshot(fieldId);
   const source=Array.isArray(state?.tasks)?state.tasks.find((t:Row)=>t?.id===taskId):null;
   if(!source||!UUID.test(text(source.createdById,64))||
      !["personal","area","pad"].includes(source.targetType)||
      !VALID_ID.test(text(source.targetId)))return null;
   const record={field_id:fieldId,task_id:taskId,created_by:source.createdById,
      target_type:source.targetType,target_id:source.targetId};
   const {error:insertError}=await admin.from("promysel_task_photo_registry")
       .upsert(record,{onConflict:"field_id,task_id",ignoreDuplicates:true});
   if(insertError)throw insertError;
   return record;
  }
  const requestUrl=new URL(req.url),query=requestUrl.searchParams;
  if(route==="/register"&&req.method==="POST"){
   const body=await req.json();
   const fieldId=text(body?.fieldId),taskId=text(body?.taskId),targetId=text(body?.targetId);
   const type=text(body?.targetType,20);
   if(!VALID_ID.test(fieldId)||!VALID_ID.test(taskId)||!VALID_ID.test(targetId)||
     !["personal","area","pad"].includes(type))return response({detail:"Некорректные параметры задания"},400);
   const membership=await memberOf(fieldId);
   if(!membership||membership.role==="admin")return response({detail:"Нет права создавать задания"},403);
   const existing=await findTask(fieldId,taskId);
   if(existing){
     if(existing.created_by!==actor||existing.target_type!==type||existing.target_id!==targetId)
       return response({detail:"Номер задания уже существует"},409);
     return response({status:"exists",taskId});
   }
   if(type==="personal"){
    const {data,error}=await admin.from("field_memberships").select("user_id")
     .eq("field_id",fieldId).eq("user_id",targetId).eq("approved",true).eq("blocked",false).maybeSingle();
    if(error)throw error;if(!data)return response({detail:"Исполнитель не относится к месторождению"},403);
   } else {
    const state=await snapshot(fieldId);
    const valid=type==="area"?
      Array.isArray(state?.areas)&&state.areas.some((a:Row)=>a?.id===targetId):
      Array.isArray(state?.pads)&&state.pads.some((p:Row)=>p?.id===targetId);
    if(!valid)return response({detail:"Сначала синхронизируйте участок или кустовую площадку"},409);
   }
   const {error}=await admin.from("promysel_task_photo_registry").insert({
    field_id:fieldId,task_id:taskId,created_by:actor,target_type:type,target_id:targetId
   });
   if(error)return response({detail:"Не удалось зарегистрировать задание"},409);
   return response({status:"created",taskId},201);
  }
  if(route==="/list"&&req.method==="GET"){
    const fieldId=text(query.get("fieldId")),taskId=text(query.get("taskId"));
    if(!VALID_ID.test(fieldId)||!VALID_ID.test(taskId))return response({detail:"Неверное задание"},400);
    const member=await memberOf(fieldId),task=member?await findTask(fieldId,taskId):null;
    if(!member||!task||!authorizedRead(actor,member,task))return response({detail:"Нет доступа к заданию"},403);
    const {data,error}=await admin.from("promysel_task_photos")
     .select("id,phase,uploaded_by,original_name,uploaded_at")
     .eq("field_id",fieldId).eq("task_id",taskId).order("uploaded_at",{ascending:true}).limit(80);
    if(error)throw error;return response({items:data??[]});
  }
  if(route==="/upload"&&req.method==="POST"){
    const length=Number(req.headers.get("content-length")??"0");
    if(length>7*1024*1024)return response({detail:"Фотография слишком большая"},413);
    const form=await req.formData();
    const fieldId=text(form.get("fieldId")),taskId=text(form.get("taskId")),
      phase=text(form.get("phase"),20),clientId=text(form.get("clientId"),64);
    if(!VALID_ID.test(fieldId)||!VALID_ID.test(taskId)||!UUID.test(clientId))
      return response({detail:"Некорректный идентификатор фотографии"},400);
    const member=await memberOf(fieldId),task=member?await findTask(fieldId,taskId):null;
    if(!member||!task||!authorizedWrite(actor,member,task,phase))
      return response({detail:"У вас нет права прикреплять фотографии к заданию"},403);
    const file=form.get("photo");
    if(!(file instanceof File)||!MIMES.has(file.type)||file.size<=0||file.size>5242880)
      return response({detail:"Поддерживаются JPEG, PNG, WebP до 5 МБ"},400);
    const bytes=new Uint8Array(await file.arrayBuffer());
    if(!imageMagic(bytes,file.type))return response({detail:"Некорректный формат изображения"},400);
    const {data:duplicate,error:dupError}=await admin.from("promysel_task_photos").select("id")
     .eq("field_id",fieldId).eq("task_id",taskId).eq("uploaded_by",actor)
     .eq("client_upload_id",clientId).maybeSingle();
    if(dupError)throw dupError;
    if(duplicate)return response({id:duplicate.id,duplicate:true});
    const ext=file.type==="image/png"?"png":file.type==="image/webp"?"webp":"jpg";
    const objectPath=[fieldId,taskId,actor,clientId+"."+ext].join("/");
    const {error:uploadError}=await admin.storage.from(bucket)
     .upload(objectPath,bytes,{contentType:file.type,upsert:false});
    if(uploadError)return response({detail:"Файл не удалось загрузить. Повторите попытку."},503);
    const {data, error:saveError}=await admin.from("promysel_task_photos").insert({
      field_id:fieldId,task_id:taskId,phase,uploaded_by:actor,
      client_upload_id:clientId,object_path:objectPath,
      original_name:text(file.name,180)||"photo."+ext,content_type:file.type
    }).select("id").single();
    if(saveError){
      // Concurrent retry may already have stored metadata. Never create duplicates.
      const {data:previous}=await admin.from("promysel_task_photos").select("id")
       .eq("field_id",fieldId).eq("task_id",taskId).eq("uploaded_by",actor)
       .eq("client_upload_id",clientId).maybeSingle();
      if(previous)return response({id:previous.id,duplicate:true});
      await admin.storage.from(bucket).remove([objectPath]);
      return response({detail:"Не удалось сохранить фотографию"},503);
    }
    return response({id:data.id},201);
  }
  const photoRoute=route.match(/^\/([0-9a-f-]{36})\/url$/i);
  if(photoRoute&&req.method==="GET"){
    const id=photoRoute[1];if(!UUID.test(id))return response({detail:"Неверный идентификатор"},400);
    const {data,error}=await admin.from("promysel_task_photos")
     .select("field_id,task_id,object_path").eq("id",id).maybeSingle();
    if(error)throw error;if(!data)return response({detail:"Фотография не найдена"},404);
    const member=await memberOf(data.field_id),task=member?await findTask(data.field_id,data.task_id):null;
    if(!member||!task||!authorizedRead(actor,member,task))return response({detail:"Нет доступа"},403);
    const {data:signed,error:signError}=await admin.storage.from(bucket)
      .createSignedUrl(data.object_path,60);
    if(signError)throw signError;return response({url:signed.signedUrl});
  }
  return response({detail:"Маршрут не найден"},404);
 }catch(e){
  console.error("promysel-task-photos",e instanceof Error?e.message:String(e));
  return response({detail:"Не удалось обработать запрос. Повторите позже."},500);
 }
});
