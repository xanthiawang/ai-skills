"""无头走查单文件原型（stdlib CDP，沿用 cdp_client.py 的 WS 客户端）。

原型文件按 artifact 约定以 <title> 开头、无 doctype，直接本地打开手机视口会按 980 宽排版；
所以先包一层 <!doctype html>…<meta viewport> 骨架写到输出目录再加载。
每个视口 × 路由：收集 Runtime.exceptionThrown / console.error / Log error，检查 scrollWidth 是否超出 innerWidth，
保存整页截图，并把结果写成 walkthrough.json。

用法：python3 cdp_walkthrough_2026-10-12.py <原型.html> <输出目录> route[:js动作] ...
例：  ... 沐仞官网原型_2026-10-12.html out home guides "newsletter:document.querySelector('#nlIdx [data-n=1]').click()"
"""
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9337
SKEL = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n'
VIEWPORTS = [("desktop", 1440, 900, 1, False, 5200, 0.6), ("mobile", 390, 844, 2, True, 7000, 1)]
CHECK_JS = r"""(function(){var d=document.documentElement,iw=window.innerWidth,over=[];
if(d.scrollWidth>iw+1){Array.prototype.forEach.call(document.querySelectorAll('body *'),function(e){var r=e.getBoundingClientRect();if(r.width>0&&r.right>iw+1&&over.length<10){var cs=getComputedStyle(e);if(cs.position!=='fixed'&&cs.visibility!=='hidden')over.push(e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\s+/).join('.'):'')+' right='+Math.round(r.right))}})}
var on=document.querySelector('[data-route].on');
return JSON.stringify({title:document.title,route:on?on.getAttribute('data-route'):null,iw:iw,sw:d.scrollWidth,sh:d.scrollHeight,over:over,
 newsletterLinks:document.querySelectorAll('a[href="#newsletter"]').length,guideCards:document.querySelectorAll('#guideCards .gcard').length,
 h1:(document.querySelector('[data-route].on h1')||{}).textContent||null})})()"""


class WS:
    def __init__(self, url):
        host, rest = url.split("//", 1)[1].split("/", 1)
        h, p = host.split(":")
        self.s = socket.create_connection((h, int(p)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.i = 0
        self.events = []

    def send(self, method, params=None):
        self.i += 1
        data = json.dumps({"id": self.i, "method": method, "params": params or {}}).encode()
        hdr = bytearray([0x81]); n = len(data)
        if n < 126: hdr.append(0x80 | n)
        elif n < 65536: hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else: hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(bytes(hdr) + mask + bytes(b ^ mask[k % 4] for k, b in enumerate(data)))
        while True:
            msg = json.loads(self._recv())
            if msg.get("id") == self.i: return msg
            if "method" in msg: self.events.append(msg)

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk: raise ConnectionError("closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv(self):
        payload = b""
        while True:
            b1, b2 = self._read(2); n = b2 & 0x7F
            if n == 126: n = struct.unpack(">H", self._read(2))[0]
            elif n == 127: n = struct.unpack(">Q", self._read(8))[0]
            payload += self._read(n)
            if b1 & 0x80: return payload.decode("utf-8", "replace")


def classify(events):
    errs, logs = [], []
    for ev in events:
        m, p = ev["method"], ev.get("params", {})
        if m == "Runtime.exceptionThrown":
            d = p.get("exceptionDetails", {}); e = d.get("exception", {})
            errs.append("exception: " + (e.get("description") or d.get("text") or "?")[:300])
        elif m == "Runtime.consoleAPICalled" and p.get("type") in ("error", "warning", "assert"):
            errs.append(p["type"] + ": " + " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", []))[:300])
        elif m == "Log.entryAdded" and p.get("entry", {}).get("level") in ("error", "warning"):
            logs.append(p["entry"]["level"] + " " + p["entry"].get("source", "") + ": " + p["entry"].get("text", "")[:200] + " " + p["entry"].get("url", "")[:120])
    return errs, logs


def main(html_path, out_dir, routes):
    os.makedirs(out_dir, exist_ok=True)
    wrapped = os.path.join(out_dir, "wrapped.html")
    with open(wrapped, "w", encoding="utf-8") as f:
        f.write(SKEL + open(html_path, encoding="utf-8").read() + "\n</body></html>")
    url0 = "file://" + os.path.abspath(wrapped)
    prof = os.path.join(out_dir, ".chrome-profile")
    proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                             "--hide-scrollbars", "--window-size=1440,900", "--lang=zh-CN", "--allow-file-access-from-files", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = []
    try:
        for _ in range(50):
            try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1); break
            except Exception: time.sleep(0.2)
        for vname, W, H, dsf, mobile, cap, scale in VIEWPORTS:
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?about:blank", method="PUT")
            tab = json.loads(urllib.request.urlopen(req).read())
            ws = WS(tab["webSocketDebuggerUrl"])
            try:
                ws.send("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": dsf, "mobile": mobile})
                if mobile:
                    ws.send("Emulation.setUserAgentOverride", {"userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari/604.1"})
                ws.send("Page.enable"); ws.send("Runtime.enable"); ws.send("Log.enable")
                for k, spec in enumerate(routes):
                    route, _, action = spec.partition(":")
                    name = f"{k:02d}_{route}" + ("_act" if action else "")
                    ws.events = []
                    ws.send("Page.navigate", {"url": "about:blank"}); time.sleep(0.3)
                    ws.send("Page.navigate", {"url": url0 + "#" + route}); time.sleep(2.4)
                    if action:
                        r = ws.send("Runtime.evaluate", {"expression": action, "returnByValue": True}); time.sleep(0.8)
                        if "exceptionDetails" in r.get("result", {}): ws.events.append({"method": "Runtime.exceptionThrown", "params": r["result"]})
                    ws.send("Runtime.evaluate", {"expression": "window.scrollTo(0,0)"}); time.sleep(0.3)
                    r = ws.send("Runtime.evaluate", {"expression": CHECK_JS, "returnByValue": True})
                    val = r.get("result", {}).get("result", {}).get("value")
                    data = json.loads(val) if isinstance(val, str) else {"error": str(r)[:300]}
                    ws.send("Runtime.evaluate", {"expression": "1"})  # drain pending events
                    errs, logs = classify(ws.events)
                    h = min(int(data.get("sh", H)), cap)
                    shot = ws.send("Page.captureScreenshot", {"format": "png", "clip": {"x": 0, "y": 0, "width": W, "height": h, "scale": scale}, "captureBeyondViewport": True})
                    png = os.path.join(out_dir, f"{vname}_{name}.png")
                    if "result" in shot: open(png, "wb").write(base64.b64decode(shot["result"]["data"]))
                    row = {"viewport": vname, "route": route, "action": action or None, "check": data, "js_errors": errs, "log": logs, "png": os.path.basename(png)}
                    results.append(row)
                    # 手机模拟下内容溢出会把布局视口撑宽（innerWidth > 设定宽度），所以同时比较 sw/iw 与设定的 W
                    data["overflow"] = bool(data.get("sw", 0) > data.get("iw", 0) + 1 or data.get("iw", 0) > W)
                    if data["overflow"] and not data.get("over"):
                        data["over"] = ["viewport widened to %s (set %s)" % (data.get("iw"), W)]
                    flag = "OK " if not errs and not data["overflow"] else "!! "
                    print(f"{flag}{vname:7s} #{route:18s} route={data.get('route')} title={data.get('title')} sw={data.get('sw')}/{data.get('iw')}/W{W} sh={data.get('sh')} errs={len(errs)} log={len(logs)} h1={data.get('h1')}")
                    for o in (data.get("over") or []): print("     overflow:", o)
                    for e in errs: print("    ", e)
                    for l in logs: print("    ", l)
            finally:
                try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
                except Exception: pass
        json.dump(results, open(os.path.join(out_dir, "walkthrough.json"), "w"), ensure_ascii=False, indent=1)
        bad = [r for r in results if r["js_errors"] or r["check"].get("overflow")]
        print(f"\n{len(results)} checks, {len(bad)} with JS errors or horizontal overflow")
    finally:
        proc.terminate()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
