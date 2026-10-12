import sys, json, time, os, base64, importlib.util, subprocess, urllib.request
spec = importlib.util.spec_from_file_location('cdp', sys.argv[1]); cdp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cdp)
url, out, port = sys.argv[2], sys.argv[3], int(sys.argv[4]); width = int(sys.argv[5]) if len(sys.argv)>5 else 1440
prof = out + '.prof'
proc = subprocess.Popen([cdp.CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "--hide-scrollbars", "--lang=zh-CN", f"--window-size={width},900", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
JS = r'''(function(){
 const vis=e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'};
 const txt=e=>(e.innerText||e.getAttribute('aria-label')||'').trim().replace(/\s+/g,' ').slice(0,60);
 const pick=(root)=>[...root.querySelectorAll('a,button')].filter(vis).map(e=>({t:txt(e),h:e.getAttribute('href')||'',tag:e.tagName.toLowerCase(),bg:getComputedStyle(e).backgroundColor,c:getComputedStyle(e).color,r:getComputedStyle(e).borderRadius,y:Math.round(e.getBoundingClientRect().top+scrollY)})).filter(x=>x.t);
 const hdr=document.querySelector('header, nav, [class*="header"], [class*="navbar"], [class*="Header"]');
 const ftr=document.querySelector('footer, [class*="footer"], [class*="Footer"]');
 const all=pick(document);
 return JSON.stringify({title:document.title, h:document.documentElement.scrollHeight, header:hdr?pick(hdr):[], footer:ftr?pick(ftr):[], top:all.filter(x=>x.y<900), count:all.length, lang:document.documentElement.lang});
})()'''
try:
    for _ in range(60):
        try: urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1); break
        except Exception: time.sleep(0.25)
    tab = json.loads(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")).read())
    ws = cdp.WS(tab["webSocketDebuggerUrl"])
    mobile = width < 800
    ws.send("Emulation.setDeviceMetricsOverride", {"width": width, "height": 900 if not mobile else 844, "deviceScaleFactor": 1 if not mobile else 2, "mobile": mobile})
    if mobile: ws.send("Emulation.setUserAgentOverride", {"userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"})
    ws.send("Page.enable"); ws.send("Runtime.enable")
    ws.send("Page.navigate", {"url": url}); time.sleep(7)
    # scroll through to trigger lazy content, then back to top
    ws.send("Runtime.evaluate", {"expression": "(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,120))} scrollTo(0,0)})()", "awaitPromise": True}); time.sleep(1.5)
    info = json.loads(ws.send("Runtime.evaluate", {"expression": JS, "returnByValue": True})["result"]["result"]["value"])
    info['url']=url; json.dump(info, open(out + '.json','w'), ensure_ascii=False, indent=1)
    h = min(info['h'], 12000)
    shot = ws.send("Page.captureScreenshot", {"format": "jpeg", "quality": 80, "clip": {"x":0,"y":0,"width":width,"height":h,"scale":1 if not mobile else 1}, "captureBeyondViewport": True})
    open(out + '_long.jpg','wb').write(base64.b64decode(shot["result"]["data"]))
    shot = ws.send("Page.captureScreenshot", {"format": "png"})
    open(out + '_top.png','wb').write(base64.b64decode(shot["result"]["data"]))
    print(json.dumps({k:info[k] for k in ('title','h','count','lang')}, ensure_ascii=False))
    print('HEADER', json.dumps([(x['t'],x['h']) for x in info['header']][:30], ensure_ascii=False))
    print('FOOTER', json.dumps([(x['t'],x['h']) for x in info['footer']][:60], ensure_ascii=False))
finally:
    proc.terminate(); time.sleep(0.5)
    subprocess.run(['rm','-rf',prof])
