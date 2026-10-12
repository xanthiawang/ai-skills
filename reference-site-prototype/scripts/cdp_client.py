"""Minimal stdlib CDP client: open each URL in headless Chrome, wait, run extract JS, save JSON + full-page-height screenshot."""
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9333


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

    def send(self, method, params=None):
        self.i += 1
        data = json.dumps({"id": self.i, "method": method, "params": params or {}}).encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(bytes(hdr) + mask + bytes(b ^ mask[k % 4] for k, b in enumerate(data)))
        while True:
            msg = json.loads(self._recv())
            if msg.get("id") == self.i:
                return msg

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv(self):
        payload = b""
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload += self._read(n)
            if b1 & 0x80:
                return payload.decode("utf-8", "replace")


def main(js_path, out_dir, sites):
    js = open(js_path).read()
    prof = os.path.join(out_dir, ".chrome-profile")
    proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                             "--hide-scrollbars", "--window-size=1440,900", "--lang=zh-CN",
                             "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1); break
            except Exception:
                time.sleep(0.2)
        results = {}
        for name, url in sites:
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?about:blank", method="PUT")
            tab = json.loads(urllib.request.urlopen(req).read())
            ws = WS(tab["webSocketDebuggerUrl"])
            try:
                ws.send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})
                ws.send("Page.enable")
                ws.send("Page.navigate", {"url": url})
                time.sleep(10)
                # scroll once to trigger lazy content, then back to top
                ws.send("Runtime.evaluate", {"expression": "window.scrollTo(0, 1800)"}); time.sleep(1.5)
                ws.send("Runtime.evaluate", {"expression": "window.scrollTo(0, 0)"}); time.sleep(1.5)
                r = ws.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
                val = r.get("result", {}).get("result", {}).get("value")
                data = json.loads(val) if isinstance(val, str) else {"error": r}
                data["captured_at"] = time.strftime("%Y-%m-%d %H:%M:%S %z")
                shot = ws.send("Page.captureScreenshot", {"format": "png", "clip": {"x": 0, "y": 0, "width": 1440, "height": 2400, "scale": 0.6}, "captureBeyondViewport": True})
                if "result" in shot:
                    open(os.path.join(out_dir, f"{name}_long.png"), "wb").write(base64.b64decode(shot["result"]["data"]))
                results[name] = data
                print(name, "ok", data.get("title"))
            except Exception as e:
                results[name] = {"error": str(e)}
                print(name, "ERR", e)
            finally:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
                except Exception:
                    pass
        json.dump(results, open(os.path.join(out_dir, "extracted_styles.json"), "w"), ensure_ascii=False, indent=1)
    finally:
        proc.terminate()


if __name__ == "__main__":
    sites = [s.split("=", 1) for s in sys.argv[3:]]
    main(sys.argv[1], sys.argv[2], sites)
