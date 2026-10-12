import sys, json, time, os, importlib.util, subprocess, urllib.request
spec = importlib.util.spec_from_file_location('cdp', sys.argv[1]); cdp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cdp)
url, port = sys.argv[2], int(sys.argv[3]); prof = os.path.abspath(f'.hp{port}')
proc = subprocess.Popen([cdp.CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "--hide-scrollbars", "--lang=zh-CN", "--window-size=1440,900", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
JS = r'''(function(){const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
 const hs=[...document.querySelectorAll('h1,h2,h3')].filter(vis).map(e=>({t:e.tagName,x:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,90),y:Math.round(e.getBoundingClientRect().top+scrollY)})).filter(h=>h.x);
 return JSON.stringify({title:document.title,h:document.documentElement.scrollHeight,hs:hs});})()'''
try:
    for _ in range(60):
        try: urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1); break
        except Exception: time.sleep(0.25)
    tab = json.loads(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")).read())
    ws = cdp.WS(tab["webSocketDebuggerUrl"]); ws.send("Emulation.setDeviceMetricsOverride", {"width":1440,"height":900,"deviceScaleFactor":1,"mobile":False}); ws.send("Page.enable"); ws.send("Runtime.enable")
    ws.send("Page.navigate", {"url": url}); time.sleep(7)
    ws.send("Runtime.evaluate", {"expression": "(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,150))} scrollTo(0,0)})()", "awaitPromise": True}); time.sleep(1.5)
    info = json.loads(ws.send("Runtime.evaluate", {"expression": JS, "returnByValue": True})["result"]["result"]["value"])
    print(json.dumps({'url':url,'title':info['title'],'h':info['h']}, ensure_ascii=False))
    for h in info['hs']: print(f"  {h['y']:6d} {h['t']}  {h['x']}")
finally:
    proc.terminate(); time.sleep(0.3); subprocess.run(['rm','-rf',prof])
