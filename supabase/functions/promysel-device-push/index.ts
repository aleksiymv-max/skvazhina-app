import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2.75.1";

type Subscription = {endpoint:string,p256dh:string,auth_secret:string,user_id:string,field_id:string};
const url = Deno.env.get("SUPABASE_URL")!;
const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const db = createClient(url, serviceKey, {auth:{persistSession:false}});
const allowedOrigins = new Set(["https://promysel-web.pages.dev","http://localhost:3000","http://localhost:8080"]);
const baseHeaders = {"content-type":"application/json","cache-control":"no-store"};
function response(body:unknown,status=200,origin?:string){
  const h:Record<string,string>={...baseHeaders};
  if(origin&&allowedOrigins.has(origin)){
    h["access-control-allow-origin"]=origin;
    h["vary"]="Origin";
    h["access-control-allow-headers"]="authorization,content-type,apikey";
    h["access-control-allow-methods"]="GET,POST,DELETE,OPTIONS";
  }
  return new Response(status===204?null:JSON.stringify(body),{status,headers:h});
}
function providerAllowed(endpoint:string):boolean{
  try{
    const u=new URL(endpoint);
    if(u.protocol!=="https:"||u.username||u.password||u.port)return false;
    const h=u.hostname.toLowerCase();
    return h==="fcm.googleapis.com" || h.endsWith(".push.apple.com")
      || h.endsWith(".push.services.mozilla.com")
      || h.endsWith(".notify.windows.com");
  }catch(_){return false;}
}
async function signedIn(req:Request,fieldId:string){
  const token=(req.headers.get("authorization")??"").replace(/^Bearer\s+/i,"");
  if(!token)return null;
  const {data:{user},error}=await db.auth.getUser(token);
  if(error||!user)return null;
  const {data:member}=await db.from("field_memberships")
    .select("approved,blocked").eq("user_id",user.id).eq("field_id",fieldId).maybeSingle();
  if(!member?.approved||member.blocked)return null;
  return user.id;
}
async function vapid(){
  const {data,error}=await db.from("promysel_push_keys")
   .select("public_key,private_key").eq("key_name","vapid-main").maybeSingle();
  if(error||!data)throw new Error("Push keys unavailable");
  return data as {public_key:string,private_key:string};
}
Deno.serve(async(req:Request)=>{
  const origin=req.headers.get("origin")??undefined;
  if(req.method==="OPTIONS")return response(null,204,origin);
  const pathname=new URL(req.url).pathname;
  const route=pathname.replace(/^\/promysel-device-push/,"")||"/";
  try{
    if(route==="/health"&&req.method==="GET")
      return response({status:"ok",service:"promysel-device-push"},200,origin);
    if(route==="/public-key"&&req.method==="GET")
      return response({publicKey:(await vapid()).public_key},200,origin);
    if(route==="/subscribe"&&req.method==="POST"){
      const body=await req.json().catch(()=>({}));
      const fieldId=String(body?.fieldId??"");
      if(!/^field-[0-9a-z-]{1,90}$/i.test(fieldId))return response({detail:"Неверное месторождение"},400,origin);
      const userId=await signedIn(req,fieldId);
      if(!userId)return response({detail:"Необходим вход и допуск к месторождению"},403,origin);
      const subscription=body?.subscription;
      const endpoint=String(subscription?.endpoint??"");
      const p256dh=String(subscription?.keys?.p256dh??"");
      const auth=String(subscription?.keys?.auth??"");
      if(endpoint.length>4096||!providerAllowed(endpoint)||
         !/^[A-Za-z0-9_-]{70,250}$/.test(p256dh)||
         !/^[A-Za-z0-9_-]{15,100}$/.test(auth))
        return response({detail:"Некорректная подписка устройства"},400,origin);
      const {data:old}=await db.from("promysel_push_subscriptions")
        .select("user_id").eq("endpoint",endpoint).maybeSingle();
      if(old&&old.user_id!==userId)return response({detail:"Устройство привязано к другому сотруднику"},409,origin);
      const {error}=await db.from("promysel_push_subscriptions").upsert({
         endpoint,user_id:userId,field_id:fieldId,p256dh,auth_secret:auth,
         enabled:true,updated_at:new Date().toISOString()
      },{onConflict:"endpoint"});
      if(error)throw error;
      return response({status:"subscribed"},201,origin);
    }
    if(route==="/unsubscribe"&&req.method==="POST"){
      const body=await req.json().catch(()=>({}));
      const fieldId=String(body?.fieldId??"");
      const userId=await signedIn(req,fieldId);
      if(!userId)return response({detail:"Нет доступа"},403,origin);
      const endpoint=String(body?.endpoint??"");
      if(endpoint.length>4096)return response({detail:"Неверный адрес"},400,origin);
      await db.from("promysel_push_subscriptions").delete()
       .eq("field_id",fieldId).eq("user_id",userId).eq("endpoint",endpoint);
      return response({status:"unsubscribed"},200,origin);
    }
    if((route==="/deliver"||route==="/dispatch")&&req.method==="POST"){
      const body=await req.json().catch(()=>({}));
      const fieldId=String(body?.fieldId??"");
      if(!/^field-[0-9a-z-]{1,90}$/i.test(fieldId))return response({detail:"Неверное месторождение"},400,origin);
      let dispatchEventId=0;
      if(route==="/dispatch"){
        dispatchEventId=Number(body?.eventId??0);
        const supplied=String(body?.signature??"").toLowerCase();
        if(!Number.isSafeInteger(dispatchEventId)||dispatchEventId<1||!/^[0-9a-f]{64}$/.test(supplied)){
          return response({detail:"Недопустимая подпись"},403,origin);
        }
        const {data:secret,error:secretError}=await db.from("promysel_push_keys")
          .select("private_key").eq("key_name","push-webhook-hmac").maybeSingle();
        if(secretError||!secret?.private_key)return response({detail:"Webhook unavailable"},503,origin);
        const keyBytes=Uint8Array.from(secret.private_key.match(/.{2}/g)!.map((s:string)=>parseInt(s,16)));
        const hmacKey=await crypto.subtle.importKey("raw",keyBytes,{name:"HMAC",hash:"SHA-256"},false,["sign"]);
        const input=new TextEncoder().encode(String(dispatchEventId)+"|"+fieldId);
        const sig=new Uint8Array(await crypto.subtle.sign("HMAC",hmacKey,input));
        let mismatch=0;
        for(let i=0;i<sig.length;i++) mismatch |= sig[i]^parseInt(supplied.slice(i*2,i*2+2),16);
        if(mismatch!==0)return response({detail:"Нет доступа"},403,origin);
      }else{
        const userId=await signedIn(req,fieldId);
        if(!userId)return response({detail:"Нет доступа"},403,origin);
      }
      const keys=await vapid();
      webpush.setVapidDetails("https://promysel-web.pages.dev",
        keys.public_key,keys.private_key);
      let query=db.from("promysel_push_events")
        .select("id,user_id,event_key,title,body,task_id,send_attempts")
        .eq("field_id",fieldId).is("sent_at",null).lt("send_attempts",5)
        .gte("created_at",new Date(Date.now()-7*86400000).toISOString());
      if(dispatchEventId)query=query.eq("id",dispatchEventId);
      const {data:pending,error}=await query.order("id",{ascending:true})
        .limit(dispatchEventId?1:25);
      if(error)throw error;
      let pushed=0;
      for(const event of pending??[]){
        const {data:devices}=await db.from("promysel_push_subscriptions")
          .select("endpoint,p256dh,auth_secret,user_id,field_id")
          .eq("field_id",fieldId).eq("user_id",event.user_id)
          .eq("enabled",true).limit(8);
        if(!devices?.length)continue;
        const payload=JSON.stringify({
          title:event.title,body:event.body,url:"/tasks",tag:"promysel-"+event.event_key,
          taskId:event.task_id,badgeCount:Math.min(99,(pending??[]).filter((e)=>e.user_id===event.user_id).length)
        });
        let anySent=false;
        for(const d of devices as Subscription[]){
          try{
            await webpush.sendNotification({endpoint:d.endpoint,keys:{p256dh:d.p256dh,auth:d.auth_secret}},payload,
              {TTL:86400,urgency:"normal",topic:"promysel-tasks"});
            anySent=true;
          }catch(err){
            const status=Number((err as {statusCode?:number})?.statusCode??0);
            if(status===404||status===410)
              await db.from("promysel_push_subscriptions").delete().eq("endpoint",d.endpoint);
          }
        }
        if(anySent){
          pushed++;
          await db.from("promysel_push_events").update({
            sent_at:new Date().toISOString(),send_attempts:event.send_attempts+1
          }).eq("id",event.id).is("sent_at",null);
        }else await db.from("promysel_push_events")
          .update({send_attempts:event.send_attempts+1}).eq("id",event.id).is("sent_at",null);
      }
      return response({status:"ok",sent:pushed},200,origin);
    }
    return response({detail:"Маршрут не найден"},404,origin);
  }catch(err){
    console.error("promysel push",err instanceof Error?err.message:String(err));
    return response({detail:"Сервис уведомлений временно недоступен"},503,origin);
  }
});
