import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from oracle_control.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from oracle_control.security import tenant_principal

router = APIRouter(prefix='/v1/admin/users', tags=['workspace administration'])

class FounderInvite(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    redirect_to: str | None = Field(default=None, max_length=2048)

@router.post('/invite-founder', status_code=202)
async def invite_founder(body: FounderInvite, principal=Depends(tenant_principal)):
    if principal.get('auth_method') != 'api_key' or 'admin' not in principal.get('roles', []):
        raise HTTPException(status_code=403, detail='Founder setup requires an administrator API key')
    email = body.email.strip().lower()
    if '@' not in email or email.startswith('@') or email.endswith('@'):
        raise HTTPException(status_code=422, detail='Enter a valid email address')
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail='Supabase Auth administration is not configured')
    headers = {'apikey': SUPABASE_SERVICE_ROLE_KEY, 'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}', 'Content-Type': 'application/json'}
    base = f'{SUPABASE_URL}/auth/v1'
    timeout = httpx.Timeout(20.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        invite_url = f'{base}/invite'
        if body.redirect_to:
            from urllib.parse import quote
            invite_url += '?redirect_to=' + quote(body.redirect_to, safe='')
        invite = await client.post(invite_url, headers=headers, json={'email': email})
        if invite.status_code >= 400:
            try:
                payload = invite.json()
                detail = payload.get('msg') or payload.get('message') or 'Supabase could not send the founder invitation'
            except ValueError:
                detail = 'Supabase could not send the founder invitation'
            raise HTTPException(status_code=invite.status_code if invite.status_code < 500 else 502, detail=detail)
        invited = invite.json()
        user = invited.get('user', invited)
        user_id = user.get('id') if isinstance(user, dict) else None
        if not user_id:
            raise HTTPException(status_code=502, detail='Invitation was sent but Supabase did not return a user ID')
        update = await client.put(f'{base}/admin/users/{user_id}', headers=headers, json={'app_metadata': {'tenant_id': principal['tenant_id'], 'roles': ['admin', 'analyst', 'auditor', 'collector']}})
        if update.status_code >= 400:
            raise HTTPException(status_code=502, detail='Invitation was created, but administrator permissions could not be assigned. Contact platform support before signing in.')
    return {'status': 'invited', 'email': email, 'tenant_id': principal['tenant_id'], 'roles': ['admin', 'analyst', 'auditor', 'collector'], 'message': 'Founder invitation sent. Complete email verification and set a password before signing in.'}