import {createClient} from "npm:@supabase/supabase-js@2.57.0";
// One-time initial administrator provisioner. Never accepts an arbitrary administrator e-mail.
// Both privileged actions execute only on the server with the service-role key.
const HEAD={"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"POST,OPTIONS","Access-Control-Allow-Headers":"content-type"};
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:HEAD});
Deno.serve(async (req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:HEAD});
 if(req.method!=="POST")return reply({detail:"Method not allowed"},405);
 const raw=await req.text();
 if(raw.length>1024)return reply({detail:"Request is too large"},413);
 let b:Record<string,unknown>;
 try{const p=JSON.parse(raw);if(!p||typeof p!=="object"||Array.isArray(p))throw Error("object");b=p}
 catch{return reply({detail:"Invalid JSON"},400)}
 const setupCode=typeof b.code==="string"?b.code:"";
 const password=typeof b.temporaryPassword==="string"?b.temporaryPassword:"";
 if(setupCode.length<20||setupCode.length>200||password.length<16||password.length>120){
   return reply({detail:"Invalid one-time setup code or password"},400);
 }
 const url=Deno.env.get("SUPABASE_URL")??"",key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??"";
 if(!url||!key)return reply({detail:"Service unavailable"},503);
 const admin=createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
 // Check the server-stored code hash before ever creating an Auth user.
 const {data:allowed,error:verifyError}=await admin.rpc("promysel_bootstrap_code_is_valid",{p_code:setupCode});
 if(verifyError){console.error("admin bootstrap check",verifyError.code);return reply({detail:"Bootstrap check unavailable"},503)}
 if(allowed!==true)return reply({detail:"Invalid or used setup code"},403);
 const email="admin@promysel.local";
 const {data:created,error:createdError}=await admin.auth.admin.createUser({
   email,password,email_confirm:true,user_metadata:{full_name:"Системный администратор"}
 });
 if(createdError||!created.user){
   console.error("admin bootstrap createUser",createdError?.code??"no_user");
   return reply({detail:"Supabase Auth rejected account creation"},409);
 }
 const {error:claimError}=await admin.rpc("promysel_claim_initial_admin",{
   p_actor:created.user.id,p_code:setupCode
 });
 if(claimError){
   await admin.auth.admin.deleteUser(created.user.id);
   console.error("admin bootstrap claim",claimError.code);
   return reply({detail:"Failed to activate administrator; user rolled back"},409);
 }
 return reply({status:"created",email,mustChangePassword:true},201);
});