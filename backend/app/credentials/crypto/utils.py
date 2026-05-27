
import os
import json
import hashlib
import base64


def generate_salt(length: int = 16) -> str:
    return base64url_encode(os.urandom(length))


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def sha256_hash(data: str) -> str:
    digest = hashlib.sha256(data.encode("utf-8")).digest()
    return base64url_encode(digest)


def create_disclosure(salt: str, claim_name: str, claim_value: str) -> str:
    disclosure_array = [salt, claim_name, claim_value]
    disclosure_json = json.dumps(disclosure_array, separators=(",", ":"))
    return base64url_encode(disclosure_json.encode("utf-8"))


def hash_disclosure(disclosure: str) -> str:
    return sha256_hash(disclosure)


def decode_disclosure(disclosure: str) -> tuple:
    decoded_bytes = base64url_decode(disclosure)
    decoded_json = json.loads(decoded_bytes.decode("utf-8"))
    return tuple(decoded_json)
