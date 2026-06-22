#!/usr/bin/env python3
import http.server, socketserver, requests, os, json
from urllib.parse import urlparse
PORT = int(os.environ.get("RPC_FORCE_PORT","8899"))
import redis
r=redis.Redis(host='localhost', port=6379, decode_responses=True)

class Handler(http.server.BaseHTTPRequestHandler):
    def _get_target(self):
        url = r.get("rpc:current") or os.environ.get("RPC_DEFAULT","")
        if not url:
            # fallback common env
            url = os.environ.get("SOLANA_RPC_URL","") or os.environ.get("RPC_URL","")
        return url

    def _proxy(self, method):
        target = self._get_target()
        if not target:
            self.send_response(503); self.end_headers(); self.wfile.write(b"No RPC current"); return
        try:
            length = int(self.headers.get('Content-Length','0'))
            data = self.rfile.read(length) if length>0 else None
            headers = {k:v for k,v in self.headers.items() if k.lower()!='host'}
            resp = requests.request(method, target, data=data, headers=headers, timeout=5)
            self.send_response(resp.status_code)
            for k,v in resp.headers.items():
                if k.lower()=='content-length': continue
                self.send_header(k,v)
            body = resp.content
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502); self.end_headers(); self.wfile.write(f"Router error: {e}".encode())

    def do_GET(self):  self._proxy('GET')
    def do_POST(self): self._proxy('POST')

if __name__=="__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"[rpc_force_router] listening on 127.0.0.1:{PORT}")
        httpd.serve_forever()
