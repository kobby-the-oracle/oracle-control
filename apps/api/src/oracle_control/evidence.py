import hashlib
import json
from typing import Any

def canonical_json(value: Any) -> bytes:
    """Stable JSON bytes for repeatable digests; this is not a digital signature."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def event_digests(event: dict[str, Any]) -> tuple[str, str]:
    return sha256_hex(canonical_json(event["payload"])), sha256_hex(canonical_json(event))

def verify_digest(data: bytes, expected_sha256: str) -> bool:
    return sha256_hex(data) == expected_sha256.lower()
