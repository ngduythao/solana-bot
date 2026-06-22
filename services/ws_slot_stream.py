
import os, json, time, redis, threading, websocket

WS = os.getenv("WS_ENDPOINT","wss://api.mainnet-beta.solana.com")
ENABLE = os.getenv("WS_ENABLE","1")=="1"
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))

def on_message(ws, message):
    try:
        d = json.loads(message)
        if d.get("method")=="notification" or d.get("params"):
            r.set("hsbot:last_slot_ts", time.time())
    except Exception as e:
        pass

def on_open(ws):
    sub = {"jsonrpc":"2.0","id":1,"method":"slotSubscribe"}
    ws.send(json.dumps(sub))

def run():
    if not ENABLE: 
        print("[ws_slot_stream] disabled"); return
    while True:
        try:
            ws = websocket.WebSocketApp(WS, on_open=on_open, on_message=on_message)
            ws.run_forever(ping_interval=20)
        except Exception as e:
            time.sleep(1)

if __name__=="__main__":
    run()
