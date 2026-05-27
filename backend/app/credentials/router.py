
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.credentials.schemas import IssueRequest, ShareRequest, ShareResponse
from app.credentials.service import issue_credential, list_credentials, share_credential

router = APIRouter()


@router.post("/issue")
async def issue(request: IssueRequest, user: dict = Depends(get_current_user)):
    return await issue_credential(
        user_id=user["user_id"],
        claims=request.claims,
        issuer_name=request.issuer_name,
        credential_title=request.credential_title,
    )


@router.get("/")
async def get_credentials(user: dict = Depends(get_current_user)):
    return await list_credentials(user["user_id"])


@router.post("/share", response_model=ShareResponse)
async def share(request: ShareRequest, user: dict = Depends(get_current_user)):
    return await share_credential(
        user_id=user["user_id"],
        credential_id=request.credential_id,
        selected_fields=request.selected_fields,
        expires_in_hours=request.expires_in_hours,
    )
