import { createClient } from "npm:@supabase/supabase-js@2.57.0";
// Backward-compatible adapter for the ORIGINAL Flutter Promysel 1.77 app.
// Browser must pass Supabase Auth bearer token for every private endpoint.
// All administrative writes use the existing audited, scoped Postgres RPCs.
const HEAD={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Access-Control-Allow-Methods":"GET,POST,DELETE,OPTIONS","Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
const reply=(x:unknown,status=200)=>new Response(JSON.stringify(x),{status,headers:HEAD});
const good=(x:unknown)=>!!x&&typeof x==="object"&&!Array.isArray(x);
const txt=(x:unknown)=>typeof x==="string"?x.trim():"";
const base=Deno.env.get("SUPABASE_URL")??"",publish=Deno.env.get("SUPABASE_ANON_KEY")??"",secret=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
const fieldTag=(x:unknown)=>txt(x).slice(0,128);
const validEmail=(x:string)=>x.length<=254&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(x);
type J=Record<string,unknown>;

function mergeRows(oldV:unknown,newV:unknown,k:string):J[]{
 const out:J[]=[],pos=new Map<string,number>();
 for(const v of [...(Array.isArray(oldV)?oldV:[]),...(Array.isArray(newV)?newV:[])]){
  if(!good(v))continue;const row={...(v as J)};
  const key=k==="annulus"?String(row.wellId??"")+"|"+String(row.date??""):String(row.id??"");
  const idx=pos.get(key);
  if(idx===undefined||key===""||key==="|"){
    if(key!==""&&key!=="|")pos.set(key,out.length);
    if(key!==""&&key!=="|"||!out.some(x=>JSON.stringify(x)===JSON.stringify(row)))out.push(row);
  }else{
    const old=out[idx];
    if(k==="pads")out[idx]={...old,...row,wells:mergeRows(old.wells,row.wells,"id")};
    else if(k==="tasks"&&((old.status==="confirmed"&&row.status!=="confirmed")||
      (old.status==="awaitingConfirmation"&&row.status==="active"&&!row.rejectedAt)))continue;
    else if(k==="notifications"&&old.read===true)out[idx]={...old,...row,read:true};
    else out[idx]={...old,...row};
  }
 }
 return out;
}
function mergeState(a:J,b:J):J{
 const o:J={...a,...b};
 for(const k of ["areas","pads","tasks","annulus","training","notifications"])o[k]=mergeRows(a[k],b[k],k);
 for(const k of ["avatars","problemApplications"])
   o[k]={...(good(a[k])?a[k] as J:{}),...(good(b[k])?b[k] as J:{})};
 const x=good(a.walkConfig)?a.walkConfig as J:{},y=good(b.walkConfig)?b.walkConfig as J:{};
 const cfg:J={...x,...y};
 for(const k of ["enabled","units","wellEnabled","wellUnits"])
   cfg[k]={...(good(x[k])?x[k] as J:{}),...(good(y[k])?y[k] as J:{})};
 o.walkConfig=cfg;return o;
}

Deno.serve(async(req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:HEAD});
 const route=new URL(req.url).pathname.replace(/^.*?\/promysel-compat/,"");
 if(req.method==="GET"&&(route==="/health"||route==="/v1/health"))return reply({status:"ok",service:"promysel-compat",backend:"supabase"});
 if(!base||!publish||!secret)return reply({detail:"Облачная конфигурация недоступна"},503);
 const guest=createClient(base,publish,{auth:{persistSession:false,autoRefreshToken:false}});
 const admin=createClient(base,secret,{auth:{persistSession:false,autoRefreshToken:false}});
 const authorization=req.headers.get("authorization")??"";
 const token=authorization.startsWith("Bearer ")?authorization.slice(7).trim():"";
 const publicRoute=route==="/v1/registration/fields"&&req.method==="GET"||
  route==="/v1/auth/login"&&req.method==="POST"||
  route==="/v1/registration/apply"&&req.method==="POST"||
  route==="/v1/auth/forgot-password"&&req.method==="POST";
 let body:J={};
 if(req.method==="POST"){
  const raw=await req.text();
  if(raw.length>1024*1024)return reply({detail:"Размер запроса превышает 1 МБ"},413);
  if(raw){try{const b=JSON.parse(raw);if(!good(b))return reply({detail:"Ожидается JSON-объект"},400);body=b as J}
  catch{return reply({detail:"Некорректный JSON"},400)}}
 }
 try{
  if(publicRoute&&route==="/v1/registration/fields"){
   const {data,error}=await admin.from("oil_fields").select("id,name").order("name").limit(100);
   if(error)throw error;return reply({items:data??[]});
  }
  if(publicRoute&&route==="/v1/auth/login"){
   const email=txt(body.login).toLowerCase()||txt(body.username).toLowerCase();
   const password=typeof body.password==="string"?body.password:"";
   if(!validEmail(email)||!password)return reply({detail:"Введите корректный email и пароль"},400);
   const {data,error}=await guest.auth.signInWithPassword({email,password});
   if(error||!data.user||!data.session)return reply({detail:"Неверная электронная почта или пароль"},401);
   const {data:members,error:memberErr}=await admin.from("field_memberships").select("field_id,role,subrole,display_name,approved,blocked").eq("user_id",data.user.id).limit(10);
   if(memberErr)throw memberErr;
   const member=(members??[]).find((m:J)=>m.approved===true&&m.blocked!==true);
   const isAdmin=data.user.app_metadata?.system_admin===true;
   if(!member&&!isAdmin)return reply({detail:"Заявка ещё не согласована или доступ заблокирован"},403);
   const mustChange=data.user.app_metadata?.must_change_password===true;
   return reply({token:data.session.access_token,refresh_token:data.session.refresh_token,
     expires_at:data.session.expires_at, mustChangePassword:mustChange,
     user:{id:data.user.id,name:member?.display_name??data.user.user_metadata?.full_name??"Администратор",
       email:data.user.email,role:isAdmin&&!member?"admin":member?.role,
       subrole:member?.subrole??null,fieldId:member?.field_id??null}});
  }
  if(publicRoute&&route==="/v1/auth/forgot-password"){
   const email=txt(body.email).toLowerCase();
   if(!validEmail(email))return reply({detail:"Некорректная почта"},400);
   const {error}=await guest.auth.resetPasswordForEmail(email,{redirectTo:"https://promysel-web.pages.dev/finish-registration.html"});
   if(error)console.error("resetPasswordForEmail:",error.message);
   return reply({status:"ok",detail:"Если почта зарегистрирована, письмо отправлено"});
  }
  if(publicRoute&&route==="/v1/registration/apply"){
   const email=txt(body.email).toLowerCase(),name=txt(body.fullName),role=txt(body.role),subrole=txt(body.subrole);
   const field=fieldTag(body.fieldId),newField=txt(body.newFieldName);
   if(!validEmail(email)||name.length<3||name.length>200)return reply({detail:"Заполните ФИО и корректную почту"},400);
   if(!["shopChief","engineer","operator","dispatcher"].includes(role))return reply({detail:"Неизвестная роль"},400);
   if(!!field===!!newField||newField.length>200)return reply({detail:"Укажите существующее или новое месторождение"},400);
   if(newField&&role!=="shopChief")return reply({detail:"Новое месторождение запрашивает начальник цеха"},403);
   if(field){
     const {data}=await admin.from("oil_fields").select("id").eq("id",field).maybeSingle();
     if(!data)return reply({detail:"Месторождение не найдено"},404);
   }
   // APPLICATION ONLY: nobody is invited or created in Auth before approval.
   const {data:existing,error:checkErr}=await admin.from("registration_requests")
     .select("id").eq("email",email).eq("state","pending").limit(1);
   if(checkErr)throw checkErr;
   if(existing?.length)return reply({id:String(existing[0].id),
     detail:"Заявка уже ожидает согласования. Письмо придёт после одобрения."});
   const {data,error}=await admin.from("registration_requests").insert({
     requested_by:null,field_id:field||null,proposed_field_name:newField||null,
     requested_role:role,requested_subrole:role==="engineer"?subrole||null:null,
     full_name:name,email,state:"pending"
   }).select("id").single();
   if(error)throw error;
   return reply({id:String(data.id),
      detail:"Заявка отправлена на согласование. После одобрения придёт письмо для установки пароля."},201);
  }
  if(!token)return reply({detail:"Необходимо войти в приложение"},401);
  const actorClient=createClient(base,publish,{global:{headers:{Authorization:"Bearer "+token}},
    auth:{persistSession:false,autoRefreshToken:false}});
  const {data:auth,error:authError}=await actorClient.auth.getUser(token);
  if(authError||!auth.user)return reply({detail:"Сессия истекла. Войдите повторно."},401);
  const user=auth.user;
  const elevated=user.app_metadata?.system_admin===true;
  if(user.app_metadata?.must_change_password===true&&
     !["/v1/auth/first-password","/v1/auth/change-password"].includes(route)){
     return reply({detail:"Необходимо изменить временный пароль"},403);
  }
  const {data:members,error:mErr}=await admin.from("field_memberships").select("field_id,role,subrole,display_name,approved,blocked").eq("user_id",user.id).limit(30);
  if(mErr)throw mErr;
  const memberships=(members??[]).filter((m:J)=>m.approved===true&&m.blocked!==true);
  const canField=(fieldId:string)=>memberships.find((m:J)=>m.field_id===fieldId);
  async function effectiveState(fid:string):Promise<{snapshot:J|null,seq:number,changed:boolean}>{
    const {data,error}=await admin.from("sync_events").select("sequence,payload")
      .eq("field_id",fid).eq("event_type","app_state").order("sequence",{ascending:false}).limit(80);
    if(error)throw error;
    if(!data?.length)return {snapshot:null,seq:0,changed:false};
    let acc:J={};
    for(const row of [...data].reverse())if(good(row.payload))acc=mergeState(acc,row.payload as J);
    const last=data[0].payload as J;
    const names=["areas","pads","tasks","annulus","training","notifications","walkConfig","avatars","problemApplications"];
    return {snapshot:acc,seq:Number(data[0].sequence),
      changed:names.some(k=>JSON.stringify(acc[k])!==JSON.stringify(last?.[k]))};
  }
  const administrator=elevated;
  if(req.method==="POST"&&(route==="/v1/auth/first-password"||route==="/v1/auth/change-password")){
   const password=txt(body.password)||txt(body.newPassword);
   if(password.length<12||password.length>128)return reply({detail:"Пароль должен содержать 12–128 символов"},400);
   if(route.endsWith("first-password")&&user.app_metadata?.must_change_password!==true)return reply({detail:"Смена первого пароля не требуется"},409);
   if(route.endsWith("change-password")){
    const old=txt(body.oldPassword);
    if(!old||old===password||!user.email)return reply({detail:"Укажите прежний и новый пароль"},400);
    const {error}=await guest.auth.signInWithPassword({email:user.email,password:old});
    if(error)return reply({detail:"Неверный прежний пароль"},401);
   }
   const {error}=await admin.auth.admin.updateUserById(user.id,{password,
    app_metadata:{...user.app_metadata,must_change_password:false,password_changed_at:new Date().toISOString()}});
   if(error)throw error;
   return reply({status:"ok"});
  }
  if(req.method==="GET"&&route==="/v1/registration/pending"){
   let query=admin.from("registration_requests").select("id,requested_by,field_id,proposed_field_name,requested_role,requested_subrole,full_name,email,state").or("state.eq.pending,and(state.eq.approved,approved_field_id.not.is.null,invitation_sent_at.is.null)").order("created_at",{ascending:true}).limit(200);
   if(!administrator){
     const chief=memberships.find((m:J)=>m.role==="shopChief");
     if(!chief)return reply({detail:"Нет права просматривать заявки"},403);
     query=query.eq("field_id",chief.field_id);
   }
   const {data,error}=await query;
   if(error)throw error;
   return reply({items:(data??[]).map((x:J)=>({id:String(x.id),name:x.full_name,email:x.email,role:x.requested_role,subrole:x.requested_subrole,fieldId:x.field_id??"",requiresAdmin:x.field_id===null}))});
  }
  const approval=route.match(/^\/v1\/registration\/(\d+)\/(approve|reject)$/);
  if(req.method==="POST"&&approval){
   const target=Number(approval[1]);if(!Number.isSafeInteger(target)||target<1)return reply({detail:"Неверный номер заявки"},400);
   if(approval[2]==="reject"){
     const {data,error}=await admin.rpc("promysel_reject_registration",{
       p_request_id:target,p_actor:user.id,p_note:""});
     if(error)return reply({detail:error.message},403);
     return reply(data);
   }
   // A verified administrator or scoped shop chief APPROVES first.
   const {data:decision,error:startError}=await admin.rpc("promysel_start_registration_approval",{
      p_request_id:target,p_actor:user.id
   });
   if(startError)return reply({detail:startError.message},403);
   let invitedId=txt(decision?.existingUserId);
   let sent=false;
   if(!invitedId){
     const {data:invited,error:inviteError}=await admin.auth.admin.inviteUserByEmail(String(decision.email),{
       data:{full_name:decision.fullName},
       redirectTo:"https://promysel-web.pages.dev/finish-registration.html"
     });
     if(inviteError||!invited.user){
       console.error("post-approval invite:",inviteError?.message??"missing user");
       return reply({detail:"Заявка согласована, но письмо не отправлено. Повторите отправку из заявок."},503);
     }
     invitedId=invited.user.id;
     sent=true;
   }
   const {data:finished,error:finishError}=await admin.rpc("promysel_finish_registration_approval",{
       p_request_id:target,p_actor:user.id,p_user_id:invitedId
   });
   if(finishError){
     console.error("approved invite finalization:",finishError.message);
     return reply({detail:"Решение принято, но привязка учётной записи не завершена. Повторите действие."},409);
   }
   if(!sent){
      const {error:mailErr}=await guest.auth.resetPasswordForEmail(String(decision.email),{
        redirectTo:"https://promysel-web.pages.dev/finish-registration.html"
      });
      if(mailErr)console.error("approved existing user mail:",mailErr.message);
      sent=!mailErr;
   }
   return reply({...finished,invitationSent:sent,detail:sent?
     "Заявка согласована. Письмо для установки пароля отправлено.":
     "Заявка согласована. Письмо отправить не удалось, обратитесь к администратору."});
  }
  if(req.method==="GET"&&(route==="/v1/users"||route==="/v1/registration/users")){
   if(!administrator&&memberships.length===0)return reply({detail:"Нет доступа"},403);
   const fields=administrator?null:memberships.map((m:J)=>String(m.field_id));
   let query=admin.from("field_memberships").select("user_id,field_id,display_name,role,subrole,approved,blocked").order("joined_at",{ascending:false}).limit(500);
   if(fields&&fields.length)query=query.in("field_id",fields);
   const {data,error}=await query;if(error)throw error;
   return reply({items:(data??[]).map((m:J)=>({id:m.user_id,name:m.display_name,role:m.role,
      subrole:m.subrole,fieldId:m.field_id,approved:m.approved===true&&m.blocked!==true}))});
  }
  const deleteUser=route.match(/^\/v1\/users\/([0-9a-f-]{36})$/i);
  if(req.method==="DELETE"&&deleteUser){
   const target=deleteUser[1],chief=memberships.find((m:J)=>m.role==="shopChief");
   if(!chief)return reply({detail:"Только начальник цеха может отстранить сотрудника"},403);
   const {data,error}=await admin.rpc("promysel_set_worker_blocked",{p_field:chief.field_id,p_actor:user.id,p_target:target,p_blocked:true});
   if(error)return reply({detail:error.message},403);
   return reply({status:"blocked",userId:target,record:data});
  }

  const padWellsRoute=route.match(new RegExp("^/api/v1/pads/([^/]+)/wells$"));
  if(req.method==="GET"&&(padWellsRoute||route==="/api/v1/pads")){
    const allowed=memberships.map((m:J)=>String(m.field_id));
    if(!allowed.length)return reply({detail:"Нет доступа к месторождению"},403);
    const pads:J[]=[];
    for(const fid of allowed){const state=await effectiveState(fid);const data=state.snapshot;
      if(data&&Array.isArray(data.pads))for(const item of data.pads)if(good(item))pads.push(item as J);
    }
    if(route==="/api/v1/pads")
      return reply(pads.map(p=>({id:p.id,name:p.name,type:p.type??p.kind??"oil",field_id:p.fieldId??null})));
    const padId=decodeURIComponent(padWellsRoute?.[1]??""),pad=pads.find(p=>String(p.id)===padId);
    if(!pad)return reply({detail:"Куст ещё не синхронизирован"},404);
    const wells=Array.isArray(pad.wells)?pad.wells.filter(good) as J[]:[];
    return reply(wells.map(w=>({id:w.id,number:w.number,
      type:w.type==="gasCondensate"?"gas_condensate":"oil",
      status:w.status==="stopped"?"Остановлена":w.status==="workover"?"ВНР":"В работе"})));
  }
  if(route==="/v1/sync/push"&&req.method==="POST"||
     route==="/v1/sync/pull"&&req.method==="GET"){
   const url=new URL(req.url);
   const fieldId=fieldTag(req.method==="GET"?url.searchParams.get("fieldId"):body.fieldId);
   const member=canField(fieldId);
   if(!member)return reply({detail:"Нет допуска к месторождению"},403);
   if(req.method==="GET"){
    const cursor=txt(url.searchParams.get("cursor"))||"0",device=txt(url.searchParams.get("deviceId"));
    if(!/^\d{1,19}$/.test(cursor)||device.length>200)return reply({detail:"Неверный курсор"},400);
    const {data,error}=await actorClient.from("sync_events")
     .select("sequence,event_key,event_type,payload,client_updated_at,device_id")
     .eq("field_id",fieldId).gt("sequence",Number(cursor)).order("sequence",{ascending:true}).limit(200);
    if(error)throw error;
    const repaired=await effectiveState(fieldId);
    const output=(data??[]).filter((x:J)=>x.device_id!==device||x.event_type==="app_state"||x.event_type==="measurement")
      .map((x:J)=>({key:x.event_key,type:x.event_type,updatedAt:x.client_updated_at,payload:x.payload}));
    if(repaired.snapshot&&repaired.changed){
      // During recovery replay immutable measurements, even if a device's
      // cursor passed them before its local SQLite data was lost.
      const {data:archivedWalks,error:archiveError}=await actorClient.from("sync_events")
        .select("event_key,event_type,payload,client_updated_at")
        .eq("field_id",fieldId).eq("event_type","measurement")
        .order("sequence",{ascending:false}).limit(200);
      if(archiveError)throw archiveError;
      const present=new Set(output.map((e:J)=>String(e.key)));
      for(const e of [...(archivedWalks??[])].reverse()){
        if(present.has(String(e.event_key)))continue;
        output.push({key:e.event_key,type:"measurement",
          updatedAt:e.client_updated_at,payload:e.payload});
      }
      output.push({key:"recovered:"+fieldId+":"+String(repaired.seq),type:"app_state",
        updatedAt:new Date().toISOString(),payload:repaired.snapshot});
    }
    return reply({cursor:(data?.length?String(data[data.length-1].sequence):cursor),items:output});
   }
   const device=txt(body.deviceId),items=body.items;
   if(!device||device.length>200||!Array.isArray(items)||items.length<1||items.length>100)
      return reply({detail:"Некорректный пакет синхронизации"},400);
   const specialist=member.role==="engineer"&&["geologist","technologist","leadingGeologist","leadingTechnologist"].includes(String(member.subrole));
   const canStructure=member.role==="shopChief"||member.role==="admin"||specialist;
   const canWalk=["operator","engineer","shopChief"].includes(String(member.role));
   const records:J[]=[];
   for(const item of items){
    if(!good(item)||!good(item.payload))return reply({detail:"Некорректный элемент синхронизации"},400);
    const i=item as J,key=txt(i.key),type=txt(i.type),payload=i.payload as J;
    if(key.length<1||key.length>300||!["measurement","app_state"].includes(type))return reply({detail:"Неверный тип изменения"},400);
    if(type==="measurement"&&!canWalk||type==="app_state"&&!canStructure)return reply({detail:"Нет прав на изменение"},403);
    if(type==="app_state"&&payload.fieldId!==fieldId)return reply({detail:"Месторождение снимка не совпадает"},403);
    records.push({event_key:key,field_id:fieldId,device_id:device,event_type:type,
     payload,actor_id:user.id,client_updated_at:i.updatedAt??null});
   }
   const {error}=await actorClient.from("sync_events").upsert(records,{onConflict:"event_key",ignoreDuplicates:true});
   if(error)throw error;
   return reply({accepted:records.map((x:J)=>x.event_key)});
  }
  return reply({detail:"Маршрут не найден"},404);
 }catch(e){
  console.error("promysel-compat:",e instanceof Error?e.message:String(e));
  return reply({detail:"Ошибка облачного сервера. Проверьте настройки и журнал."},500);
 }
});
