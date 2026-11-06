"use strict";
const fs=require("fs"),vm=require("vm"),assert=require("node:assert/strict");
const source=fs.readFileSync("supabase/functions/promysel-compat/index.ts","utf8");
const start=source.indexOf("function avatarTransportDigest(value:string):string{");
// Execute only the fingerprint helper. Unrelated typed Edge helpers may be
// inserted between this helper and Deno.serve, and are not valid plain JS.
const end=source.indexOf("\n}",start);
assert(start>=0&&end>start,"Supabase avatar fingerprint helper missing");
const compiled=source.slice(start,end+2).replace("value:string):string","value)");
const digest=vm.runInNewContext(compiled+"\navatarTransportDigest;",{}, {timeout:3000});
function independentDigest(text){
 let a=2166136261,b=5381;
 // Match Dart's UTF-16 codeUnits (base64 data is ASCII).
 for(const unit of text.split("").map(c=>c.charCodeAt(0))){
   a=Math.imul(a^unit,16777619)>>>0;
   b=(Math.imul(b,33)+unit)>>>0;
 }
 return text.length+":"+a.toString(16)+":"+b.toString(16);
}
for(const text of ["","__deleted__","SGVsbG8=","/9j/4AAQSkZJRgAB", "AbCd123+/=\u0000", "Промысел"]){
 assert.equal(digest(text),independentDigest(text),"Cross-platform hash mismatch");
}
function delta(remote,local){
 return Object.fromEntries(Object.entries(remote).filter(([id,content])=>
     local[id]!==digest(content)));
}
const data={a:"SGVsbG8=",b:"AQIDBA==",c:"__deleted__"};
const cached={a:digest(data.a),b:digest("older photo"),c:digest("old image")};
assert.deepEqual(delta(data,{}),data,"First device receives every photo");
assert.deepEqual(delta(data,cached),{b:data.b,c:"__deleted__"},"Changed photo and deletion tombstone sent");
assert.deepEqual(delta(data,Object.fromEntries(Object.entries(data).map(([k,v])=>[k,digest(v)]))),{},"No repeated images when cache current");
assert.equal(delta({a:data.a},{a:"tampered"})["a"],data.a,"Unknown hash must resend");
assert(source.includes('if(cacheParam.length>0&&cacheParam.length<=4096)'),"Cache must be bounded");
console.log("PASS avatar hashes: browser/Dart compatibility, changed image, tombstones, first install, cache-hit suppression");
