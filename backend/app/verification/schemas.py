
from pydantic import BaseModel
from typing import Optional


class VerificationResponse(BaseModel):
    verified: bool
    credential_title: Optional[str] = None
    disclosed_fields: Optional[dict] = None
    issuer: Optional[str] = None
    issued_at: Optional[int] = None
    total_claims: Optional[int] = None
    disclosed_count: Optional[int] = None
    hidden_count: Optional[int] = None
    expired: Optional[bool] = None
    error: Optional[str] = None
