import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {homedir} from 'node:os';
import {join} from 'node:path';
const base=join(homedir(),'.local/share/wechat-assistant');
export default {id:'wechat-reply-helper',name:'Human-confirmed reply drafts',register(api){
  api.registerTool(ctx=>({name:'wechat_reply',
    description:'Prepare a short single-line WeChat reply preview for the authorized owner, or inspect its status. Resolve exact recipient; ambiguous titles are refused. This tool never confirms or sends to other contacts. A native Mac app requires human review of the exact recipient and text. First sender test must target File Transfer with text 微信助手代发测试. Only say sent if status is sent_database_verified.',
    parameters:{type:'object',additionalProperties:false,properties:{action:{type:'string',enum:['prepare','status']},recipient:{type:'string',maxLength:200},text:{type:'string',minLength:1,maxLength:200},code:{type:'string',pattern:'^[A-F0-9]{12}$'}},required:['action']},
    async execute(_id,p){
      if(!['prepare','status'].includes(p.action))throw Error('Only draft preparation/status are available to the model.');
      const c=JSON.parse(readFileSync(join(base,'reader-config.json'),'utf8'));
      const n=x=>String(x||'').toLowerCase(), route=ctx.deliveryContext||{};
      const allowed=(!ctx.requesterSenderId||n(ctx.requesterSenderId)===n(c.owner))&&
        ((n(route.channel)==='openclaw-weixin'&&n(route.to)===n(c.owner)&&n(route.accountId)===n(c.account))||
         n(ctx.sessionKey)===`agent:main:openclaw-weixin:${n(c.account)}:direct:${n(c.owner)}`);
      if(!allowed)throw Error('Owner conversation required.');
      const result=await new Promise((resolve,reject)=>{
        const child=spawn(c.python,[join(base,'reply-bridge/reply_queue.py')],{stdio:['pipe','pipe','pipe']});
        let out='',err='';const timer=setTimeout(()=>{child.kill('SIGTERM');reject(Error('Draft preview timed out; no contact send assumed.'));},70000);
        child.stdout.on('data',d=>{out+=d;if(out.length>100000){child.kill('SIGTERM');reject(Error('Unexpected reply output size.'));}});
        child.stderr.on('data',d=>{err+=d;});child.on('error',e=>{clearTimeout(timer);reject(e);});
        child.on('close',code=>{clearTimeout(timer);try{if(code!==0)throw Error(err||'Reply preparation failed');resolve(JSON.parse(out));}catch(e){reject(e);}});
        child.stdin.end(JSON.stringify(p));
      });
      ctx.assertActive?.();return {content:[{type:'text',text:JSON.stringify(result)}],details:result};
    }
  }),{name:'wechat_reply',optional:true});
}};
