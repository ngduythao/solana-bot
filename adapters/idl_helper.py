
import os, json, base64
from typing import Any, Dict, Optional
try:
    from anchorpy import Idl, IdlAccount, IdlTypeDef
    from borsh_construct import CStruct, U8, U16, U32, U64, I32, I64
    LIBS_OK = True
except Exception:
    LIBS_OK = False

# Fallback minimal types
def _num(bytes_len: int, signed=False):
    import struct
    def parse(b: bytes, off: int):
        fmt = {1: 'b' if signed else 'B',
               2: 'h' if signed else 'H',
               4: 'i' if signed else 'I',
               8: 'q' if signed else 'Q'}[bytes_len]
        return int.from_bytes(b[off:off+bytes_len], 'little', signed=signed)
    return parse

def extract_offsets_from_idl(idl_json: Dict[str, Any], account_name: str, fields: Dict[str, int]) -> Dict[str,int]:
    """Best-effort: returns offsets for requested fields by walking Anchor IDL struct in order.
    If unsupported, returns provided 'fields' as fallback (manual offsets).
    """
    if not idl_json:
        return fields
    try:
        # find account
        accs = idl_json.get("accounts", [])
        acct = next(a for a in accs if a.get("name","").lower()==account_name.lower())
        layout = acct["type"]["fields"]
        off = 8  # skip Anchor discriminator
        offsets = {}
        for f in layout:
            name = f["name"]
            t = f["type"]
            # handle common primitives (u16,u32,u64,i32,i64, bytes[16], publicKey[32])
            if t == "u8": size=1
            elif t == "i8": size=1
            elif t == "u16": size=2
            elif t == "i16": size=2
            elif t == "u32": size=4
            elif t == "i32": size=4
            elif t == "u64": size=8
            elif t == "i64": size=8
            elif t == "publicKey": size=32
            elif isinstance(t, dict) and t.get("array"):
                elem = t["array"][0]
                length = t["array"][1]
                if elem == "u8": size = length
                else: size = 0
            else:
                # unknown/complex; stop mapping
                size = 0
            if name not in offsets and name in fields:
                offsets[name] = off
            off += size
        # fill missing from defaults
        for k,v in fields.items():
            offsets.setdefault(k,v)
        return offsets
    except Exception:
        return fields
