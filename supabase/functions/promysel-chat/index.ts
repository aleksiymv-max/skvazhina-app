import {createClient} from 'npm:@supabase/supabase-js@2.57.0';
const base=Deno.env.get('SUPABASE_URL')??'', key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')??'';
const db=createClient(base,key,{auth:{persistSession:false,autoRefreshToken:false}});
const H={'access-control-allow-origin':'*','access-control-allow-methods':'GET,POST,PATCH,DELETE,OPTIONS','access-control-allow-headers':'authorization,content-type,apikey,x-client-info','content-type':'application/json; charset=utf-8','cache-control':'no-store'};
const response=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:H});
const str=(v:unknown)=>typeof v==='string'?v.trim():'';
const validUuid=(s:string)=>/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(s);
const B='promysel-chat';
const safeName=(s:string)=>s.replace(/[^\p{L}\p{N}._ -]/gu,'_').slice(0,100)||'media';
type J=Record<string,unknown>;
Deno.serve(async(req:Request)=>{
 if(req.method==='OPTIONS')return new Response(null,{headers:H,status:204});
 try{
  const token=(req.headers.get('authorization')??'').replace(/^Bearer\s+/i,'').trim();
  if(!token)return response({detail:'Нужна авторизация'},401);
  const {data:identity,error:authError}=await db.auth.getUser(token);
  const uid=identity.user?.id;if(authError||!uid)return response({detail:'Сессия истекла'},401);
  const url=new URL(req.url), path=url.pathname.replace(/^.*\/promysel-chat/,'')||'/';
  const body=(req.method==='GET')?{}:await req.json().catch(()=>({}));
  const value=body&&typeof body==='object'&&!Array.isArray(body)?body as J:{};
  const field=str(url.searchParams.get('fieldId')||value.fieldId);
  const {data:memberships,error:memErr}=await db.from('field_memberships').select('field_id').eq('user_id',uid).eq('approved',true).eq('blocked',false);
  if(memErr)throw memErr;
  const allowed=(memberships??[]).map(x=>String(x.field_id));
  if(!allowed.length)return response({detail:'Нет допуска к месторождению'},403);
  async function active(fid:string){if(!allowed.includes(fid))return false;const {data}=await db.from('oil_fields').select('id').eq('id',fid).is('archived_at',null).maybeSingle();return !!data;}
  async function roomAccess(roomId:string){
    if(!validUuid(roomId))return null;
    const {data:member}=await db.from('promysel_chat_members').select('room_id,muted,sound_enabled,last_read_at').eq('room_id',roomId).eq('user_id',uid).maybeSingle();
    if(!member)return null;
    const {data:room}=await db.from('promysel_chat_rooms').select('*').eq('id',roomId).maybeSingle();
    if(!room||!await active(String(room.field_id)))return null;
    return {room,member};
  }
  if(req.method==='GET'&&path==='/users'){
   if(!await active(field))return response({detail:'Месторождение недоступно'},403);
   const {data,error}=await db.from('field_memberships').select('user_id,display_name,role').eq('field_id',field).eq('approved',true).eq('blocked',false).order('display_name').limit(300);
   if(error)throw error;return response({items:(data??[]).map(x=>({id:x.user_id,name:x.display_name,role:x.role}))});
  }
  if(req.method==='GET'&&path==='/rooms'){
   if(!await active(field))return response({detail:'Месторождение недоступно'},403);
   // One SQL statement replaces the N+1 requests formerly triggered per room.
   const {data,error}=await db.rpc('promysel_chat_listing',{p_user:uid,p_field:field});
   if(error)throw error;
   const items=Array.isArray(data)?data as J[]:[];
   // Only group photos live in private Storage. Individual user pictures use the synchronized profile avatar store.
   const decorated=await Promise.all(items.map(async r=>{
     const avatarPath=str(r.avatar_path);
     if(!avatarPath||r.kind!=='group')return {...r,avatarUrl:null};
     const {data:link}=await db.storage.from(B).createSignedUrl(avatarPath,1800);
     return {...r,avatarUrl:link?.signedUrl??null};
   }));
   return response({items:decorated});
  }
  if(req.method==='POST'&&path==='/rooms'){
   if(!await active(field))return response({detail:'Месторождение недоступно'},403);
   const kind=str(value.kind),title=str(value.title).slice(0,100);
   if(!['private','group','saved'].includes(kind))return response({detail:'Неверный тип чата'},400);
   const targets=Array.isArray(value.people)?[...new Set(value.people.map(str))]:[];
   const participants=[...new Set([uid,...(kind==='saved'?[]:targets)])];
   if(kind==='private'&&(participants.length!==2||!targets.length))return response({detail:'Выберите одного собеседника'},400);
   if(kind==='group'&&(!title||participants.length<2||participants.length>101))return response({detail:'Название и участники группы обязательны'},400);
   if(kind==='saved'&&participants.length!==1)return response({detail:'Избранное только для себя'},400);
   if(participants.some(id=>!validUuid(id)))return response({detail:'Неверный участник'},400);
   const {data:eligible,error:eerr}=await db.from('field_memberships').select('user_id').eq('field_id',field).eq('approved',true).eq('blocked',false).in('user_id',participants);
   if(eerr)throw eerr;if((eligible??[]).length!==participants.length)return response({detail:'Участник не работает в этом месторождении'},403);
   const pairKey=kind==='group'?null:`${field}:${kind}:${participants.slice().sort().join(':')}`;
   if(pairKey){const {data:existing}=await db.from('promysel_chat_rooms').select('id').eq('pair_key',pairKey).maybeSingle();if(existing){await db.from('promysel_chat_members').update({hidden:false}).eq('room_id',existing.id).eq('user_id',uid);return response({id:existing.id});}}
   const {data:room,error:rerr}=await db.from('promysel_chat_rooms').insert({field_id:field,kind,title,created_by:uid,pair_key:pairKey}).select('id').single();
   if(rerr){if(pairKey){const {data:existing}=await db.from('promysel_chat_rooms').select('id').eq('pair_key',pairKey).maybeSingle();if(existing){await db.from('promysel_chat_members').update({hidden:false}).eq('room_id',existing.id).eq('user_id',uid);return response({id:existing.id});}}throw rerr;}
   const {error:joinErr}=await db.from('promysel_chat_members').insert(participants.map(x=>({room_id:room.id,user_id:x})));
   if(joinErr){await db.from('promysel_chat_rooms').delete().eq('id',room.id);throw joinErr;}
   return response({id:room.id},201);
  }
  const transcriptRoute=path.match(/^\/rooms\/([0-9a-f-]{36})\/messages\/([0-9a-f-]{36})\/transcribe$/i);
  if(req.method==='POST'&&transcriptRoute){
    const requestedRoom=transcriptRoute[1],messageId=transcriptRoute[2];
    if(!await roomAccess(requestedRoom))return response({detail:'Нет доступа к переписке'},403);
    const {data:message,error:readError}=await db.from('promysel_chat_messages')
      .select('id,kind,attachment_path,mime_type,attachment_name,transcript,deleted_at,bytes')
      .eq('room_id',requestedRoom).eq('id',messageId).maybeSingle();
    if(readError)throw readError;
    if(!message||message.kind!=='voice'||message.deleted_at||!message.attachment_path)
      return response({detail:'Голосовое сообщение не найдено'},404);
    if(message.transcript)return response({text:message.transcript});
    const speechKey=Deno.env.get('OPENAI_API_KEY')??'';
    if(!speechKey)return response({detail:'Распознавание речи ещё не подключено администратором'},503);
    if(Number(message.bytes)>25*1024*1024)return response({detail:'Для распознавания файл должен быть меньше 25 МБ'},413);
    const {data:audio,error:downloadError}=await db.storage.from(B).download(String(message.attachment_path));
    if(downloadError||!audio)return response({detail:'Не удалось получить аудиофайл'},502);
    if(audio.size>25*1024*1024)return response({detail:'Файл слишком большой'},413);
    const filename=str(message.attachment_name)||
       (str(message.mime_type).includes('webm')?'recording.webm':'recording.m4a');
    const form=new FormData();
    form.set('model','gpt-transcribe');
    form.set('file',new File([audio],filename,{type:str(message.mime_type)||'audio/mp4'}));
    let upstream:Response;
    try{
      upstream=await fetch('https://api.openai.com/v1/audio/transcriptions',{
        method:'POST',headers:{Authorization:'Bearer '+speechKey},body:form,
        signal:AbortSignal.timeout(55_000),
      });
    }catch(_){return response({detail:'Сервис распознавания временно недоступен'},504);}
    if(!upstream.ok)return response({detail:'Распознавание временно недоступно'},502);
    const decoded=await upstream.json().catch(()=>({}));
    const transcript=str(decoded?.text).slice(0,12000);
    if(!transcript)return response({detail:'В записи не удалось распознать речь'},422);
    const {error:saveError}=await db.from('promysel_chat_messages')
      .update({transcript}).eq('id',messageId).eq('room_id',requestedRoom);
    if(saveError)throw saveError;
    return response({text:transcript});
  }
  const m=path.match(/^\/rooms\/([0-9a-f-]{36})(?:\/(messages|upload|settings|members|leave))?(?:\/([0-9a-f-]{36}))?$/i);
  if(!m)return response({detail:'Маршрут не найден'},404);
  const roomId=m[1],action=m[2]??'',msgId=m[3];
  const scope=await roomAccess(roomId);if(!scope)return response({detail:'Чат недоступен'},403);
  const {room}=scope;
  if(req.method==='DELETE'&&action===''){
   // Remove only this member's chat from the list; history and other participants are preserved.
   const {error}=await db.from('promysel_chat_members').update({hidden:true,pinned:false})
      .eq('room_id',roomId).eq('user_id',uid);
   if(error)throw error;
   return response({status:'hidden',historyPreserved:true});
  }
  if(req.method==='GET'&&action==='messages'){
   // Polling 'after' only fetches additions and avoids re-signing every historical image.
   const after=str(url.searchParams.get('after')),before=str(url.searchParams.get('before'));
   let q=db.from('promysel_chat_messages').select('*').eq('room_id',roomId)
     .order('created_at',{ascending:!!after}).limit(after?40:60);
   if(after)q=q.gt('created_at',after);
   else if(before)q=q.lt('created_at',before);
   const {data,error}=await q;if(error)throw error;
   const rows=after?(data??[]):(data??[]).reverse();
   const assets=[...new Set(rows.flatMap((v:J)=>{
     if(v.deleted_at)return [];
     if(v.kind==='album'&&Array.isArray(v.attachments))
       return (v.attachments as J[]).map(x=>str(x.path)).filter(Boolean);
     return v.attachment_path?[str(v.attachment_path)]:[];
   }))];
   const signed=new Map<string,string>();
   if(assets.length){
     const {data:links,error:linkError}=await db.storage.from(B).createSignedUrls(assets,1800);
     if(linkError)console.warn('chat signed URLs',linkError.message);
     for(const item of links??[])if(item.signedUrl)signed.set(item.path,item.signedUrl);
   }
   return response({items:rows.map((v:J)=>{
     if(v.deleted_at)return {...v,body:'',attachment_path:null,attachments:[],url:null};
     if(v.kind==='album'&&Array.isArray(v.attachments))
       return {...v,url:null,attachments:(v.attachments as J[]).map(x=>({...x,url:signed.get(str(x.path))??null}))};
     return {...v,url:v.attachment_path?signed.get(str(v.attachment_path))??null:null};
   })});
  }
  if(req.method==='POST'&&action==='upload'){
   const type=str(value.mimeType),size=Number(value.size),name=safeName(str(value.name));
   const kind=str(value.kind);
   const mimeAllowed=kind==='image'?type.startsWith('image/'):(kind==='video'||kind==='video_note')?type.startsWith('video/'):kind==='voice'?type.startsWith('audio/'):kind==='document'?/^(application\/|text\/|image\/)/.test(type):false;
   if(!mimeAllowed||!Number.isFinite(size)||size<1||size>50*1024*1024)return response({detail:'Недопустимый формат или размер файла (до 50 МБ)'},400);
   const filePath=`${roomId}/${uid}/${crypto.randomUUID()}-${name}`;
   const {data,error}=await db.storage.from(B).createSignedUploadUrl(filePath);
   if(error)throw error;return response({path:filePath,uploadUrl:data.signedUrl,token:data.token});
  }
  if(req.method==='POST'&&action==='messages'){
   const kind=str(value.kind)||'text',bodyText=str(value.body),attachment=str(value.path),clientId=str(value.clientId);
   const isAlbum=kind==='album';
   if(!['text','image','video','video_note','voice','document','album'].includes(kind)||bodyText.length>8000)
     return response({detail:'Некорректное сообщение'},400);
   if(kind==='text'&&!bodyText)return response({detail:'Введите сообщение'},400);
   if(!isAlbum&&kind!=='text'&&!attachment.startsWith(roomId+'/'+uid+'/'))
     return response({detail:'Недоступное вложение'},403);
   if(clientId&&!validUuid(clientId))return response({detail:'Некорректный идентификатор'},400);
   const rawFiles=Array.isArray(value.attachments)?value.attachments:[];
   let album:J[]=[];
   if(isAlbum){
     if(rawFiles.length<1||rawFiles.length>10)return response({detail:'Можно прикрепить от 1 до 10 фотографий'},400);
     album=rawFiles.map(x=>({
       path:str(x?.path),name:safeName(str(x?.name)),mimeType:str(x?.mimeType),size:Number(x?.size),
     }));
     const valid=album.every(x=>str(x.path).startsWith(roomId+'/'+uid+'/')&&
       str(x.mimeType).startsWith('image/')&&Number.isFinite(x.size)&&Number(x.size)>0&&Number(x.size)<=50*1024*1024);
     if(!valid||new Set(album.map(x=>str(x.path))).size!==album.length)
       return response({detail:'Вложение не относится к этой переписке'},403);
   }
   if(isAlbum||kind!=='text'){
     const prefix=roomId+'/'+uid;
     const names=isAlbum?album.map(x=>str(x.path).split('/').pop()||''):[attachment.split('/').pop()||''];
     const {data:files,error:findErr}=await db.storage.from(B).list(prefix,{limit:1000});
     if(findErr||!files||!names.every(n=>files.some(f=>f.name===n)))
       return response({detail:'Вложение ещё не загружено. Повторите отправку.'},400);
   }
   const payload={
     room_id:roomId,sender_id:uid,kind,body:bodyText,
     attachment_path:kind==='text'||isAlbum?null:attachment,
     attachments:isAlbum?album:[],
     attachment_name:isAlbum?null:str(value.name).slice(0,160)||null,
     mime_type:isAlbum?null:str(value.mimeType)||null,
     bytes:isAlbum?album.reduce((a,x)=>a+Number(x.size),0):Math.max(0,Number(value.size)||0),
     client_id:clientId||null,
     duration_ms:kind==='voice'||kind==='video_note'?Math.max(0,Math.min(120000,Number(value.durationMs)||0)):null,
     waveform:kind==='voice'&&Array.isArray(value.waveform)?value.waveform.slice(-65)
       .map(Number).filter((v:number)=>Number.isFinite(v)&&v>=0&&v<=1):[],
   };
   const {data,error}=await db.from('promysel_chat_messages').upsert(payload,{
     onConflict:'room_id,sender_id,client_id',ignoreDuplicates:true,
   }).select('id').maybeSingle();
   if(error)throw error;
   await db.from('promysel_chat_members').update({hidden:false}).eq('room_id',roomId);
   await db.from('promysel_chat_rooms').update({updated_at:new Date().toISOString()}).eq('id',roomId);
   return response({id:data?.id??null,status:'sent'});
  }
  if(msgId&&action==='messages'&&['PATCH','DELETE'].includes(req.method)){
   const {data:old}=await db.from('promysel_chat_messages').select('*').eq('id',msgId).eq('room_id',roomId).maybeSingle();
   if(!old||old.sender_id!==uid)return response({detail:'Изменять можно только свои сообщения'},403);
   if(req.method==='PATCH'){
    const newText=str(value.body);if(old.kind!=='text'||old.deleted_at||!newText||newText.length>8000)return response({detail:'Редактирование невозможно'},400);
    const {error}=await db.from('promysel_chat_messages').update({body:newText,edited_at:new Date().toISOString()}).eq('id',msgId);if(error)throw error;
    return response({status:'edited'});
   }
   const {error}=await db.from('promysel_chat_messages').update({body:'',attachments:[],deleted_at:new Date().toISOString()}).eq('id',msgId);if(error)throw error;
   return response({status:'deleted'});
  }
  if(req.method==='PATCH'&&action==='settings'){
   const next:J={};if(typeof value.muted==='boolean')next.muted=value.muted;
   if(typeof value.soundEnabled==='boolean')next.sound_enabled=value.soundEnabled;
   if(typeof value.pinned==='boolean')next.pinned=value.pinned;
   if(value.read===true)next.last_read_at=new Date().toISOString();
   if(Object.keys(next).length){const {error}=await db.from('promysel_chat_members').update(next).eq('room_id',roomId).eq('user_id',uid);if(error)throw error;}
   const avatarPath=str(value.avatarPath);if(avatarPath){
     if(room.kind!=='group'||room.created_by!==uid||!avatarPath.startsWith(`${roomId}/${uid}/`))return response({detail:'Изменить фотографию может только создатель группы'},403);
     const {data:files}=await db.storage.from(B).list(`${roomId}/${uid}`,{search:avatarPath.split('/').pop()||'',limit:10});
     if(!files?.some(f=>f.name===avatarPath.split('/').pop()))return response({detail:'Фотография не загружена'},400);
     const {error}=await db.from('promysel_chat_rooms').update({avatar_path:avatarPath}).eq('id',roomId);if(error)throw error;
   }
   const name=str(value.title);if(name){if(room.kind!=='group'||room.created_by!==uid)return response({detail:'Название меняет только создатель группы'},403);
    const {error}=await db.from('promysel_chat_rooms').update({title:name.slice(0,100)}).eq('id',roomId);if(error)throw error;}
   return response({status:'updated'});
  }
  if(req.method==='POST'&&action==='members'){
   if(room.kind!=='group'||room.created_by!==uid)return response({detail:'Только создатель управляет участниками'},403);
   const target=str(value.userId);if(!validUuid(target))return response({detail:'Неверный участник'},400);
   const {data:allowedPerson}=await db.from('field_memberships').select('user_id').eq('user_id',target).eq('field_id',room.field_id).eq('approved',true).eq('blocked',false).maybeSingle();
   if(!allowedPerson)return response({detail:'Сотрудник недоступен'},403);
   const {error}=await db.from('promysel_chat_members').upsert({room_id:roomId,user_id:target},{onConflict:'room_id,user_id',ignoreDuplicates:true});if(error)throw error;
   return response({status:'added'});
  }
  if(req.method==='DELETE'&&action==='members'){
   if(room.kind!=='group'||room.created_by!==uid)return response({detail:'Только создатель управляет участниками'},403);
   const target=str(value.userId);if(target===uid)return response({detail:'Создателю нужно выйти из группы'},400);
   const {error}=await db.from('promysel_chat_members').delete().eq('room_id',roomId).eq('user_id',target);if(error)throw error;
   return response({status:'removed'});
  }
  if(req.method==='POST'&&action==='leave'){
   if(room.kind!=='group')return response({detail:'Выход доступен только из группы'},400);
   if(room.created_by===uid)return response({detail:'Передайте управление участникам или попросите администратора'},400);
   const {error}=await db.from('promysel_chat_members').delete().eq('room_id',roomId).eq('user_id',uid);if(error)throw error;
   return response({status:'left'});
  }
  return response({detail:'Маршрут не найден'},404);
 }catch(e){console.error('promysel-chat',e instanceof Error?e.message:String(e));return response({detail:'Ошибка сервера чатов'},500);}
});