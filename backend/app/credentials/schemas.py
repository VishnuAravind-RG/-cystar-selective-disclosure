
from pydantic import BaseModel, Field
from typing import Optional


class IssueRequest(BaseModel):
    claims: dict = Field(..., min_length=1)
    issuer_name: str = Field(..., min_length=1)
    credential_title: str = Field(default="Credential", max_length=200)


class CredentialResponse(BaseModel):
    id: str
    credential_title: str
    issuer_name: str
    claims: dict
    created_at: str


class ShareRequest(BaseModel):
    credential_id: str
    selected_fields: list = Field(..., min_length=1)
    expires_in_hours: int = Field(default=24, ge=1, le=168)


class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: str
    selected_fields: list
