import { createClient } from "npm:@supabase/supabase-js@2.57.0";
// Backward-compatible adapter for the ORIGINAL Flutter Promysel 1.77 app.
// Browser must pass Supabase Auth bearer token for every private endpoint.
// All administrative writes use the existing audited, scoped Postgres RPCs.
const HEAD={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Access-Control-Allow-Methods":"GET,POST,PATCH,DELETE,OPTIONS","Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
const reply=(x:unknown,status=200)=>new Response(JSON.stringify(x),{status,headers:HEAD});
const good=(x:unknown)=>!!x&&typeof x==="object"&&!Array.isArray(x);
const txt=(x:unknown)=>typeof x==="string"?x.trim():"";
const base=Deno.env.get("SUPABASE_URL")??"",publish=Deno.env.get("SUPABASE_ANON_KEY")??"",secret=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
const fieldTag=(x:unknown)=>txt(x).slice(0,128);
// A second, independent Web origin can be configured after HTTPS and Auth redirect allow-list are ready.
const configuredPublicOrigin=txt(Deno.env.get("PROMYSEL_PUBLIC_ORIGIN"));
function validatedPublicOrigin(value:string):string{
  try{
    const url=new URL(value);
    if(url.protocol==="https:"&&!url.username&&!url.password&&url.pathname==="/"&&!url.search&&!url.hash)
      return url.origin;
  }catch(_){}
  return "";
}
// Production invitations must never be redirected to a retired Cloudflare
// hostname, even if a stale PROMYSEL_PUBLIC_ORIGIN environment variable exists.
const approvedRegistrationOrigin="https://promysel-app.tuqo.ru";
const candidateRegistrationOrigin=validatedPublicOrigin(configuredPublicOrigin);
const publicOrigin=candidateRegistrationOrigin===approvedRegistrationOrigin
  ?candidateRegistrationOrigin:approvedRegistrationOrigin;
const passwordSetupUrl=publicOrigin+"/finish-registration.html";

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
    const priorAt=Date.parse(String(old.updatedAt??"")),incomingAt=Date.parse(String(row.updatedAt??""));
    const priorNewer=Number.isFinite(priorAt)&&(!Number.isFinite(incomingAt)||priorAt>incomingAt);
    if(k==="pads"){
      const wells=mergeRows(old.wells,row.wells,"wells");
      const preferred=priorNewer?old:row;
      const order=Array.isArray(preferred.wells)?preferred.wells.map((w:J)=>String(w.id??"")):[];
      const positions=new Map<string,number>();order.forEach((id:string,i:number)=>positions.set(id,i));
      wells.sort((x,y)=>(positions.get(String(x.id))??999999)-(positions.get(String(y.id))??999999));
      out[idx]={...old,...row,...(priorNewer?old:{}),wells};
    }
    else if(priorNewer&&(k==="areas"||k==="wells"))continue;
    else if(k==="training"&&
      (Date.parse(String(old.updatedAt??""))||0)>
      (Date.parse(String(row.updatedAt??""))||0))continue;
    else if(k==="tasks"&&((old.status==="confirmed"&&row.status!=="confirmed")||
      (old.status==="awaitingConfirmation"&&row.status==="active"&&!row.rejectedAt)))continue;
    else if(k==="notifications"&&old.read===true)out[idx]={...old,...row,read:true};
    else out[idx]={...old,...row};
  }
 }
 return out;
}
// Tombstones are field-scoped, permanent deletion markers for current structure.
// Historical production measurements, tasks, and messages are NOT deleted.
type DeletedMap={areas:string[],pads:string[],wells:string[]};
function deletedStructure(raw:unknown):DeletedMap{
 const source=good(raw)?raw as J:{};
 const ids=(kind:string)=>[...new Set((Array.isArray(source[kind])?source[kind]:[])
   .filter((id:unknown)=>typeof id==="string"&&id.length>0&&id.length<=180)
   .map(String))].sort();
 return {areas:ids("areas"),pads:ids("pads"),wells:ids("wells")};
}
function mergeStructureDeleted(a:unknown,b:unknown):DeletedMap{
 const left=deletedStructure(a),right=deletedStructure(b);
 return {
   areas:[...new Set([...left.areas,...right.areas])].sort(),
   pads:[...new Set([...left.pads,...right.pads])].sort(),
   wells:[...new Set([...left.wells,...right.wells])].sort()
 };
}
function filterDeletedStructure(state:J):J{
 const del=deletedStructure(state.structureDeleted);
 const areas=new Set(del.areas),pads=new Set(del.pads),wells=new Set(del.wells);
 const activeAreas=(Array.isArray(state.areas)?state.areas:[])
   .filter(good).filter((x:J)=>!areas.has(String(x.id??"")))
   .map((x:J)=>({...x,padIds:(Array.isArray(x.padIds)?x.padIds:[])
     .filter((id:unknown)=>!pads.has(String(id)))}));
 const activePads=(Array.isArray(state.pads)?state.pads:[])
   .filter(good).filter((x:J)=>!pads.has(String(x.id??""))&&
     !areas.has(String(x.areaId??"")))
   .map((x:J)=>({...x,wells:(Array.isArray(x.wells)?x.wells:[])
     .filter((w:unknown)=>good(w)&&
       !wells.has(String(x.id??"")+":"+String((w as J).id??""))&&
       !wells.has(String((w as J).id??"")))}));
 return {...state,structureDeleted:del,areas:activeAreas,pads:activePads};
}
function mergeState(a:J,b:J):J{
 const o:J={...a,...b};
 for(const k of ["areas","pads","tasks","annulus","training","notifications"])o[k]=mergeRows(a[k],b[k],k);
 const removed=new Set<string>([
   ...(Array.isArray(a.trainingDeletedIds)?a.trainingDeletedIds:[]).map(String),
   ...(Array.isArray(b.trainingDeletedIds)?b.trainingDeletedIds:[]).map(String),
 ]);
 o.trainingDeletedIds=[...removed];
 o.training=(o.training as J[]).filter(x=>!removed.has(String(x.id??"")));
 const oldSchedules=good(a.workSchedules)?a.workSchedules as J:{};
 const newSchedules=good(b.workSchedules)?b.workSchedules as J:{};
 const schedules:J={...oldSchedules};
 for(const [id,value] of Object.entries(newSchedules)){
   const prev=oldSchedules[id];
   const prevDate=good(prev)?Date.parse(String((prev as J).updated??"")):0;
   const nextDate=good(value)?Date.parse(String((value as J).updated??"")):0;
   if(!prev||Number.isFinite(nextDate)&&(!Number.isFinite(prevDate)||nextDate>=prevDate))
     schedules[id]=value;
 }
 o.workSchedules=schedules;
 for(const k of ["avatars","problemApplications"])
   o[k]={...(good(a[k])?a[k] as J:{}),...(good(b[k])?b[k] as J:{})};
 const x=good(a.walkConfig)?a.walkConfig as J:{},y=good(b.walkConfig)?b.walkConfig as J:{};
 const cfg:J={...x,...y};
 for(const k of ["enabled","units","wellEnabled","wellUnits"])
   cfg[k]={...(good(x[k])?x[k] as J:{}),...(good(y[k])?y[k] as J:{})};
 o.walkConfig=cfg;
 o.structureDeleted=mergeStructureDeleted(a.structureDeleted,b.structureDeleted);
 return filterDeletedStructure(o);
}

// Stable UTF-16 FNV+DJ sum matches the Flutter _snapshotDigest().
function avatarTransportDigest(value:string):string{
  let a=2166136261,b=5381;
  for(let i=0;i<value.length;i++){
    const code=value.charCodeAt(i);
    a=Math.imul(a^code,16777619)>>>0;
    b=(Math.imul(b,33)+code)>>>0;
  }
  return value.length+":"+a.toString(16)+":"+b.toString(16);
}

/** Backward-compatible operator misc delta; never grants structure access. */
function scopedOperatorMisc(raw:J,actorId:string,fieldId:string):J|null{
 const allowed=new Set(["fieldId","schema","updatedAt","annulus","notifications","problemApplications"]);
 if(raw.fieldId!==fieldId||Object.keys(raw).some(k=>!allowed.has(k)))return null;
 if(raw.schema!==undefined&&(!Number.isInteger(raw.schema)||Number(raw.schema)<1))return null;
 if(raw.updatedAt!==undefined&&(typeof raw.updatedAt!=="string"||raw.updatedAt.length>80))return null;
 const annulus=raw.annulus;
 if(annulus!==undefined&&(!Array.isArray(annulus)||annulus.length>2000||!annulus.every(good)))return null;
 const notifications=raw.notifications;
 if(notifications!==undefined&&(!Array.isArray(notifications)||notifications.length>1000||
    !notifications.every((n:unknown)=>good(n)&&String((n as J).userId??"")===actorId)))return null;
 const problems=raw.problemApplications;
 // Non-empty legacy map changes have no secure per-entry ownership proof.
 // Reject rather than acknowledge or silently lose these queued edits.
 if(problems!==undefined&&(!good(problems)||Object.keys(problems).length>0))return null;
 return {fieldId,
   ...(raw.schema!==undefined?{schema:raw.schema}:{}),
   ...(raw.updatedAt!==undefined?{updatedAt:raw.updatedAt}:{}),
   ...(annulus!==undefined?{annulus}:{}),
   ...(notifications!==undefined?{notifications}:{}),
   ...(problems!==undefined?{problemApplications:{}}:{})};
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
 if(["POST","PATCH","DELETE"].includes(req.method)){
  const raw=await req.text();
  if(raw.length>1024*1024)return reply({detail:"Размер запроса превышает 1 МБ"},413);
  if(raw){try{const b=JSON.parse(raw);if(!good(b))return reply({detail:"Ожидается JSON-объект"},400);body=b as J}
  catch{return reply({detail:"Некорректный JSON"},400)}}
 }
 try{
  if(publicRoute&&route==="/v1/registration/fields"){
   const {data,error}=await admin.from("oil_fields").select("id,name").is("archived_at",null).order("name").limit(100);
   if(error)throw error;return reply({items:data??[]});
  }
  if(publicRoute&&route==="/v1/auth/login"){
   const email=txt(body.login).toLowerCase()||txt(body.username).toLowerCase();
   const password=typeof body.password==="string"?body.password:"";
   if(!validEmail(email)||!password)return reply({detail:"Введите корректный email и пароль"},400);
   const {data,error}=await guest.auth.signInWithPassword({email,password});
   if(error||!data.user||!data.session)return reply({detail:"Неверная электронная почта или пароль"},401);
   // A single indexed FK join replaces the per-login membership + field round trip.
   // The inner join excludes archived fields without weakening access rules.
   const {data:members,error:memberErr}=await admin.from("field_memberships")
     .select("field_id,role,subrole,display_name,approved,blocked,oil_fields!inner(id,archived_at)")
     .eq("user_id",data.user.id).is("oil_fields.archived_at",null).limit(10);
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
   const {error}=await guest.auth.resetPasswordForEmail(email,{
     redirectTo:passwordSetupUrl+"?mode=forgot&token_hash="
   });
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
   // A partial UNIQUE INDEX on normalized email guarantees idempotency even
   // when two phones or double taps race between SELECT and INSERT.
   const existingRequest=async()=>{
     const {data,error}=await admin.from("registration_requests")
       .select("id,state,requested_by").eq("email",email)
       .in("state",["pending","approved"])
       .order("created_at",{ascending:false}).limit(1);
     if(error)throw error;
     return data?.[0]??null;
   };
   const repeatedReply=(r:J|null)=>{
     if(r?.state==="approved")
       return reply({detail:"Эта электронная почта уже зарегистрирована. Войдите в приложение или восстановите пароль."},409);
     return reply({id:r?.id!=null?String(r.id):null,alreadyExists:true,
       detail:"Заявка на эту почту уже отправлена и ожидает согласования. Повторная отправка не требуется."},200);
   };
   let existing=await existingRequest();
   // A completed Auth hard-delete can precede a failed registration cleanup.
   // Repair only requests whose linked Auth user has actually disappeared.
   if(existing?.state==="approved"){
     let linkedAuthDeleted=!existing.requested_by;
     if(existing.requested_by){
       const {data:linked,error:linkedError}=await admin.auth.admin.getUserById(String(existing.requested_by));
       linkedAuthDeleted=linkedError?.status===404||(!linkedError&&!linked?.user);
     }
     if(linkedAuthDeleted){
       const {error:staleError}=await admin.from("registration_requests")
         .delete().eq("id",existing.id).eq("state","approved");
       if(staleError)throw staleError;
       existing=await existingRequest();
     }
   }
   if(existing)return repeatedReply(existing);
   const {data,error}=await admin.from("registration_requests").insert({
     requested_by:null,field_id:field||null,proposed_field_name:newField||null,
     requested_role:role,requested_subrole:role==="engineer"?subrole||null:null,
     full_name:name,email,state:"pending"
   }).select("id").single();
   if(error){
     // Postgres 23505 means another concurrent registration won the race.
     if(error.code==="23505")return repeatedReply(await existingRequest());
     throw error;
   }
   return reply({id:String(data.id),
     detail:"Заявка отправлена на согласование. После одобрения придёт письмо для установки пароля."},201);
  }
  if(!token)return reply({detail:"Необходимо войти в приложение"},401);
  const actorClient=createClient(base,publish,{global:{headers:{Authorization:"Bearer "+token}},
    auth:{persistSession:false,autoRefreshToken:false}});
  // ES256: verify the signature with cached Supabase JWKS locally.
  // Immediately check auth.sessions and LIVE memberships in a single
  // service-role RPC. Signed JWTs alone must NOT bypass server-side logout.
  const {data:verified,error:claimsError}=await actorClient.auth.getClaims(token);
  const claims=verified?.claims as Record<string,unknown>|undefined;
  const uid=String(claims?.sub??""),sessionId=String(claims?.session_id??"");
  if(claimsError||!/^[0-9a-f-]{36}$/i.test(uid)||
     !/^[0-9a-f-]{36}$/i.test(sessionId))
    return reply({detail:"Сессия истекла. Войдите повторно."},401);
  const {data:scope,error:scopeError}=await admin.rpc("promysel_request_scope_v213",{
    p_user_id:uid,p_session_id:sessionId
  });
  if(scopeError)throw scopeError;
  if(!scope?.user)return reply({detail:"Сессия завершена. Войдите повторно."},401);
  const user=scope.user as J;
  // The invitation landing may be used before field access is approved.
  // Query Supabase service-role RPC by authenticated token; never trust email
  // or user ID supplied by the browser. This also protects OLD invite URLs.
  if(route==="/v1/registration/password-status"&&req.method==="GET"||
     route==="/v1/registration/initial-password"&&req.method==="POST"){
    const {data:state,error:stateError}=await admin.rpc("promysel_initial_password_status",{
      p_user_id:user.id
    });
    if(stateError)throw stateError;
    if(route.endsWith("password-status"))
      return reply({passwordSet:state?.passwordSet===true,approved:state?.approved===true});
    const newPassword=typeof body.password==="string"?body.password:"";
    if(state?.passwordSet===true)return reply({
      detail:"Пароль уже установлен. Повторная регистрация не требуется. Войдите с прежним паролем."
    },409);
    if(state?.approved!==true)return reply({
      detail:"Заявка ещё не согласована. Обратитесь к руководителю."
    },403);
    if(newPassword.length<12||newPassword.length>128)
      return reply({detail:"Пароль должен содержать от 12 до 128 символов."},400);
    const {error:passwordError}=await admin.auth.admin.updateUserById(user.id,{
      password:newPassword,app_metadata:{
        ...user.app_metadata,must_change_password:false,
        password_changed_at:new Date().toISOString()
      }
    });
    if(passwordError){
      console.error("initial password setup",passwordError.code??"unknown");
      return reply({detail:"Не удалось установить пароль. Попробуйте ещё раз."},400);
    }
    return reply({status:"password_set",detail:"Пароль установлен. Теперь войдите в приложение."});
  }
  const elevated=user.app_metadata?.system_admin===true;
  if(user.app_metadata?.must_change_password===true&&
     !["/v1/auth/first-password","/v1/auth/change-password"].includes(route)){
     return reply({detail:"Необходимо изменить временный пароль"},403);
  }
  // All scope checks are current on EVERY request, not cached in the
  // browser and not taken from user-writable JWT metadata.
  const memberships: J[]=(Array.isArray(scope.memberships)?scope.memberships:[])
    .filter((m:J)=>m.approved===true&&m.blocked!==true);
  const activeFields=new Set<string>([
    ...memberships.map((m:J)=>String(m.field_id)),
    ...(elevated&&Array.isArray(scope.admin_field_ids)?
       scope.admin_field_ids.map((id:unknown)=>String(id)):[])
  ]);
  const canField=(fieldId:string)=>memberships.find((m:J)=>m.field_id===fieldId);
  async function effectiveState(fid:string):Promise<{snapshot:J|null,seq:number,changed:boolean,revisions:J}>{
    const {data,error}=await admin.from("sync_events").select("sequence,payload")
      .eq("field_id",fid).eq("event_type","app_state").order("sequence",{ascending:false}).limit(4);
    if(error)throw error;
    if(!data?.length){
      const {data:domainOnly,error:onlyError}=await admin.from("promysel_sync_domain_state")
        .select("domain").eq("field_id",fid).limit(1);
      if(onlyError)throw onlyError;
      if(!domainOnly?.length)return {snapshot:null,seq:0,changed:false,revisions:{}};
    }
    let acc:J={};
    for(const row of [...data].reverse())if(good(row.payload))acc=mergeState(acc,row.payload as J);
    // All four domain rows are independently authoritative, even when an
    // older phone uploads a stale broad app_state snapshot.
    const {data:docs,error:domainError}=await admin.from("promysel_sync_domain_state")
      .select("domain,payload,revision").eq("field_id",fid).limit(4);
    if(domainError)throw domainError;
    const domainRevisions:J={tasks:0,schedules:0,training:0,structure:0};
    for(const doc of docs??[]){
      domainRevisions[String(doc.domain)]=Number(doc.revision);
      if(good(doc.payload))acc=mergeState(acc,doc.payload as J);
    }
    // Only the last four app_state events are replayed for performance. These
    // durable markers must never fall out of that window or a stale device
    // could revive an area, pad or well removed by a supervisor.
    const {data:markers,error:markerError}=await admin.from("promysel_structure_tombstones")
      .select("kind,entity_id").eq("field_id",fid).limit(10000);
    if(markerError)throw markerError;
    const durable:J={areas:[],pads:[],wells:[]};
    for(const marker of markers??[]){
      const kind=String(marker.kind);
      if(Array.isArray(durable[kind]))(durable[kind] as string[]).push(String(marker.entity_id));
    }
    acc=filterDeletedStructure({...acc,
      structureDeleted:mergeStructureDeleted(acc.structureDeleted,durable)});
    // Provenance is immutable and belongs to the first field-scoped task event.
    // Legacy snapshots currently contain replicated tasks from other fields.
    // Never forward them to a new user or a different field.
    const rawTasks=Array.isArray(acc.tasks)?acc.tasks.filter(good) as J[]:[];
    const ids=[...new Set(rawTasks.map((t:J)=>String(t.id??'')).filter(Boolean))];
    const owned=new Set<string>();
    for(let i=0;i<ids.length;i+=150){
      const {data:scopes,error:scopeError}=await admin.from("promysel_task_scopes")
        .select("task_id").eq("field_id",fid).in("task_id",ids.slice(i,i+150));
      if(scopeError)throw scopeError;
      for(const row of scopes??[])owned.add(String(row.task_id));
    }
    acc.tasks=rawTasks.filter((t:J)=>owned.has(String(t.id??''))&&
      (!t.fieldId||String(t.fieldId)===fid)).map((t:J)=>({...t,fieldId:fid}));
    // Durable avatar authority: every delete or deliberate replacement has a
    // server revision. Older app_state snapshots are NEVER allowed to undo it.
    const {data:avatarRows,error:avatarError}=await admin.from("promysel_avatar_versions")
      .select("user_id,avatar_value,revision").eq("field_id",fid).limit(500);
    if(avatarError)throw avatarError;
    const mergedAvatars:J=good(acc.avatars)?{...(acc.avatars as J)}:{};
    const avatarVersions:J={};
    for(const record of avatarRows??[]){
      const id=String(record.user_id);
      mergedAvatars[id]=String(record.avatar_value);
      avatarVersions[id]=Number(record.revision);
    }
    acc.avatars=mergedAvatars;
    acc.avatarVersions=avatarVersions;
    const last=(data?.[0]?.payload??{}) as J;
    const names=["areas","pads","structureDeleted","tasks","annulus","training","trainingDeletedIds","workSchedules","notifications","walkConfig","avatars","avatarVersions","problemApplications"];
    return {snapshot:acc,seq:Number(data?.[0]?.sequence??0),revisions:domainRevisions,
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
   let query=admin.from("registration_requests").select("id,requested_by,field_id,approved_field_id,proposed_field_name,requested_role,requested_subrole,full_name,email,state,invitation_sent_at").or("state.eq.pending,and(state.eq.approved,approved_field_id.not.is.null,invitation_sent_at.is.null)").order("created_at",{ascending:true}).limit(200);
   if(!administrator){
     const chiefFields=memberships.filter((m:J)=>m.role==="shopChief").map((m:J)=>String(m.field_id));
     if(!chiefFields.length)return reply({detail:"Нет права просматривать заявки"},403);
     const requestedField=fieldTag(new URL(req.url).searchParams.get("fieldId"));
     if(requestedField&&!chiefFields.includes(requestedField))
       return reply({detail:"Нет доступа к заявкам другого месторождения"},403);
     query=requestedField?query.eq("field_id",requestedField):query.in("field_id",chiefFields);
   }
   const {data,error}=await query;
   if(error)throw error;
   // Show already APPROVED employees whose invitation is still queued.
   // Never label such a request as a new pending approval.
   const requestIds=(data??[]).map((x:J)=>Number(x.id)).filter((id:number)=>Number.isSafeInteger(id));
   const jobs=new Map<number,J>();
   if(requestIds.length){
     const {data:deliveries,error:deliveryError}=await admin.from("promysel_registration_invitation_jobs")
       .select("request_id,status,attempts,next_attempt_at,last_error_code")
       .in("request_id",requestIds);
     if(deliveryError)throw deliveryError;
     for(const delivery of deliveries??[])jobs.set(Number(delivery.request_id),delivery as J);
   }
   // A project-wide sender budget applies even when the individual request
   // is due. Expose the actual next possible attempt to the approved chief.
   const {data:mailGate,error:gateError}=await admin.from("promysel_invitation_mail_gate")
     .select("next_available_at").eq("key","supabase-auth").maybeSingle();
   if(gateError)throw gateError;
   const gateAt=Date.parse(String(mailGate?.next_available_at??""))||0;
   return reply({items:(data??[]).map((x:J)=>{
     const j=jobs.get(Number(x.id));
     const due=Date.parse(String(j?.next_attempt_at??""))||0;
     const nextAt=x.state==="approved"&&j?.status!=="accepted"
       ?new Date(Math.max(due,gateAt,Date.now())).toISOString():null;
     return {
       id:String(x.id),name:x.full_name,email:x.email,role:x.requested_role,
       subrole:x.requested_subrole,fieldId:x.field_id??x.approved_field_id??"",
       requiresAdmin:x.field_id===null,
       status:x.state==="approved"?"approved_awaiting_invitation":"pending",
       invitationStatus:x.state==="approved"?String(j?.status??"queued"):"not_approved",
       nextRetryAt:nextAt,attempts:j?.attempts??0,
       deliveryError:j?.last_error_code??null,
     };
   })});
  }
  // A registration invitation contains field context only, never an approval token.
  // A chief can share it through the native system share sheet on Web/Android/iOS.
  if(req.method==="GET"&&route==="/v1/registration/invite-link"){
    const fieldId=fieldTag(new URL(req.url).searchParams.get("fieldId"));
    if(!fieldId)return reply({detail:"Укажите месторождение"},400);
    if(!administrator&&!memberships.some((m:J)=>m.role==="shopChief"&&m.field_id===fieldId))
      return reply({detail:"Приглашать сотрудников может только начальник цеха"},403);
    if(!activeFields.has(fieldId))return reply({detail:"Месторождение недоступно"},404);
    const url=new URL(publicOrigin+"/login");
    url.searchParams.set("register","1");
    url.searchParams.set("fieldId",fieldId);
    return reply({url:url.toString(),fieldId});
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
   // Approve once; keep the decision even when the email provider is capped.
   const {data:decision,error:startError}=await admin.rpc("promysel_start_registration_approval",{
      p_request_id:target,p_actor:user.id
   });
   if(startError)return reply({detail:startError.message},403);
   const {data:claim,error:claimError}=await admin.rpc("promysel_claim_registration_invitation",{
      p_request_id:target,p_actor:user.id
   });
   if(claimError){
     console.error("registration invitation claim",claimError.code??"unknown");
     return reply({status:"approved",invitationSent:false,
       detail:"Заявка согласована, но очередь приглашений временно недоступна."},202);
   }
   if(claim?.status==="already_registered"){
     const existingId=txt(claim?.acceptedUserId);
     if(!existingId)return reply({detail:"Не удалось определить действующий аккаунт"},409);
     const {data:result,error:finalizeError}=await admin.rpc("promysel_finish_registration_approval",{
       p_request_id:target,p_actor:user.id,p_user_id:existingId
     });
     if(finalizeError){
       console.error("existing account approval finalization",finalizeError.code??"unknown");
       return reply({status:"approved",invitationSent:false,
         detail:"Учётная запись существует, но доступ пока не согласован."},202);
     }
     const {error:recordError}=await admin.rpc("promysel_record_registration_invitation",{
       p_request_id:target,p_actor:user.id,p_status:"accepted",p_user_id:existingId
     });
     if(recordError)console.warn("existing account mail status",recordError.code??"unknown");
     return reply({...result,status:"approved",invitationSent:false,
       invitationStatus:"already_registered",
       detail:"Сотрудник уже установил пароль. Доступ подтверждён, повторное письмо не отправляется. Войдите с прежним паролем."});
   }
   if(claim?.status==="sent")return reply({status:"approved",invitationSent:true,
     detail:"Заявка уже согласована и приглашение отправлено."});
   const acceptedId=txt(claim?.acceptedUserId);
   if(!claim?.canSend&&!acceptedId){
     const due=claim?.nextRetryAt??null;
     return reply({status:"approved",invitationSent:false,
       invitationStatus:String(claim?.status??"queued"),nextRetryAt:due,
       detail:claim?.status==="action_required"
         ?"Заявка согласована. Для отправки приглашения требуется настройка почты."
         :"Заявка согласована. Письмо ожидает отправки; повторные запросы ограничены."},202);
   }
   const safeMailCode=(err:unknown)=>{
     const o=err&&typeof err==="object"?err as Record<string,unknown>:{};
     const message=String(o.message??"").toLowerCase();
     if(o.status===429||message.includes("rate limit")||message.includes("too many"))
       return "over_email_send_rate_limit";
     if(message.includes("not authorized")||message.includes("smtp")||
       message.includes("not configured"))
       return "email_configuration_required";
     return "mail_delivery_failed";
   };
   let invitedId=acceptedId;
   if(!invitedId){
     invitedId=txt(decision?.existingUserId);
     let deliveryError:unknown=null;
     if(!invitedId){
       const {data:invited,error:inviteError}=await admin.auth.admin.inviteUserByEmail(
         String(decision.email),{
           data:{full_name:decision.fullName},redirectTo:passwordSetupUrl
         });
       if(inviteError||!invited?.user)deliveryError=inviteError??new Error("invite_user_missing");
       else invitedId=invited.user.id;
     }else{
       // Existing account: email FIRST, membership finalization SECOND.
       // Previously the database claimed delivery before reset email was sent.
       const {error:resetError}=await guest.auth.resetPasswordForEmail(
         String(decision.email),{redirectTo:passwordSetupUrl+"?mode=first&token_hash="});
       if(resetError)deliveryError=resetError;
     }
     if(deliveryError){
       const code=safeMailCode(deliveryError);
       const action=code==="email_configuration_required"?"action_required":"retry";
       const {error:recordError}=await admin.rpc("promysel_record_registration_invitation",{
         p_request_id:target,p_actor:user.id,p_status:action,p_error_code:code
       });
       if(recordError)console.error("registration mail queue update",recordError.code??"unknown");
       console.warn("registration invitation deferred",JSON.stringify({requestId:target,code}));
       return reply({status:"approved",invitationSent:false,
         invitationStatus:action,
         detail:action==="action_required"
           ?"Заявка согласована. Настройте SMTP, чтобы отправить письмо сотруднику."
           :"Заявка согласована. Почтовый сервис ограничил отправку. Приглашение в очереди."},202);
     }
     if(!invitedId){
       return reply({status:"approved",invitationSent:false,
         detail:"Заявка согласована, но сервер не вернул учётную запись."},202);
     }
     const {error:acceptedError}=await admin.rpc("promysel_record_registration_invitation",{
       p_request_id:target,p_actor:user.id,p_status:"accepted",p_user_id:invitedId
     });
     if(acceptedError){
       console.error("registration mail acceptance bookkeeping",acceptedError.code??"unknown");
       return reply({status:"approved",invitationSent:false,
         detail:"Письмо принято почтой, завершение регистрации требует повторной проверки."},202);
     }
   }
   const {data:finished,error:finishError}=await admin.rpc("promysel_finish_registration_approval",{
     p_request_id:target,p_actor:user.id,p_user_id:invitedId
   });
   if(finishError){
     console.error("approved invite finalization",finishError.code??"unknown");
     return reply({status:"approved",invitationSent:true,
       invitationStatus:"accepted",
       detail:"Письмо отправлено, но привязка сотрудника не завершена. Повторите проверку."},202);
   }
   const {error:completedError}=await admin.rpc("promysel_record_registration_invitation",{
     p_request_id:target,p_actor:user.id,p_status:"sent",p_user_id:invitedId
   });
   if(completedError)console.warn("registration delivery completed with update warning",completedError.code??"unknown");
   return reply({...finished,invitationSent:true,invitationStatus:"sent",
     detail:"Заявка согласована, письмо для установки пароля передано почтовому сервису."});
  }
  if(req.method==="GET"&&(route==="/v1/users"||route==="/v1/registration/users")){
    if(!administrator&&memberships.length===0)return reply({detail:"Нет доступа"},403);
    const fields=administrator?null:memberships.map((m:J)=>String(m.field_id));
    // A complete response is atomic from the perspective of the Flutter client.
    // Do not silently return the first 500 employees or any partial page.
    const rows:J[]=[];const pageSize=200;
    for(let offset=0;offset<10000;offset+=pageSize){
      let q=admin.from("field_memberships")
        .select("user_id,field_id,display_name,role,subrole,approved,blocked,chief_id")
        .order("joined_at",{ascending:false}).order("user_id",{ascending:true})
        .range(offset,offset+pageSize-1);
      if(fields&&fields.length)q=q.in("field_id",fields);
      q=q.in("field_id",activeFields.size?[...activeFields]:["__none__"]);
      const {data,error}=await q;
      if(error)throw error;
      rows.push(...(data??[]));
      if(!data||data.length<pageSize)break;
      if(offset+pageSize>=10000)return reply({detail:"Список персонала превышает ограничение сервера"},503);
    }
    const items=rows.map((m:J)=>({id:m.user_id,name:m.display_name,role:m.role,
      subrole:m.subrole,fieldId:m.field_id,chiefId:m.chief_id,approved:m.approved===true&&m.blocked!==true}));
    return reply({items,count:items.length,complete:true,loadedAt:new Date().toISOString()});
  }
  const roleChange=route.match(/^\/v1\/users\/([0-9a-f-]{36})\/role$/i);
  if(req.method==="POST"&&roleChange){
    const target=roleChange[1],newRole=txt(body.role),subrole=txt(body.subrole);
    const chief=memberships.find((m:J)=>m.role==="shopChief");
    if(!chief||!chief.field_id)return reply({detail:"Только начальник цеха может изменять роли"},403);
    if(target===user.id)return reply({detail:"Изменять свою роль нельзя"},403);
    if(!["operator","engineer","dispatcher"].includes(newRole))
      return reply({detail:"Начальник может назначать только операторов, ИТР и диспетчеров"},400);
    const subs=["leadingGeologist","leadingTechnologist","geologist","technologist","master"];
    if(newRole==="engineer"&&!subs.includes(subrole))
      return reply({detail:"Выберите должность ИТР"},400);
    const {data:worker,error:findErr}=await admin.from("field_memberships")
      .select("user_id,field_id,role,approved,blocked").eq("field_id",chief.field_id)
      .eq("user_id",target).maybeSingle();
    if(findErr)throw findErr;
    if(!worker||worker.approved!==true||worker.blocked===true||
       !["operator","engineer","dispatcher"].includes(String(worker.role)))
      return reply({detail:"Сотрудник недоступен для изменения роли"},403);
    const {error}=await admin.from("field_memberships").update({
      role:newRole,subrole:newRole==="engineer"?subrole:null
    }).eq("field_id",chief.field_id).eq("user_id",target);
    if(error)throw error;
    return reply({status:"updated",userId:target,role:newRole,
      subrole:newRole==="engineer"?subrole:null});
  }
  if(req.method==="POST"&&route==="/v1/profile/name"){
    const name=txt(body.fullName).replace(/\s+/g," ");
    if(name.length<5||name.length>160||name.split(" ").length<2||
       /[<>\r\n\t]/.test(name))
      return reply({detail:"Укажите корректные ФИО (не менее двух слов)"},400);
    if(memberships.length===0&&!elevated)return reply({detail:"Нет действующего допуска"},403);
    const {error}=await admin.from("field_memberships").update({
      display_name:name
    }).eq("user_id",user.id);
    if(error)throw error;
    const {error:metaError}=await admin.auth.admin.updateUserById(user.id,{
      user_metadata:{...user.user_metadata,full_name:name}
    });
    if(metaError)console.warn("Profile metadata sync:",metaError.message);
    return reply({status:"updated",name});
  }
  // Hard-delete an employee account: preserve business evidence, release the email.
  // Both UI callers require scope/name confirmation; this code never trusts a
  // supplied user_id without looking up live memberships and server Auth metadata.
  async function eraseWorkerAccount(target:string,field:string,confirmName:string|null,legacy=false):Promise<Response>{
    if(target===user.id)return reply({detail:"Нельзя удалить собственную учётную запись"},403);
    if(!field)return reply({detail:"Не выбрано месторождение"},400);
    const supervising=memberships.some((m:J)=>m.field_id===field&&m.role==="shopChief");
    if(!administrator&&!supervising)return reply({detail:"Нет права удалять сотрудников этого месторождения"},403);
    const {data:found,error:authErr}=await admin.auth.admin.getUserById(target);
    if(authErr||!found?.user)return reply({detail:"Учётная запись уже удалена"},404);
    const employee=found.user;
    if(employee.app_metadata?.system_admin===true)return reply({detail:"Системного администратора удалять запрещено"},403);
    const email=txt(employee.email).toLowerCase();
    if(!validEmail(email))return reply({detail:"В учётной записи не найдена корректная электронная почта"},409);
    const {data:all,error:memberError}=await admin.from("field_memberships")
      .select("field_id,role,display_name,approved,blocked").eq("user_id",target).limit(20);
    if(memberError)throw memberError;
    const rows=all??[];
    if(legacy){
      if(rows.some((m:J)=>m.approved===true&&m.blocked!==true))return reply({detail:"У сотрудника остались действующие допуски. Сначала удалите его из списка персонала."},409);
      if(rows.some((m:J)=>m.field_id!==field))return reply({detail:"Найдена привязка к другому месторождению; очистка отклонена"},409);
      const {data:approved,error:requestError}=await admin.from("registration_requests")
        .select("id,approved_field_id,field_id").eq("requested_by",target)
        .eq("state","approved").limit(10);
      if(requestError)throw requestError;
      if(!(approved??[]).some((r:J)=>(r.approved_field_id??r.field_id)===field))
        return reply({detail:"Не найдено подтверждения прежней регистрации сотрудника на этом месторождении"},409);
    }else{
      const member=rows.find((m:J)=>m.field_id===field);
      if(!member)return reply({detail:"Сотрудник не найден на выбранном месторождении"},404);
      if(txt(confirmName)!==member.display_name)
        return reply({detail:"Введите точные ФИО сотрудника для подтверждения"},400);
      if(!administrator&&!["operator","engineer","dispatcher"].includes(String(member.role)))
        return reply({detail:"Начальник цеха может удалять только своих сотрудников"},403);
    }
    // Do not accidentally revoke another field's membership or active sessions.
    if(rows.length>1)return reply({detail:"У сотрудника есть доступ к другим месторождениям. Полное удаление аккаунта запрещено до отключения остальных доступов."},409);

    // Redact only personnel-related audit details. Do not delete measurements,
    // operational events or chat messages owned by the field or other people.
    const {error:redactError}=await admin.from("personnel_audit")
      .update({details:{personalDataErased:true,historyPreserved:true}})
      .eq("target_user_id",target);
    if(redactError)throw redactError;

    // Requires the v1.93 SET NULL/CASCADE migration to preserve historic records.
    // A failed delete MUST NOT be represented to the UI as a successful removal.
    const {error:deleteError}=await admin.auth.admin.deleteUser(target,false);
    if(deleteError){
      console.error("Personnel Auth hard-delete failed:",deleteError.message);
      return reply({detail:"Не удалось полностью удалить аккаунт. Доступ не был подтверждён как удалённый; обратитесь к администратору.",code:"AUTH_DELETE_FAILED"},409);
    }
    const failed:string[]=[];
    for(const table of ["promysel_push_subscriptions","promysel_push_events"]){
      const {error}=await admin.from(table).delete().eq("user_id",target);
      if(error){console.error("Personnel cleanup",table,error.message);failed.push(table);}
    }
    const {error:requestCleanup}=await admin.from("registration_requests")
      .delete().eq("email",email);
    if(requestCleanup){console.error("Registration cleanup:",requestCleanup.message);failed.push("registration_requests");}
    // The audit record has no personal identifiers; immutable field records remain.
    const {error:auditError}=await admin.from("personnel_audit")
      .insert({field_id:field,actor_id:user.id,action:"employee_account_erased",
        details:{historyPreserved:true,emailReleased:!requestCleanup}});
    if(auditError)console.warn("Deletion audit not stored:",auditError.message);
    if(failed.length)return reply({status:"partially_deleted",historyPreserved:true,
      detail:"Учётная запись удалена, но очистка связанных записей завершилась с ошибкой. Обратитесь к системному администратору.",
      cleanupIncomplete:failed},500);
    return reply({status:"deleted",historyPreserved:true,emailReusable:true,
      detail:"Учётная запись полностью удалена. Электронная почта свободна для новой регистрации."});
  }
  const deleteUser=route.match(/^\/v1\/users\/([0-9a-f-]{36})$/i);
  if(req.method==="DELETE"&&deleteUser){
    const field=fieldTag(body.fieldId);
    return await eraseWorkerAccount(deleteUser[1],field,txt(body.confirmName),false);
  }


  // Sensitive administrative operations are checked against signed app_metadata on the server.
  const fRoute=route.match(/^\/v1\/admin\/fields\/([^/]+)$/);
  const uRoute=route.match(/^\/v1\/admin\/users\/([0-9a-f-]{36})$/i);
  if(route.startsWith("/v1/admin/")&&!administrator)return reply({detail:"Только системному администратору"},403);
  // Legacy: earlier admin removal only deleted membership, leaving Auth/email.
  // A separate, explicitly confirmed action can clean up ONLY an orphaned account.
  if(route==="/v1/admin/removed-users/cleanup"&&req.method==="POST"){
    const email=txt(body.email).toLowerCase(),confirm=txt(body.confirmEmail).toLowerCase();
    if(!validEmail(email)||email!==confirm)return reply({detail:"Подтвердите точную электронную почту дважды"},400);
    const {data:requests,error:requestError}=await admin.from("registration_requests")
      .select("requested_by,approved_field_id,field_id").eq("email",email)
      .eq("state","approved").order("created_at",{ascending:false}).limit(5);
    if(requestError)throw requestError;
    const r=(requests??[]).find((x:J)=>x.requested_by&&(x.approved_field_id||x.field_id));
    if(!r)return reply({detail:"Не найдено прежней согласованной регистрации"},404);
    const {data:existing,error:lookupError}=await admin.auth.admin.getUserById(String(r.requested_by));
    if(lookupError||!existing?.user)return reply({detail:"Auth-аккаунт уже отсутствует; обратитесь к администратору для очистки устаревшей заявки"},409);
    if(txt(existing.user.email).toLowerCase()!==email)return reply({detail:"Почта не совпадает с учётной записью"},409);
    return await eraseWorkerAccount(String(r.requested_by),String(r.approved_field_id??r.field_id),null,true);
  }

  if(req.method==="POST"&&route==="/v1/admin/fields"){
   const name=txt(body.name).replace(/\s+/g," ");if(name.length<3||name.length>160)return reply({detail:"Некорректное название"},400);
   const id="field-"+crypto.randomUUID();const {error}=await admin.from("oil_fields").insert({id,name});
   if(error)return reply({detail:error.message},409);
   await admin.from("personnel_audit").insert({field_id:id,actor_id:user.id,action:"field_create",details:{name}});
   return reply({id,name,status:"created"});
  }
  if(fRoute&&req.method==="PATCH"){
   const id=fRoute[1],name=txt(body.name).replace(/\s+/g," ");
   if(name.length<3||name.length>160)return reply({detail:"Некорректное название"},400);
   const {data,error}=await admin.from("oil_fields").update({name}).eq("id",id).is("archived_at",null).select("id").maybeSingle();
   if(error)return reply({detail:error.message},409);if(!data)return reply({detail:"Месторождение не найдено"},404);
   await admin.from("personnel_audit").insert({field_id:id,actor_id:user.id,action:"field_rename",details:{name}});
   return reply({id,name,status:"updated"});
  }
  if(fRoute&&req.method==="DELETE"){
   const id=fRoute[1];const {data:field,error:findError}=await admin.from("oil_fields").select("id,name").eq("id",id).is("archived_at",null).maybeSingle();
   if(findError)throw findError;if(!field)return reply({detail:"Месторождение не найдено"},404);
   if(txt(body.confirmName)!==field.name)return reply({detail:"Введите точное название месторождения"},400);
   // Reversible archival avoids cascaded destruction of pads, wells, history and tasks.
   const {error}=await admin.from("oil_fields").update({archived_at:new Date().toISOString()}).eq("id",id).is("archived_at",null);
   if(error)throw error;
   await admin.from("personnel_audit").insert({field_id:id,actor_id:user.id,action:"field_archive",details:{name:field.name,historyPreserved:true}});
   return reply({id,status:"archived",historyPreserved:true});
  }
  if(uRoute&&req.method==="PATCH"){
   const target=uRoute[1],name=txt(body.fullName).replace(/\s+/g," "),role=txt(body.role),
     subrole=txt(body.subrole),oldField=txt(body.oldFieldId),newField=txt(body.fieldId),chiefId=txt(body.chiefId);
   if(target===user.id)return reply({detail:"Нельзя изменять свой профиль администратора"},403);
   if(name.length<5||name.length>160||name.split(" ").length<2||/[<>\r\n\t]/.test(name))return reply({detail:"Некорректные ФИО"},400);
   if(!["operator","engineer","dispatcher","shopChief","manager"].includes(role))return reply({detail:"Недопустимая роль"},400);
   if(role==="engineer"&&!["leadingGeologist","leadingTechnologist","geologist","technologist","master"].includes(subrole))return reply({detail:"Выберите должность ИТР"},400);
   const {data:field}=await admin.from("oil_fields").select("id").eq("id",newField).is("archived_at",null).maybeSingle();
   if(!field)return reply({detail:"Месторождение недоступно"},404);
   const {data:worker}=await admin.from("field_memberships").select("user_id").eq("user_id",target).eq("field_id",oldField).maybeSingle();
   if(!worker)return reply({detail:"Сотрудник не найден"},404);
   if(chiefId&&role!=="shopChief"){
    const {data:chief}=await admin.from("field_memberships").select("user_id").eq("user_id",chiefId).eq("field_id",newField)
      .eq("role","shopChief").eq("approved",true).eq("blocked",false).maybeSingle();
    if(!chief)return reply({detail:"Начальник цеха не найден в выбранном месторождении"},400);
   }
   const {error}=await admin.from("field_memberships").update({field_id:newField,display_name:name,role,
     subrole:role==="engineer"?subrole:null,chief_id:role==="shopChief"?null:chiefId||null})
     .eq("user_id",target).eq("field_id",oldField);
   if(error)return reply({detail:error.message},409);
   await admin.from("personnel_audit").insert({field_id:newField,actor_id:user.id,target_user_id:target,action:"admin_update",
     details:{name,role,oldField,newField,chiefId}});
   return reply({status:"updated",userId:target});
  }
  if(uRoute&&req.method==="DELETE"){
    return await eraseWorkerAccount(uRoute[1],fieldTag(body.fieldId),txt(body.confirmName),false);
  }



  // Daily presence is shared across profile, roster and dashboard. Supervisor edits are
  // field-scoped and audited with the server-authenticated user.
  if(route==="/v1/presence"&&req.method==="GET"){
    const u=new URL(req.url);
    const fid=fieldTag(u.searchParams.get("fieldId")),day=txt(u.searchParams.get("day"));
    if(!/^\d{4}-\d{2}-\d{2}$/.test(day)||!fid)return reply({detail:"Неверная дата или месторождение"},400);
    if(!administrator&&!canField(fid))return reply({detail:"Нет доступа к месторождению"},403);
    const {data,error}=await admin.from("promysel_daily_presence")
      .select("user_id,is_working,updated_at").eq("field_id",fid).eq("work_day",day).limit(1000);
    if(error)throw error;
    return reply({fieldId:fid,day,items:(data??[]).map((x:J)=>({
      id:x.user_id,atWork:x.is_working,updatedAt:x.updated_at
    }))});
  }
  const presenceRoute=route.match(/^\/v1\/presence\/([0-9a-f-]{36})$/i);
  if(presenceRoute&&req.method==="PATCH"){
    const fid=fieldTag(body.fieldId),day=txt(body.day),target=presenceRoute[1];
    if(!fid||!/^\d{4}-\d{2}-\d{2}$/.test(day)||typeof body.atWork!=="boolean")
      return reply({detail:"Неверные данные статуса"},400);
    const todayUTC=new Date();
    const parsed=Date.parse(day+"T12:00:00Z");
    if(!Number.isFinite(parsed)||Math.abs(parsed-todayUTC.getTime())>3*86400000)
      return reply({detail:"Разрешено менять только текущий день"},400);
    const membership=canField(fid);
    const supervisor=administrator||membership?.role==="shopChief"||
      (membership?.role==="engineer"&&membership?.subrole==="master");
    if(!administrator&&!membership)return reply({detail:"Нет доступа к месторождению"},403);
    if(target!==user.id&&!supervisor)return reply({detail:"Изменять статус другого сотрудника может только руководитель"},403);
    const {data:worker,error:check}=await admin.from("field_memberships")
      .select("user_id").eq("field_id",fid).eq("user_id",target)
      .eq("approved",true).eq("blocked",false).maybeSingle();
    if(check)throw check;
    if(!worker)return reply({detail:"Сотрудник не найден в месторождении"},404);
    const atWork=body.atWork as boolean;
    const {error}=await admin.from("promysel_daily_presence").upsert({
      field_id:fid,user_id:target,work_day:day,
      is_working:atWork,changed_by:user.id,updated_at:new Date().toISOString()
    },{onConflict:"field_id,user_id,work_day"});
    if(error)throw error;
    return reply({id:target,fieldId:fid,day,atWork,status:"updated"});
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
  // A personal avatar is not a privileged field-wide app_state update.
  // Operators and engineers can update only their OWN photo with membership
  // verification and a revision guard; stale devices receive HTTP 409.
  if(route==="/v1/avatar/mutate"&&req.method==="POST"){
    const fid=fieldTag(body.fieldId);
    if(!canField(fid))return reply({detail:"Нет допуска к месторождению"},403);
    const kind=txt(body.kind),operationId=txt(body.operationId);
    const expected=Number(body.expectedRevision);
    if(!["set","delete"].includes(kind)||
      !/^[a-zA-Z0-9:_-]{8,120}$/.test(operationId)||
      !Number.isSafeInteger(expected)||expected<0)
      return reply({detail:"Некорректная версия фотографии"},400);
    const value=kind==="delete"?"__deleted__":txt(body.avatar);
    if(kind==="set"&&(value.length<24||value.length>900000||
      !/^[A-Za-z0-9+/=]+$/.test(value)))
      return reply({detail:"Некорректное изображение"},400);
    const {data:result,error}=await admin.rpc("promysel_avatar_commit_v206",{
      p_field_id:fid,p_user_id:user.id,p_avatar:value,
      p_expected_revision:expected,p_operation_id:operationId
    });
    if(error){
      console.error("promysel avatar update",error.code??"unknown");
      return reply({detail:"Не удалось сохранить фотографию"},503);
    }
    if(result?.status==="conflict")return reply(
      {status:"conflict",revision:result.revision,
       detail:"Фотография изменена на другом устройстве. Обновите профиль."},409);
    return reply({status:result?.status??"ok",revision:result?.revision??0});
  }

  // v2.11 Independent domain revisions: no direct Data API table grants.
  if(route==="/v1/sync/domain/revisions"&&req.method==="GET"){
    const field=fieldTag(new URL(req.url).searchParams.get("fieldId"));
    if(!canField(field))return reply({detail:"Нет доступа к месторождению"},403);
    const {data,error}=await admin.from("promysel_sync_domain_state")
      .select("domain,revision").eq("field_id",field).limit(4);
    if(error)throw error;
    const revisions:J={tasks:0,schedules:0,training:0,structure:0};
    for(const x of data??[])revisions[String(x.domain)]=Number(x.revision);
    return reply({revisions});
  }
  if(route==="/v1/sync/domain/push"&&req.method==="POST"){
    const field=fieldTag(body.fieldId),domain=txt(body.domain),
      op=txt(body.key),device=txt(body.deviceId);
    const m=canField(field);
    if(!m)return reply({detail:"Нет допуска к месторождению"},403);
    if(!["tasks","schedules","training","structure"].includes(domain)||
      op.length<8||op.length>300||device.length<1||device.length>200||
      !good(body.payload)||!Number.isSafeInteger(Number(body.expectedRevision))||
      Number(body.expectedRevision)<0)
      return reply({detail:"Некорректные данные операции"},400);
    const src=body.payload as J,role=String(m.role),chief=role==="shopChief"||elevated,
      engineer=role==="engineer",master=engineer&&m.subrole==="master";
    const specialist=engineer&&["geologist","technologist",
      "leadingGeologist","leadingTechnologist"].includes(String(m.subrole));
    const current=(await effectiveState(field)).snapshot??{fieldId:field} as J;
    const dst:J={fieldId:field};
    const same=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
    const valid=(id:unknown)=>typeof id==="string"&&id.length>0&&id.length<=180;
    if(domain==="tasks"){
      if(!Array.isArray(src.tasks)||src.tasks.length>1000)
        return reply({detail:"Список заданий превышает ограничения"},400);
      const old=new Map<string,J>((Array.isArray(current.tasks)?current.tasks:[])
        .filter(good).map((v:J)=>[String(v.id),v]));
      // Masters can confirm only tasks directed to APPROVED operators,
      // never every personal task in the field.
      const masterOperatorIds=new Set<string>();
      if(master){
        const {data:operators,error:operatorsError}=await admin.from("field_memberships")
          .select("user_id").eq("field_id",field).eq("role","operator")
          .eq("approved",true).eq("blocked",false);
        if(operatorsError)throw operatorsError;
        for(const row of operators??[])masterOperatorIds.add(String(row.user_id));
      }
      const changed:J[]=[];
      for(const raw of src.tasks){
        if(!good(raw))continue;
        const row=raw as J,id=txt(row.id),prev=old.get(id);
        if(!valid(id)||String(row.fieldId??field)!==field)continue;
        if(!prev){
          if(!(chief||engineer)||String(row.createdById)!==user.id||
             !["personal","area","pad"].includes(String(row.targetType)))continue;
          changed.push({...row,fieldId:field,createdById:user.id,status:"active",
            completedAt:null,confirmedAt:null});continue;
        }
        if(same(row,prev))continue;
        const before=String(prev.status),after=String(row.status);
        const completer=prev.targetType==="personal"?String(prev.targetId)===user.id:
          ["area","pad"].includes(String(prev.targetType))&&(role==="operator"||engineer||chief);
        const reviewer=chief||String(prev.createdById)===user.id||
          (master&&prev.targetType==="personal"&&masterOperatorIds.has(String(prev.targetId)));
        if(before==="confirmed"&&after!=="confirmed")continue;
        if(before==="active"&&after==="awaitingConfirmation"&&completer){
          changed.push({...prev,status:"awaitingConfirmation",
            completedById:user.id,completedBy:m.display_name,
            completedAt:new Date().toISOString(),
            completionComment:txt(row.completionComment).slice(0,2000)});continue;
        }
        if(before==="awaitingConfirmation"&&after==="confirmed"&&reviewer){
          changed.push({...prev,status:"confirmed",confirmedById:user.id,
            confirmedBy:m.display_name,confirmedAt:new Date().toISOString()});continue;
        }
        if(before==="awaitingConfirmation"&&after==="active"&&reviewer&&row.rejectedAt){
          changed.push({...prev,status:"active",rejectedAt:new Date().toISOString(),
            rejectedBy:m.display_name,rejectionComment:txt(row.rejectionComment).slice(0,2000),
            completedAt:null,completedBy:null,completedById:null});continue;
        }
        if((chief||String(prev.createdById)===user.id)&&before===after){
          const edited={...prev,title:txt(row.title).slice(0,180)||prev.title,
            description:txt(row.description).slice(0,5000)};
          if(!same(edited,prev))changed.push(edited);
        }
      }
      if(!changed.length)return reply({status:"noop",domain});
      dst.tasks=changed;
    }else if(domain==="schedules"){
      const schedules=good(src.workSchedules)?src.workSchedules as J:{};
      const own=schedules[user.id];
      if(!good(own))return reply({status:"noop",domain});
      if(JSON.stringify(own).length>65000)return reply({detail:"Слишком большой график"},413);
      const earlier=(good(current.workSchedules)?(current.workSchedules as J)[user.id]:null) as J|null;
      if(earlier&&Date.parse(String(earlier.updated??""))>
           Date.parse(String((own as J).updated??"")))
        return reply({detail:"График изменён на другом устройстве",domain,status:"conflict"},409);
      if(same(own,earlier))return reply({status:"noop",domain});
      dst.workSchedules={[user.id]:own};
    }else if(domain==="training"){
      const items=Array.isArray(src.training)?src.training:[];
      if(items.length>2000)return reply({detail:"Слишком много записей обучения"},413);
      const prev=new Map<string,J>((Array.isArray(current.training)?current.training:[])
        .filter(good).map((x:J)=>[String(x.id),x]));
      const changed:J[]=[];
      for(const raw of items){
        if(!good(raw))continue;const x=raw as J,id=txt(x.id),owner=txt(x.userId);
        if(!valid(id)||!owner||(owner!==user.id&&!chief))continue;
        if(prev.has(id)&&String(prev.get(id)?.userId)!==owner)continue;
        const oldDate=Date.parse(String(prev.get(id)?.updatedAt??""));
        const newDate=Date.parse(String(x.updatedAt??""));
        if(Number.isFinite(oldDate)&&(!Number.isFinite(newDate)||newDate<oldDate))continue;
        if(!same(prev.get(id),x))changed.push(x);
      }
      const deleted=(Array.isArray(src.trainingDeletedIds)?src.trainingDeletedIds:[])
        .map(String).filter((id:string)=>valid(id)&&
          (chief||String(prev.get(id)?.userId)===user.id)).slice(0,2000);
      if(!changed.length&&!deleted.length)return reply({status:"noop",domain});
      dst.training=changed;dst.trainingDeletedIds=deleted;
    }else if(domain==="structure"){
      if(!(chief||specialist))return reply({detail:"Нет прав изменять структуру"},403);
      for(const section of ["areas","pads"]){
        const list=Array.isArray(src[section])?src[section]:[];
        if(list.length>2000)return reply({detail:"Слишком много объектов структуры"},413);
        const previous=new Map<string,J>((Array.isArray(current[section])?current[section]:[])
          .filter(good).map((v:J)=>[String(v.id),v]));
        dst[section]=list.filter(good).filter((v:J)=>valid(v.id)&&
          (!v.fieldId||v.fieldId===field)&&
          (!previous.has(String(v.id))||
            (Date.parse(String(v.updatedAt??""))||0)>=
            (Date.parse(String(previous.get(String(v.id))?.updatedAt??""))||0)));
      }
      if(good(src.walkConfig))dst.walkConfig=src.walkConfig;
      const oldDeleted=deletedStructure(current.structureDeleted);
      const newDeleted=deletedStructure(src.structureDeleted);
      if(!chief&&(["areas","pads","wells"] as const).some(
        k=>newDeleted[k].some(id=>!oldDeleted[k].includes(id))))
        return reply({detail:"Удалять структуру может только начальник цеха"},403);
      dst.structureDeleted=newDeleted;
    }
    const {data:result,error:mutationError}=await admin.rpc("promysel_commit_sync_domain",{
      p_field_id:field,p_domain:domain,p_mutation_key:op,p_device_id:device,
      p_actor:user.id,p_expected_revision:Number(body.expectedRevision),p_payload:dst
    });
    if(mutationError)throw mutationError;
    if(result?.status==="conflict")
      return reply({status:"conflict",domain,revision:result.revision,
        detail:"Раздел изменён на другом устройстве; нужна повторная загрузка"},409);
    if(domain==="tasks"&&(result?.status==="accepted"||result?.status==="duplicate")){
      for(const row of dst.tasks as J[]){
        const {error:scopeError}=await admin.from("promysel_task_scopes")
          .upsert({task_id:String(row.id),field_id:field,scope_source:"domain-v211"},
            {onConflict:"task_id",ignoreDuplicates:true});
        if(scopeError)throw scopeError;
      }
    }
    return reply({status:result?.status??"accepted",domain,revision:result?.revision??0});
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
    // Fast no-change path: one indexed sequence lookup replaces two or more
    // payload / snapshot queries during normal idle polling. Full recovery,
    // including old immutable measurements, always bypasses this shortcut.
    const fullRestore=cursor==="0"||url.searchParams.get("recover")==="1";
    if(!fullRestore){
      const {data:changed,error:checkError}=await admin.from("sync_events")
        .select("sequence").eq("field_id",fieldId)
        .gt("sequence",Number(cursor)).order("sequence",{ascending:false}).limit(1);
      if(checkError)throw checkError;
      if(!changed?.length)return reply({cursor,items:[]});
    }
    // HOTFIX 2026-11-04: avoid full app_state history replay.
    // Full snapshots carry inline avatars; fetching 100+ duplicates caused
    // PostgREST 57014 statement timeouts and sync/pull HTTP 500.
    const {data:recent,error:seqError}=await admin.from("sync_events")
      .select("sequence").eq("field_id",fieldId)
      .in("event_type",["app_state","avatar_change","domain_change"])
      .order("sequence",{ascending:false}).limit(1);
    if(seqError)throw seqError;
    const latestRelevantSeq=Number(recent?.[0]?.sequence??0);
    const {data,error}=await actorClient.from("sync_events")
      .select("sequence,event_key,payload,client_updated_at")
      .eq("field_id",fieldId).eq("event_type","measurement")
      .gt("sequence",Number(cursor)).order("sequence",{ascending:true}).limit(200);
    if(error)throw error;
    const output=(data??[]).map((x:J)=>({key:x.event_key,type:"measurement",
      updatedAt:x.client_updated_at,payload:x.payload}));
    const lastMeasurementSeq=data?.length?Number(data[data.length-1].sequence):Number(cursor);
    // Never move the cursor over a measurement page we have not delivered.
    const moreMeasurements=(data?.length??0)>=200;
    let stateDeliveredSeq=0;let deliveredDomainRevisions:J={};
    if((fullRestore||latestRelevantSeq>Number(cursor))&&(!moreMeasurements||fullRestore)){
      const repaired=await effectiveState(fieldId);
      if(repaired.snapshot){deliveredDomainRevisions=repaired.revisions;
        if(fullRestore&&cursor!=="0"){
          // Explicit recovery also replays old immutable measurements.
          const {data:archive,error:archiveError}=await actorClient.from("sync_events")
            .select("event_key,payload,client_updated_at")
            .eq("field_id",fieldId).eq("event_type","measurement")
            .order("sequence",{ascending:false}).limit(200);
          if(archiveError)throw archiveError;
          const seen=new Set(output.map((e:J)=>String(e.key)));
          for(const e of [...(archive??[])].reverse()){
            if(seen.has(String(e.event_key)))continue;
            seen.add(String(e.event_key));
            output.push({key:e.event_key,type:"measurement",
              updatedAt:e.client_updated_at,payload:e.payload});
          }
        }
        // The field-wide snapshot is for synchronization, not an entitlement
        // to see every colleague's personal task or completed history.
        // Apply the SAME rules server-side: browser devtools cannot bypass it.
        const snapshot={...repaired.snapshot};
        // v2.13: Most app_state payload bytes are inline profile photos.
        // Only send photos absent/changed on THIS device; cached photos stay
        // in AppStateStore.reconcileWithCurrent. Deletion tombstones are sent
        // whenever their hash differs. No photos are removed from the DB.
        const cacheParam=url.searchParams.get("avatarCache")??"";
        let cachedAvatars:J={};
        if(cacheParam.length>0&&cacheParam.length<=4096){
          try{
            const decoded=JSON.parse(cacheParam);
            if(good(decoded))cachedAvatars=decoded as J;
          }catch(_){/* Unknown/old clients receive all profile photos. */}
        }
        if(good(snapshot.avatars)){
          const changedAvatars:J={};
          for(const [id,rawValue] of Object.entries(snapshot.avatars as J)){
            if(typeof rawValue!=="string")continue;
            // A claimed hash is just a network optimization, never evidence of
            // access and never used to authorize a read or update.
            if(cachedAvatars[id]!==avatarTransportDigest(rawValue))
              changedAvatars[id]=rawValue;
          }
          snapshot.avatars=changedAvatars;
        }
        const allTasks=Array.isArray(snapshot.tasks)?snapshot.tasks as J[]:[];
        const viewerId=user.id;
        const chief=String(member.role)==="shopChief";
        const master=String(member.role)==="engineer"&&String(member.subrole)==="master";
        let operatorIds=new Set<string>();
        if(master){
          const {data:operators,error:operatorsError}=await admin.from("field_memberships")
            .select("user_id").eq("field_id",fieldId).eq("role","operator")
            .eq("approved",true).eq("blocked",false);
          if(operatorsError)throw operatorsError;
          operatorIds=new Set((operators??[]).map(x=>String(x.user_id)));
        }
        snapshot.tasks=allTasks.filter(t=>{
          if(chief)return true;
          const related=t.createdById===viewerId||
            (t.targetType==="personal"&&t.targetId===viewerId)||
            t.completedById===viewerId||t.confirmedById===viewerId;
          if(related)return true;
          if(master&&t.targetType==="personal"&&operatorIds.has(String(t.targetId)))return true;
          // Open common work is visible to its field until confirmed. Its
          // completed history remains limited to actual participants.
          return t.status!=="confirmed"&&(t.targetType==="area"||t.targetType==="pad");
        });
        snapshot.notifications=(Array.isArray(snapshot.notifications)?snapshot.notifications as J[]:[])
          .filter(n=>String(n.userId??"")===viewerId);
        const recoveredSeq=Math.max(repaired.seq,latestRelevantSeq);
        output.push({key:"recovered:"+fieldId+":"+String(recoveredSeq),
          type:"app_state",updatedAt:new Date().toISOString(),payload:snapshot});
        // A recovered snapshot may be returned with page one, but its sequence
        // must never skip measurement pages that have not been delivered yet.
        stateDeliveredSeq=moreMeasurements?0:recoveredSeq;
      }
    }
    return reply({cursor:String(Math.max(Number(cursor),lastMeasurementSeq,stateDeliveredSeq)),
      items:output,domainRevisions:deliveredDomainRevisions});
   }
   const device=txt(body.deviceId),items=body.items;
   if(!device||device.length>200||!Array.isArray(items)||items.length<1||items.length>100)
      return reply({detail:"Некорректный пакет синхронизации"},400);
   const specialist=member.role==="engineer"&&["geologist","technologist","leadingGeologist","leadingTechnologist"].includes(String(member.subrole));
   const canStructure=member.role==="shopChief"||member.role==="admin"||specialist;
   const canWalk=["operator","engineer","shopChief"].includes(String(member.role));
   const records:J[]=[];
   const ordinaryRecords:J[]=[],scopedMiscRecords:J[]=[];
   const tombstoneRequests:{field_id:string,kind:string,entity_id:string,actor_id:string}[]=[];
   for(const item of items){
    if(!good(item)||!good(item.payload))return reply({detail:"Некорректный элемент синхронизации"},400);
    const i=item as J,key=txt(i.key),type=txt(i.type);let payload=i.payload as J;
    if(key.length<1||key.length>300||!["measurement","app_state"].includes(type))return reply({detail:"Неверный тип изменения"},400);
    if(type==="measurement"&&!canWalk)return reply({detail:"Нет прав на изменение"},403);
    const operatorMisc=type==="app_state"&&!canStructure;
    if(operatorMisc){
      if(!canWalk)return reply({detail:"Нет прав на изменение"},403);
      const scoped=scopedOperatorMisc(payload,user.id,fieldId);
      if(!scoped)return reply({detail:"Требуется обновить приложение для безопасной отправки изменений этого раздела"},403);
      payload=scoped;
    }
    if(type==="app_state"&&payload.fieldId!==fieldId)return reply({detail:"Месторождение снимка не совпадает"},403);
    if(type==="app_state"&&payload.structureDeleted!==undefined){
      if(!good(payload.structureDeleted))return reply({detail:"Некорректные метки удаления"},400);
      const markerMap=deletedStructure(payload.structureDeleted);
      const count=markerMap.areas.length+markerMap.pads.length+markerMap.wells.length;
      if(count>5000)return reply({detail:"Слишком много меток удаления"},413);
      for(const kind of ["areas","pads","wells"] as const){
        for(const entity_id of markerMap[kind]){
          tombstoneRequests.push({field_id:fieldId,kind,entity_id,actor_id:user.id});
        }
      }
    }
    const record:J={event_key:key,field_id:fieldId,device_id:device,event_type:type,
     payload,actor_id:user.id,client_updated_at:i.updatedAt??null};
    records.push(record);
    if(operatorMisc)scopedMiscRecords.push(record);else ordinaryRecords.push(record);
   }
   // Server-enforced role gate: regular ITR can edit names but cannot introduce
   // deletion markers. Already recorded markers may be relayed by any writer.
   if(tombstoneRequests.length){
     const {data:present,error:presentError}=await admin.from("promysel_structure_tombstones")
       .select("kind,entity_id").eq("field_id",fieldId).limit(10000);
     if(presentError)throw presentError;
     const known=new Set((present??[]).map(x=>String(x.kind)+":"+String(x.entity_id)));
     const unique=new Map<string,typeof tombstoneRequests[number]>();
     for(const row of tombstoneRequests)unique.set(row.kind+":"+row.entity_id,row);
     const fresh=[...unique].filter(([key])=>!known.has(key)).map(([,value])=>value);
     const leader=member.role==="shopChief"||member.role==="admin";
     if(fresh.length&&!leader)return reply({detail:"Удалять участки, кусты и скважины может только начальник цеха"},403);
     if(fresh.length){
       const {error:insertError}=await admin.from("promysel_structure_tombstones")
         .upsert(fresh,{onConflict:"field_id,kind,entity_id",ignoreDuplicates:true});
       if(insertError)throw insertError;
     }
   }
   // Ordinary measurements and structural snapshots continue through RLS.
   if(ordinaryRecords.length){
     const {error}=await actorClient.from("sync_events").upsert(ordinaryRecords,{onConflict:"event_key",ignoreDuplicates:true});
     if(error)throw error;
   }
   // Strictly scoped operator misc is written by the trusted server after
   // authenticating actor and field. No structure, tasks, or third-party
   // notifications are included, and original event keys remain idempotent.
   if(scopedMiscRecords.length){
     const {error}=await admin.from("sync_events").upsert(scopedMiscRecords,{onConflict:"event_key",ignoreDuplicates:true});
     if(error)throw error;
   }
   return reply({accepted:records.map((x:J)=>x.event_key)});
  }
  return reply({detail:"Маршрут не найден"},404);
 }catch(e){
  // PostgREST errors are plain objects, not Error instances.
  // Log only safe structural diagnostics; never log bearer tokens,
  // personal data, measurements or the full request body.
  const err=e&&typeof e==="object"?e as Record<string,unknown>:{};
  const code=typeof err.code==="string"?err.code:"unclassified";
  const message=typeof err.message==="string"?err.message:(e instanceof Error?e.message:"unknown");
  console.error("promysel-compat failure",JSON.stringify({
    route,method:req.method,code,
    message:message.slice(0,280),
    hint:typeof err.hint==="string"?err.hint.slice(0,220):undefined,
    details:typeof err.details==="string"?err.details.slice(0,220):undefined,
  }));
  return reply({detail:"Ошибка обмена данными на сервере. Локальные изменения сохранены.",
    code:code==="unclassified"?"SERVER_ERROR":code},500);
 }
});