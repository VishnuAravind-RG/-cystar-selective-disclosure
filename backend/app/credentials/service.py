
import uuid
from datetime import datetime, timedelta
from app.credentials.crypto import ed25519
from app.credentials.crypto.sd_jwt import create_sd_jwt, create_presentation
from app.credentials.repository import (
    save_credential,
    get_user_credentials,
    get_credential_by_id,
    save_presentation,
)
from app.core.exceptions import AppException
from app.core.config import get_settings

settings = get_settings()


async def issue_credential(user_id: str, claims: dict, issuer_name: str, credential_title: str) -> dict:
    private_key, public_key = ed25519.generate_keypair()

    sd_jwt_data = create_sd_jwt(
        claims=claims,
        issuer_name=issuer_name,
        subject=user_id,
        private_key_hex=private_key,
    )

    credential_data = {
        "user_id": user_id,
        "credential_title": credential_title,
        "issuer_name": issuer_name,
        "claims": claims,
        "sd_jwt": sd_jwt_data["sd_jwt"],
        "disclosures": sd_jwt_data["disclosures"],
        "sd_hashes": sd_jwt_data["sd_hashes"],
        "public_key": public_key,
        "private_key": private_key,
    }

    credential_id = await save_credential(credential_data)

    return {
        "id": credential_id,
        "credential_title": credential_title,
        "issuer_name": issuer_name,
        "claims": claims,
        "created_at": credential_data["created_at"].isoformat(),
    }


async def list_credentials(user_id: str) -> list:
    credentials = await get_user_credentials(user_id)
    return [
        {
            "id": c["_id"],
            "credential_title": c.get("credential_title", "Credential"),
            "issuer_name": c["issuer_name"],
            "claims": c["claims"],
            "created_at": c["created_at"].isoformat() if hasattr(c["created_at"], "isoformat") else str(c["created_at"]),
        }
        for c in credentials
    ]


async def share_credential(user_id: str, credential_id: str, selected_fields: list, expires_in_hours: int) -> dict:
    credential = await get_credential_by_id(credential_id, user_id)
    if not credential:
        raise AppException(status_code=404, detail="Credential not found")

    available_fields = list(credential["claims"].keys())
    invalid_fields = [f for f in selected_fields if f not in available_fields]
    if invalid_fields:
        raise AppException(
            status_code=400,
            detail=f"Invalid fields: {invalid_fields}. Available: {available_fields}",
        )

    presentation = create_presentation(
        sd_jwt=credential["sd_jwt"],
        all_disclosures=credential["disclosures"],
        selected_fields=selected_fields,
    )

    share_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

    presentation_data = {
        "share_token": share_token,
        "credential_id": credential_id,
        "user_id": user_id,
        "presentation": presentation,
        "public_key": credential["public_key"],
        "selected_fields": selected_fields,
        "total_fields": len(available_fields),
        "issuer_name": credential["issuer_name"],
        "credential_title": credential.get("credential_title", "Credential"),
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
    }

    await save_presentation(presentation_data)

    share_url = f"{settings.FRONTEND_URL}/verify/{share_token}"

    return {
        "share_token": share_token,
        "share_url": share_url,
        "expires_at": expires_at.isoformat(),
        "selected_fields": selected_fields,
    }
