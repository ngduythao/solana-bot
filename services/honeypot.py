
import os, socket, threading, redis, time
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
PORT=int(os.getenv("HONEYPOT_PORT","10025"))
ENABLE=os.getenv("ENABLE_HONEYPOT","0")=="1"

def handler(conn, addr):
    try:
        r.sadd("solbot:deny:ips", addr[0])
        conn.sendall(b"220 Ready\r\n")
        time.sleep(0.2)
    except Exception:
        pass
    finally:
        conn.close()

def main():
    if not ENABLE:
        print("[honeypot] disabled"); return
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT)); s.listen(50)
    print(f"[honeypot] listening on {PORT}")
    while True:
        c,a=s.accept()
        threading.Thread(target=handler, args=(c,a), daemon=True).start()

if __name__=="__main__":
    main()
