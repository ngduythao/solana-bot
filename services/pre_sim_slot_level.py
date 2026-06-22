
# This module enriches pre_sim with slot-level info if available.
import os, json, redis, time
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def enrich_with_slot(slot:int, plan:dict):
    # placeholder: tag slot; real math is in simulator core
    plan["slot"] = slot
    return plan
