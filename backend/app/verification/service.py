
from datetime import datetime
from app.credentials.repository import get_presentation_by_token
from app.credentials.crypto.sd_jwt import verify_presentation
from app.core.exceptions import AppException


async def verify_shared_credential(share_token: str) -> dict:
    presentation_doc = await get_presentation_by_token(share_token)
    if not presentation_doc:
        raise AppException(status_code=404, detail="Share link not found or expired")

    expired = False
    if "expires_at" in presentation_doc:
        expired = datetime.utcnow() > presentation_doc["expires_at"]

    if expired:
        return {
            "verified": False,
            "expired": True,
            "error": "This share link has expired",
        }

    result = verify_presentation(
        presentation=presentation_doc["presentation"],
        public_key_hex=presentation_doc["public_key"],
    )

    result["expired"] = expired
    result["credential_title"] = presentation_doc.get("credential_title", "Credential")

    return result
