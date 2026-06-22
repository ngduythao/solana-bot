
import asyncio

async def http_get_retry(client, url, *, params=None, json=None, max_tries=4, base_delay=0.2, timeout=3.0):
    for i in range(max_tries):
        try:
            r = await client.get(url, params=params, json=json, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception:
            await asyncio.sleep(base_delay*(2**i) + (0.05*i))
    raise RuntimeError("HTTP GET retry exhausted")

async def http_post_retry(client, url, *, data=None, json=None, max_tries=4, base_delay=0.2, timeout=3.0):
    for i in range(max_tries):
        try:
            r = await client.post(url, data=data, json=json, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception:
            await asyncio.sleep(base_delay*(2**i) + (0.05*i))
    raise RuntimeError("HTTP POST retry exhausted")
