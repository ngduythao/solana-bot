
import asyncio, httpx
async def http_get_retry(client,url,params=None,max_tries=4,base_delay=0.2):
    for i in range(max_tries):
        try:
            r=await client.get(url,params=params,timeout=3.0)
            r.raise_for_status(); return r
        except Exception as e:
            await asyncio.sleep(base_delay*(2**i)+0.05*i)
    raise RuntimeError("http_get_retry exhausted")
