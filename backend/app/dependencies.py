import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials

    # Newer Supabase projects (and recent Supabase CLI versions - this is
    # what a fresh `supabase start` gives you) sign JWTs asymmetrically
    # (ES256) via "JWT signing keys" instead of the legacy shared HS256
    # secret. HS256-decoding one of those tokens raises JWTError every time,
    # 401ing every authenticated request. Try the shared-secret path first
    # (cheap, no network call, works for projects still on the legacy
    # secret), and fall back to asking Supabase's own auth server to
    # validate the token - which works for either signing scheme - instead
    # of failing outright.
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            return {
                "id": user_id,
                "email": payload.get("email"),
            }
        except JWTError as exc:
            logger.info(
                "HS256 JWT decode failed (%s) - falling back to Supabase "
                "auth server verification, likely an asymmetrically-signed "
                "token",
                exc,
            )

    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
    except Exception as exc:
        logger.warning("Supabase token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if not user_response or not user_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {
        "id": user_response.user.id,
        "email": user_response.user.email,
    }


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    supabase = get_supabase_client()
    result = (
        supabase.table("users")
        .select("is_admin")
        .eq("id", current_user["id"])
        .single()
        .execute()
    )

    if not result.data or not result.data.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
