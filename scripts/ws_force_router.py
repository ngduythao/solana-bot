#!/usr/bin/env python3
# Lightweight TCP proxy for Solana WS → always forwards to ws derived from rpc:current
import asyncio, os
from urllib.parse import urlparse
import redis

PORT = int(os.environ.get("WS_FORCE_PORT","8900"))
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def derive_ws(url: str) -> str:
    if not url: return os.environ.get("WS_DEFAULT","")
    u = urlparse(url)
    scheme = 'wss' if u.scheme in ('https','wss') else 'ws'
    netloc = u.netloc or u.path
    return f"{scheme}://{netloc}"

def target_host_port() -> tuple[str,int]:
    rpc = r.get("rpc:current") or os.environ.get("RPC_DEFAULT","")
    ws  = r.get("ws:current") or derive_ws(rpc)
    if not ws:
        ws = os.environ.get("SOLANA_WS_URL","") or os.environ.get("WS_URL","")
    u = urlparse(ws)
    host = u.hostname or '127.0.0.1'
    port = u.port or (443 if u.scheme in ('wss','https') else 80)
    return host, port

async def handle_client(reader, writer):
    try:
        host, port = target_host_port()
        r = await asyncio.open_connection(host, port, ssl=(port==443))
    except Exception as e:
        writer.close(); await writer.wait_closed(); return
    sr, sw = r
    async def pipe(src, dst):
        try:
            while True:
                data = await src.read(65536)
                if not data: break
                dst.write(data)
                await dst.drain()
        except:
            pass
        finally:
            try: dst.close()
            except: pass
    await asyncio.gather(pipe(reader, sw), pipe(sr, writer))

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', PORT)
    async with server:
        await server.serve_forever()

if __name__=='__main__':
    asyncio.run(main())
