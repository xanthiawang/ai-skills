#!/usr/bin/env python3
"""Owner preview queue. Final sending is authorized only by a local human dialog."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import unicodedata

BASE=Path.home()/'.local/share/wechat-assistant'
sys.path.insert(0,str(BASE/'mac-reader-source'))
from sqlcipher_probe import DB,load_key
from wechat_db import Reader, literal


def cfg():return json.loads((BASE/'reader-config.json').read_text())
def snapshot_or_empty(reader,recipient):
    try:return reader.snapshot(recipient)
    except RuntimeError as error:
        if str(error)=='conversation_has_no_local_message_table':return {'cursor':{},'salts':{}}
        raise
def norm(text):return ''.join(unicodedata.normalize('NFKC',text).split())
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def binding(c):return digest({k:c[k] for k in ['owner','account','self_id','db_root','key_file']})
def save(path,data):
    from tempfile import mkstemp
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,tmp=mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def oc(c,args):
    p=subprocess.run([c['node'],c['cli'],'--profile',c['profile'],*args],capture_output=True,text=True,timeout=120)
    if p.returncode:raise RuntimeError('Owner-channel command failed; no preview assumed sent')
    for i,ch in enumerate(p.stdout):
        if ch=='{':
            try:return json.loads(p.stdout[i:])
            except json.JSONDecodeError:pass
    raise RuntimeError('Invalid owner-channel result')


def get_request(code,require_fresh=True):
    if not re.fullmatch('[A-F0-9]{12}',code):raise RuntimeError('Invalid request code')
    path=BASE/'reply-requests'/(code+'.json');r=json.loads(path.read_text());c=cfg()
    if r['binding']!=binding(c) or digest(r['payload'])!=r['payload_hash']:raise RuntimeError('Owner or immutable draft changed')
    if require_fresh and r['expires_at']<time.time():raise RuntimeError('Draft expired; prepare a new preview')
    return path,r,c

def validate_source(payload,c):
    root=Path(c['db_root']);reader=Reader(root,c['key_file'])
    now=snapshot_or_empty(reader,payload['recipient_id'])
    baseline=payload['baseline']
    for name,salt in baseline['salts'].items():
        if now['salts'].get(name)!=salt or now['cursor'].get(name,-1)<baseline['cursor'].get(name,0):
            raise RuntimeError('Database replaced or cursor regressed; prepare a new preview')
    p=root/'contact/contact.db'
    with DB(p,load_key(c['key_file'],p)) as db:
        contacts=db.query('SELECT username,nick_name,remark,alias FROM contact')
    contact=[x for x in contacts if x['username']==payload['recipient_id']]
    if len(contact)!=1 or (contact[0]['remark'] or contact[0]['nick_name'] or contact[0]['username'])!=payload['recipient_label']:
        raise RuntimeError('Contact changed; prepare a new preview')
    collisions={x['username'] for x in contacts if any(norm(v or '')==norm(payload['recipient_label']) for v in [x['remark'],x['nick_name'],x['alias'],x['username']])}
    if collisions!={payload['recipient_id']}:raise RuntimeError('Recipient title became ambiguous')


def prepare(value):
    c=cfg();recipient=value.get('recipient','');text=value.get('text','')
    if not isinstance(text,str) or not 1<=len(text)<=200 or any(unicodedata.category(ch)=='Cc' or '\u202a'<=ch<='\u202e' or '\u2066'<=ch<='\u2069' for ch in text):
        raise RuntimeError('Initial sender accepts one single-line message of 1..200 characters')
    if not isinstance(recipient,str) or not 1<=len(recipient)<=200:raise RuntimeError('Explicit recipient required')
    root=Path(c['db_root']);p=root/'contact/contact.db'
    with DB(p,load_key(c['key_file'],p)) as db:
        contacts=db.query('SELECT username,nick_name,remark,alias FROM contact')
    matches=[r for r in contacts if recipient in (r['username'],r['nick_name'],r['remark'],r['alias'])]
    if len(matches)!=1:raise RuntimeError('Recipient missing or ambiguous; provide exact contact identity')
    contact=matches[0];label=contact['remark'] or contact['nick_name'] or contact['username']
    if any(unicodedata.category(ch)=='Cc' or '\u202a'<=ch<='\u202e' or '\u2066'<=ch<='\u2069' for ch in label):raise RuntimeError('Unsupported control characters in recipient title')
    collisions={r['username'] for r in contacts if any(norm(x or '')==norm(label) for x in [r['remark'],r['nick_name'],r['alias'],r['username']])}
    if collisions!={contact['username']}:raise RuntimeError('Duplicate or visually similar chat title; no automatic sending')
    reader=Reader(root,c['key_file']);baseline=snapshot_or_empty(reader,contact['username'])
    code=secrets.token_hex(6).upper()
    payload={'recipient_id':contact['username'],'recipient_label':label,'recipient_alias':contact['alias'] or '',
             'text':text,'db_root':str(root),'baseline':baseline}
    request={'code':code,'binding':binding(c),'payload':payload,'payload_json':json.dumps(payload,sort_keys=True,ensure_ascii=False),'payload_hash':digest(payload),'created_at':time.time(),
             'expires_at':time.time()+1200,'status':'preview_prepared'}
    path=BASE/'reply-requests'/(code+'.json');save(path,request)
    preview=f'待发草稿 {code}\n收件人：{label}\n联系人ID：{contact["username"]}\n微信号：{contact["alias"] or "未提供"}\n\n{text}\n\n尚未发送。请在Mac核对当前聊天与完整正文，确认窗点发送后才代发。'
    sent=oc(c,['message','send','--channel','openclaw-weixin','--account',c['account'],'--target',c['owner'],'--message',preview,'--json'])
    if sent.get('payload',{}).get('deliveryStatus')!='sent' or sent.get('dryRun'):raise RuntimeError('Exact preview delivery not confirmed')
    request['status']='waiting_mac_confirmation';save(path,request)
    sender=c.get('mac_sender',{})
    if sender.get('permissions_confirmed') and sender.get('composer_top'):
        subprocess.Popen(['/usr/bin/open','-n',str(BASE/'ReplyBridge.app'),'--args','--request',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return {'code':code,'recipient':label,'text':text,'status':request['status'],'sending_enabled':bool(sender.get('enabled')),
            'requires_mac_setup':not bool(sender.get('permissions_confirmed') and sender.get('composer_top'))}


def verify_sent(code):
    path,r,c=get_request(code,require_fresh=False);payload=r['payload'];reader=Reader(Path(c['db_root']),c['key_file'])
    if r['status']!='ui_sent_pending_db':raise RuntimeError('Native human-confirmed sender has not reported this request')
    matches=[]
    for _ in range(16):
        validate_source(payload,c)
        now=snapshot_or_empty(reader,payload['recipient_id'])
        for name,salt in r['send_baseline']['salts'].items():
            if now['salts'].get(name)!=salt or now['cursor'].get(name,-1)<r['send_baseline']['cursor'].get(name,0):
                raise RuntimeError('Send verification database changed; never retry')
        try:rows=reader.read(payload['recipient_id'],limit=200,after=r['send_baseline']['cursor'],self_id=c['self_id'])
        except RuntimeError as error:
            if str(error)!='conversation_has_no_local_message_table':raise
            rows=[]
        matches=[x for x in rows if x['from_self'] and x['text']==payload['text'] and int(x['server_id'] or 0)!=0]
        if len(matches)==1:break
        if len(matches)>1:raise RuntimeError('Multiple matching rows; send cannot be uniquely verified')
        time.sleep(.5)
    if len(matches)!=1:raise RuntimeError('No unique new self-sent message with server ID; never retry automatically')
    r['status']='sent_database_verified';r['verified_at']=time.time();r['server_id']=matches[0]['server_id'];save(path,r)
    if payload['recipient_id']=='filehelper' and payload['text']=='微信助手代发测试':
        c['mac_sender']['enabled']=True;save(BASE/'reader-config.json',c)
    oc(c,['message','send','--channel','openclaw-weixin','--account',c['account'],'--target',c['owner'],
          '--message',f'已代发并在本机微信记录核对：{payload["recipient_label"]}\n{payload["text"]}\n此结果不代表对方已读。','--json'])
    return {'status':r['status'],'code':code,'recipient':payload['recipient_label'],'read_receipt':False}


def main():
    os.umask(0o077);value=json.load(sys.stdin);action=value.get('action')
    with (BASE/'reply-queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if action=='prepare':result=prepare(value)
        elif action=='status':
            _,r,_=get_request(value['code'],require_fresh=False);result={'code':r['code'],'status':r['status'],'recipient':r['payload']['recipient_label']}
        elif action in ('validate','claim','ui-sent','failed'):
            path,r,c=get_request(value['code'],require_fresh=action in ('validate','claim'))
            if action=='validate':
                if r['status']!='waiting_mac_confirmation':raise RuntimeError('Request is not awaiting human review')
                result=r
            elif action=='claim':
                if r['status']!='waiting_mac_confirmation':raise RuntimeError('Approval already used; no automatic retry')
                validate_source(r['payload'],c)
                r['send_baseline']=snapshot_or_empty(Reader(Path(c['db_root']),c['key_file']),r['payload']['recipient_id'])
                r['status']='pending_before_typing';save(path,r);result={'claimed':True}
            elif action=='ui-sent':
                if r['status']!='pending_before_typing':raise RuntimeError('Invalid sender state')
                r['status']='ui_sent_pending_db';save(path,r);result={'status':r['status']}
            else:
                r['failure_reason']=str(value.get('failure_reason',''))[:180]
                r['status']='blocked_or_uncertain';save(path,r);result={'status':r['status']}
        elif action=='verify':result=verify_sent(value['code'])
        else:raise RuntimeError('Unsupported bounded queue action')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'error':str(error)},ensure_ascii=False),file=sys.stderr);sys.exit(2)
