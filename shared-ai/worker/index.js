import { GUIDANCE, validSuggestion, preferences } from './protocol.js';
import { METHODS } from './methods.js';

const MAX_BODY=40000, ROUTE_OUTPUT=900, EDIT_OUTPUT=3500;
class PublicError extends Error { constructor(code,status=400){super(code);this.code=code;this.status=status;} }
const fail=(code,status)=>{throw new PublicError(code,status);};
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export async function digest(text){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');}
function randomToken(){return 'sa1_'+Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');}
async function readBody(request){
 if (!request.headers.get('content-type')?.startsWith('application/json')) fail('json_required',415);
 const reader=request.body?.getReader(); if(!reader)fail('body_required');
 let size=0,chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX_BODY){await reader.cancel();fail('body_too_large',413);}chunks.push(value);}
 const all=new Uint8Array(size);let at=0;for(const c of chunks){all.set(c,at);at+=c.byteLength;}
 try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(all));}catch{fail('invalid_json');}
}
function integer(value,min=0,max=100000000000){if(!Number.isSafeInteger(value)||value<min||value>max)fail('invalid_limit');return value;}
async function authenticate(request,env){
 const token=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';
 if(!/^sa1_[a-f0-9]{64}$/.test(token))fail('invalid_invite',401);
 const item=await env.DB.prepare('SELECT * FROM invites WHERE token_hash=?').bind(await digest(token)).first();
 if(!item||item.revoked||item.expires<=Date.now())fail('invite_expired_or_revoked',401);
 return item;
}
async function deviceOf(request){const device=request.headers.get('X-Snapper-Device')||'';if(!/^[a-f0-9-]{36}$/i.test(device))fail('device_required',401);return digest(device);}
async function authorizeDevice(request,env){const item=await authenticate(request,env);if(item.device_hash!==await deviceOf(request))fail('invite_device_mismatch',401);return item;}
function configured(env){try{const u=new URL(env.UPSTREAM_BASE_URL);return u.protocol==='https:'&&!!env.UPSTREAM_API_KEY&&!!env.UPSTREAM_MODEL&&!u.username&&!u.password&&!u.search&&!u.hash;}catch{return false;}}
async function masterKey(env){
 if(!/^[a-f0-9]{64}$/.test(env.PROVIDER_MASTER_KEY||''))fail('provider_not_configured',503);
 return crypto.subtle.importKey('raw',Uint8Array.from(env.PROVIDER_MASTER_KEY.match(/../g),s=>parseInt(s,16)),'AES-GCM',false,['encrypt','decrypt']);
}
async function providerRuntime(env){
 if(env.UPSTREAM_API_KEY)return env;
 try{
  const row=await env.DB.prepare('SELECT * FROM provider WHERE id=1').first();if(!row)return env;
  const sealed=JSON.parse(row.sealed),key=await masterKey(env);
  const data=await crypto.subtle.decrypt({name:'AES-GCM',iv:new Uint8Array(sealed.iv)},key,new Uint8Array(sealed.cipher));
  return {...env,UPSTREAM_BASE_URL:row.base_url,UPSTREAM_MODEL:row.model,UPSTREAM_API_KEY:new TextDecoder().decode(data)};
 }catch{return env;}
}
async function status(env,item){
 const p=await env.DB.prepare('SELECT * FROM policy WHERE id=1').first()||{enabled:0,budget:0,used:0};
 return {mode:env.BILLING_ENABLED==='true'&&p.enabled===1?'enabled':'billing_disabled',provider_configured:configured(env),label:item.label,expires:item.expires,
  budget_micros_cny:item.budget,used_micros_cny:item.used,remaining_requests:Math.max(0,item.request_limit-item.requests),daily_limit:item.daily_limit,
  global_remaining_micros_cny:Math.max(0,p.budget-p.used)};
}
async function activate(request,env){
 const input=await readBody(request);if(typeof input.code!=='string')fail('invalid_invite',401);
 const fake=new Request(request.url,{headers:{Authorization:'Bearer '+input.code}});const item=await authenticate(fake,env);
 const hash=await deviceOf(request);
 const claimed=await env.DB.prepare('UPDATE invites SET device_hash=? WHERE id=? AND (device_hash IS NULL OR device_hash=?) RETURNING id').bind(hash,item.id,hash).first();
 if(!claimed)fail('invite_already_bound',409);
 return json(await status(env,{...item,device_hash:hash}));
}
const cost=(tokens,price)=>Math.ceil(tokens*price/1000000);
function prices(env){
 const input=Number(env.INPUT_MICROS_CNY_PER_MILLION),output=Number(env.OUTPUT_MICROS_CNY_PER_MILLION);
 if(!Number.isSafeInteger(input)||input<=0||input>1000000000||!Number.isSafeInteger(output)||output<=0||output>1000000000)fail('pricing_not_configured',503);
 return {input,output};
}
function prompts(original,prefs,plan){
 if(!plan)return {system:'按原文语义理解用户要完成什么，选择0—4项真正有帮助的方法。短而开放不等于只需同义改写。本次明确要求高于历史偏好。不执行原请求。只返回JSON: intent, selections:[{id,reason}]。',data:{original,preferences:prefs,candidates:METHODS.map(({id,title})=>({id,title}))}};
 return {system:GUIDANCE,data:{original,intent:plan.intent,preferences:prefs,methods:plan.selections.map(s=>({...METHODS.find(m=>m.id===s.id),reason:s.reason}))}};
}
export async function upstream(env,prompt,max,fetcher=(...args)=>globalThis.fetch(...args)){
 const response=await fetcher(env.UPSTREAM_BASE_URL.replace(/\/$/,'')+'/chat/completions',{
  method:'POST',redirect:'manual',headers:{'Content-Type':'application/json',Authorization:'Bearer '+env.UPSTREAM_API_KEY},
  body:JSON.stringify({model:env.UPSTREAM_MODEL,messages:[{role:'system',content:prompt.system},{role:'user',content:JSON.stringify(prompt.data)}],max_completion_tokens:max,response_format:{type:'json_object'},stream:false}),signal:AbortSignal.timeout(90000)});
 if(!response.ok)fail('upstream_unavailable',502);
 const data=await response.json();const content=data.choices?.[0]?.message?.content;
 if(typeof content!=='string'||content.length>50000)fail('invalid_upstream_result',502);
 const input=data.usage?.prompt_tokens,output=data.usage?.completion_tokens;
 if(!Number.isSafeInteger(input)||input<0||!Number.isSafeInteger(output)||output<0||output>max)fail('usage_unavailable',502);
 let value;try{value=JSON.parse(content);}catch{fail('invalid_upstream_result',502);}
 return {value,input,output};
}
async function refine(request,env,fetcher){
 const item=await authorizeDevice(request,env);
 // Independent environment gate: no client, invitation, policy update, mock
 // request or administrator API can enable billing in this release deployment.
 if(env.BILLING_ENABLED!=='true')fail('billing_disabled',403);
 const policy=await env.DB.prepare('SELECT * FROM policy WHERE id=1').first();if(!policy?.enabled)fail('billing_disabled',403);
 if(!configured(env))fail('provider_not_configured',503);
 const price=prices(env),input=await readBody(request);
 if(typeof input.original!=='string'||!input.original.trim()||new TextEncoder().encode(input.original).length>24000)fail('invalid_selection');
 if(typeof input.request_id!=='string'||!/^[a-f0-9-]{36}$/i.test(input.request_id))fail('invalid_request_id');
 const prefs=preferences(input.preferences,METHODS),route=prompts(input.original,prefs,null);
 // Reserve against the largest possible selected method payload. UTF-8 bytes
 // plus a protocol margin deliberately overestimate input tokens. Model and
 // verified prices are owner-controlled, never accepted from the client.
 const biggest={intent:'测'.repeat(600),selections:METHODS.slice().sort((a,b)=>new TextEncoder().encode(JSON.stringify(b)).length-new TextEncoder().encode(JSON.stringify(a)).length).slice(0,4).map(m=>({id:m.id,reason:'测'.repeat(800)}))};
 const inputBound=new TextEncoder().encode(JSON.stringify(route)+JSON.stringify(prompts(input.original,prefs,biggest))).length+4096;
 const outputBound=ROUTE_OUTPUT+EDIT_OUTPUT,reserve=cost(inputBound,price.input)+cost(outputBound,price.output);
 const id=item.id+':'+input.request_id,hash=await digest(JSON.stringify({original:input.original,prefs}));
 const existing=await env.DB.prepare('SELECT input_hash FROM runs WHERE id=?').bind(id).first();
 if(existing)fail(existing.input_hash===hash?'request_already_started':'request_id_conflict',409);
 try{await env.DB.prepare('INSERT INTO runs(id,invite_id,input_hash,created,day,state,reserved) VALUES(?,?,?,?,?,\'pending\',?)').bind(id,item.id,hash,Date.now(),new Date().toISOString().slice(0,10),reserve).run();}
 catch{fail('quota_or_request_limit',429);}
 try{
  const first=await upstream(env,route,ROUTE_OUTPUT,fetcher),plan=first.value;
  if(typeof plan.intent!=='string'||!plan.intent||plan.intent.length>600||!Array.isArray(plan.selections)||plan.selections.length>4||new Set(plan.selections.map(s=>s.id)).size!==plan.selections.length||plan.selections.some(s=>!METHODS.some(m=>m.id===s.id)||typeof s.reason!=='string'||s.reason.length>800))fail('invalid_skill_plan',502);
  // Revocation between the two model calls stops the second call. The full
  // reservation remains until reconciliation; network errors never refund it.
  const current=await env.DB.prepare('SELECT revoked,expires FROM invites WHERE id=?').bind(item.id).first();
  if(current.revoked||current.expires<=Date.now())fail('invite_expired_or_revoked',401);
  const livePolicy=await env.DB.prepare('SELECT enabled FROM policy WHERE id=1').first();
  if(!livePolicy?.enabled||env.BILLING_ENABLED!=='true')fail('billing_disabled',403);
  const second=await upstream(env,prompts(input.original,prefs,plan),EDIT_OUTPUT,fetcher);
  if(!validSuggestion(second.value))fail('invalid_upstream_result',502);
  const tokensIn=first.input+second.input,tokensOut=first.output+second.output,charged=cost(tokensIn,price.input)+cost(tokensOut,price.output);
  if(tokensIn>inputBound||tokensOut>outputBound||charged>reserve)fail('usage_exceeds_reservation',502);
  await env.DB.prepare("UPDATE runs SET state='done',charged=?,input_tokens=?,output_tokens=? WHERE id=? AND state='pending'").bind(charged,tokensIn,tokensOut,id).run();
  return json({suggestion:second.value,methods:plan.selections.map(s=>({title:METHODS.find(m=>m.id===s.id).title,reason:s.reason})),usage:{input_tokens:tokensIn,output_tokens:tokensOut,charged_micros_cny:charged}});
 }catch(e){
  // Never release funds when a provider might already have billed the call.
  await env.DB.prepare("UPDATE runs SET state='uncertain',charged=reserved WHERE id=? AND state='pending'").bind(id).run();throw e;
 }
}
async function administrator(request,env,path,fetcher){
 const supplied=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';
 if(!env.ADMIN_TOKEN||await digest(supplied)!==await digest(env.ADMIN_TOKEN))fail('unauthorized',401);
 if(request.method==='GET')return json({billing_enabled:env.BILLING_ENABLED==='true',provider_configured:configured(env),policy:await env.DB.prepare('SELECT * FROM policy WHERE id=1').first(),invites:(await env.DB.prepare('SELECT id,label,expires,revoked,budget,used,request_limit,requests,daily_limit FROM invites ORDER BY expires DESC LIMIT 100').all()).results});
 const v=await readBody(request);
 if(path==='/admin/provider-check'){
  if(!configured(env))fail('provider_not_configured',503);
  try {
  const r=await fetcher(env.UPSTREAM_BASE_URL.replace(/\/$/,'')+'/models',{headers:{Authorization:'Bearer '+env.UPSTREAM_API_KEY},redirect:'manual',signal:AbortSignal.timeout(15000)});
  if(!r.ok)fail('upstream_unavailable',502);
  const catalog=await r.json();if(!Array.isArray(catalog.data))fail('invalid_upstream_result',502);
  return json({connected:true,model_available:catalog.data.some(m=>m.id===env.UPSTREAM_MODEL),model_count:catalog.data.length,billing_enabled:env.BILLING_ENABLED==='true',generation_requests:0});
  }catch(e){if(e instanceof PublicError)throw e;let detail=String(e?.message||'connection failed');for(const secret of [env.UPSTREAM_API_KEY,env.ADMIN_TOKEN,env.PROVIDER_MASTER_KEY])if(secret)detail=detail.split(secret).join('[redacted]');return json({error:'provider_connection_unavailable',kind:String(e?.name||'Error'),detail:detail.slice(0,200)},503);}
 }
 if(path==='/admin/initialize'){await env.DB.prepare('INSERT OR IGNORE INTO policy(id) VALUES(1)').run();return json({initialized:true,billing_enabled:false});}
 if(path==='/admin/provider'){
  // Owner-only enrollment over HTTPS. The API key never returns to a client;
  // D1 keeps ciphertext, with a separate runtime secret protecting it at rest.
  if(v.base_url!=='https://tideverse.cn/v1'||typeof v.model!=='string'||!/^[a-zA-Z0-9._/-]{1,100}$/.test(v.model)||typeof v.api_key!=='string'||v.api_key.length<16||v.api_key.length>600)fail('invalid_provider');
  const key=await masterKey(env),iv=crypto.getRandomValues(new Uint8Array(12));
  const cipher=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,new TextEncoder().encode(v.api_key));
  await env.DB.prepare('INSERT INTO provider(id,base_url,model,sealed) VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET base_url=excluded.base_url,model=excluded.model,sealed=excluded.sealed').bind(v.base_url,v.model,JSON.stringify({iv:Array.from(iv),cipher:Array.from(new Uint8Array(cipher))})).run();
  return json({provider_configured:true,billing_enabled:env.BILLING_ENABLED==='true'});
 }
 if(path==='/admin/invites'){
  if(typeof v.label!=='string'||!v.label.trim()||v.label.length>80)fail('invalid_label');
  const expires=integer(v.expires,Date.now()+60000,Date.now()+90*86400000),budget=integer(v.budget??0),limit=integer(v.request_limit??0,0,10000),daily=integer(v.daily_limit??0,0,1000);
  const code=randomToken(),id=crypto.randomUUID();await env.DB.prepare('INSERT INTO invites(id,token_hash,label,expires,budget,request_limit,daily_limit) VALUES(?,?,?,?,?,?,?)').bind(id,await digest(code),v.label,expires,budget,limit,daily).run();return json({id,code,billing_enabled:false},201);
 }
 if(path==='/admin/revoke') {await env.DB.prepare('UPDATE invites SET revoked=1 WHERE id=?').bind(String(v.id)).run();return json({revoked:true});}
 if(path==='/admin/limits'){
  const budget=integer(v.budget),limit=integer(v.request_limit,0,100000);
  if(v.id){await env.DB.prepare('UPDATE invites SET budget=?,request_limit=?,daily_limit=? WHERE id=?').bind(budget,limit,integer(v.daily_limit,0,1000),String(v.id)).run();}
  else await env.DB.prepare('UPDATE policy SET budget=?,request_limit=? WHERE id=1').bind(budget,limit).run();
  return json({updated:true,billing_enabled:env.BILLING_ENABLED==='true'});
 }
 fail('not_found',404);
}
export function createWorker(fetcher=(...args)=>globalThis.fetch(...args)){return {async fetch(request,env){
 try{
  const path=new URL(request.url).pathname;
  if(request.method==='GET'&&path==='/health')return json({service:'snapper-assist-shared-ai',version:'0.10.0',billing_enabled:env.BILLING_ENABLED==='true'});
  if(request.method==='GET'&&path==='/')return new Response(PAGE,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"}});
  if(!env.DB)fail('storage_not_ready',503);
  env=await providerRuntime(env);
  if(path.startsWith('/admin/')&&['GET','POST'].includes(request.method))return await administrator(request,env,path,fetcher);
  if(request.method==='POST'&&path==='/api/activate')return await activate(request,env);
  if(request.method==='GET'&&path==='/api/status')return json(await status(env,await authorizeDevice(request,env)));
  if(request.method==='POST'&&path==='/api/refine')return await refine(request,env,fetcher);
  fail('not_found',404);
 }catch(e){return json({error:e instanceof PublicError?e.code:'service_unavailable'},e instanceof PublicError?e.status:503);}
}};}
export default createWorker();
const PAGE=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Snapper Assist · 共享 AI</title><style>body{margin:0;background:#f5f5f7;color:#1d1d1f;font:16px -apple-system,BlinkMacSystemFont,sans-serif}main{max-width:700px;margin:8vh auto;padding:24px}h1{font-size:36px;letter-spacing:-1.3px}p{line-height:1.75;color:#626269}section{background:#fff;border:1px solid #e5e5ea;border-radius:20px;padding:24px;margin-top:20px}label{display:block;margin:16px 0 6px}input,button{font:inherit;border:1px solid #d2d2d7;border-radius:9px;padding:12px;box-sizing:border-box}input{width:100%}button{background:#0071e3;color:#fff;cursor:pointer;margin-top:14px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px ui-monospace,monospace}small{font-size:14px;color:#626269}</style><main><small>SNAPPER ASSIST</small><h1>共享方法，保留你的思考。</h1><p>朋友在助手内输入邀请码即可连接。模型密钥只保存在服务端。当前内测的真实模型扣费保持关闭，本地草稿仍可使用。</p><section><h2>维护者控制台</h2><label for="token">管理凭证</label><input id="token" type="password" autocomplete="off"><button id="load">查看用量与邀请码</button><pre id="state"></pre><label for="label">新邀请码备注</label><input id="label" placeholder="例如：朋友 A"><button id="create">创建 7 天邀请码（额度为零）</button><pre id="result"></pre><small>新邀请码只显示一次。当前控制台不会开启真实扣费。</small></section></main><script>async function call(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+document.querySelector('#token').value,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error);return data;}document.querySelector('#load').onclick=async()=>{try{document.querySelector('#state').textContent=JSON.stringify(await call('/admin/status'),null,2);}catch(e){document.querySelector('#state').textContent=e.message;}};document.querySelector('#create').onclick=async()=>{try{document.querySelector('#result').textContent=JSON.stringify(await call('/admin/invites',{label:document.querySelector('#label').value,expires:Date.now()+7*86400000,budget:0,request_limit:0,daily_limit:0}),null,2);}catch(e){document.querySelector('#result').textContent=e.message;}};</script></html>`;
