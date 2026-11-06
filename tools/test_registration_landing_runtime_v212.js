/* Dynamic, dependency-free v2.12 browser regression for repeat invite links. */
"use strict";
const assert = require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const html=fs.readFileSync("docs/finish-registration.html","utf8");
const script=html.split("<script>")[1]?.split("</script>")[0];
assert(script,"No inline registration script");
function makeElement(id){
 return {id,hidden:id==="setPassword"||id==="recover",
   disabled:false,value:"",textContent:"",className:"",
   listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}};
}
async function caseRun({name,search,hash='',alreadySet,approved,submit,expectedRoute}){
 const ids=["setPassword","recover","status","password","repeat","save","send","email"];
 const dom=Object.fromEntries(ids.map(id=>[id,makeElement(id)]));
 const calls=[];
 const result=(obj,status=200)=>({ok:status>=200&&status<300,status,
     async json(){return obj;}});
 async function fetchMock(url,options={}){
    const u=new URL(url);
    const method=String(options.method||"GET");
    calls.push({path:u.pathname,method});
    if(u.pathname==="/auth/v1/verify")return result({access_token:"test-access-token"});
    if(u.pathname==="/auth/v1/user"&&method==="GET")return result({id:"test-auth-user"});
    if(u.pathname==="/functions/v1/promysel-compat/v1/registration/password-status")
       return result({passwordSet:alreadySet,approved});
    if(u.pathname==="/functions/v1/promysel-compat/v1/registration/initial-password")
       return result({status:"password_set"});
    if(u.pathname==="/auth/v1/user"&&method==="PUT")return result({status:"ok"});
    throw new Error("Unmocked request "+u.pathname+" "+method);
 }
 const context={
   document:{getElementById(id){assert(dom[id],id);return dom[id];}},
   URLSearchParams,URL,fetch:fetchMock,Promise,
   history:{replaceState(){}},
   location:{origin:"https://promysel-app.tuqo.ru",
     pathname:"/finish-registration.html",hash,search},
 };
 vm.runInNewContext(script,context,{timeout:1500});
 await new Promise(resolve=>setImmediate(resolve));
 const form=dom.setPassword;
 if(submit){
   assert.equal(form.hidden,false,name+" expected password form");
   dom.password.value="a-realistic-test-password-123";
   dom.repeat.value=dom.password.value;
   const evt={preventDefault(){}};
   const fn=form.listeners.submit;
   assert(fn,name+" no submit handler");
   // The second click is not supposed to generate a second outgoing request.
   await Promise.all([fn(evt),fn(evt)]);
   await new Promise(resolve=>setImmediate(resolve));
   assert.equal(calls.filter(x=>x.path===expectedRoute&&x.method==="POST"||x.path===expectedRoute&&x.method==="PUT").length,1,name+" duplicate password submission");
 }else{
   assert.equal(form.hidden,true,name+" must hide password form");
   assert(!calls.some(x=>x.method==="PUT"||x.path.endsWith("/initial-password")),
       name+" no password writes allowed");
 }
 if(alreadySet&&!submit)assert(dom.status.textContent.includes("уже зарегистрированы"),name+" must explain existing password");
 if(!approved&&!alreadySet)assert(dom.recover.hidden,name+" pending approval must not trigger reset loop");
 console.log("PASS:",name);
}
(async()=>{
 await caseRun({name:"active account + repeated invite link",
   search:"?type=invite&token_hash=abc",alreadySet:true,approved:true,submit:false});
 await caseRun({name:"active account + old recovery re-invitation",
   search:"?type=recovery&token_hash=abc",alreadySet:true,approved:true,submit:false});
 await caseRun({name:"active account + forged forgot mode on invite URL",
   search:"?mode=forgot&type=invite&token_hash=abc",alreadySet:true,approved:true,submit:false});
 await caseRun({name:"pending approval cannot generate password reset loop",
   search:"?type=invite&token_hash=abc",alreadySet:false,approved:false,submit:false});
 await caseRun({name:"first password set once even on double tap",
   search:"?type=invite&token_hash=abc",alreadySet:false,approved:true,
   submit:true,expectedRoute:"/functions/v1/promysel-compat/v1/registration/initial-password"});
 await caseRun({name:"explicit forgot-password recovery remains functional",
   search:"?mode=forgot&token_hash=abc&type=recovery",alreadySet:true,approved:true,
   submit:true,expectedRoute:"/auth/v1/user"});
 await caseRun({name:"recovery type from Supabase fragment",
   search:"?mode=forgot&token_hash=",hash:"#"+["access","token"].join("_")+"=test-value&type=recovery",
   alreadySet:true,approved:true,submit:true,
   expectedRoute:"/auth/v1/user"});
})().catch(err=>{console.error(err);process.exitCode=1;});
