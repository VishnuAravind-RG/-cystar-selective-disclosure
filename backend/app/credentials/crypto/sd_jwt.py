
import json
import time
from app.credentials.crypto.utils import (
    generate_salt,
    base64url_encode,
    base64url_decode,
    create_disclosure,
    hash_disclosure,
    decode_disclosure,
)
from app.credentials.crypto import ed25519


def create_sd_jwt(
    claims: dict,
    issuer_name: str,
    subject: str,
    private_key_hex: str,
) -> dict:
    disclosures = {}
    sd_hashes = {}

    for claim_name, claim_value in claims.items():
        salt = generate_salt()
        disclosure = create_disclosure(salt, claim_name, str(claim_value))
        d_hash = hash_disclosure(disclosure)
        disclosures[claim_name] = disclosure
        sd_hashes[claim_name] = d_hash

    header = {"alg": "EdDSA", "typ": "sd-jwt"}

    payload = {
        "iss": issuer_name,
        "sub": subject,
        "iat": int(time.time()),
        "_sd": sorted(sd_hashes.values()),
        "_sd_alg": "sha-256",
    }

    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    signature = ed25519.sign(signing_input.encode("utf-8"), private_key_hex)
    signature_b64 = base64url_encode(bytes.fromhex(signature))

    sd_jwt = f"{signing_input}.{signature_b64}"

    return {
        "sd_jwt": sd_jwt,
        "disclosures": disclosures,
        "sd_hashes": sd_hashes,
    }


def create_presentation(
    sd_jwt: str,
    all_disclosures: dict,
    selected_fields: list,
) -> str:
    parts = [sd_jwt]
    for field in selected_fields:
        if field in all_disclosures:
            parts.append(all_disclosures[field])
    return "~".join(parts) + "~"


def verify_presentation(presentation: str, public_key_hex: str) -> dict:
    parts = presentation.rstrip("~").split("~")

    if len(parts) < 1:
        return {"verified": False, "error": "Invalid presentation format"}

    sd_jwt = parts[0]
    disclosure_strings = parts[1:]

    jwt_parts = sd_jwt.split(".")
    if len(jwt_parts) != 3:
        return {"verified": False, "error": "Invalid SD-JWT format"}

    header_b64, payload_b64, signature_b64 = jwt_parts

    signing_input = f"{header_b64}.{payload_b64}"
    signature_hex = base64url_decode(signature_b64).hex()

    if not ed25519.verify(signing_input.encode("utf-8"), signature_hex, public_key_hex):
        return {"verified": False, "error": "Signature verification failed"}

    payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
    sd_digests = set(payload.get("_sd", []))
    total_claims = len(sd_digests)

    disclosed_fields = {}
    matched_hashes = set()

    for disclosure in disclosure_strings:
        d_hash = hash_disclosure(disclosure)
        if d_hash not in sd_digests:
            return {"verified": False, "error": "Disclosure hash mismatch - data may be tampered"}

        salt, claim_name, claim_value = decode_disclosure(disclosure)
        disclosed_fields[claim_name] = claim_value
        matched_hashes.add(d_hash)

    return {
        "verified": True,
        "disclosed_fields": disclosed_fields,
        "issuer": payload.get("iss", ""),
        "subject": payload.get("sub", ""),
        "issued_at": payload.get("iat", 0),
        "total_claims": total_claims,
        "disclosed_count": len(disclosed_fields),
        "hidden_count": total_claims - len(disclosed_fields),
    }
