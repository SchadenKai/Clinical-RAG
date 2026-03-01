import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.db.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    """
    Validates the JWT token and returns the current user profile.
    If dev mode is true, this gracefully falls back to a default dev profile
    if no auth header is provided or if a dummy token is used.
    """
    
    # In a real app with say Supabase Auth:
    # 1. Parse credentials.credentials to verify JWT signature using Supabase JWKS.
    # 2. Extract 'sub' (the UUID of the user).
    # 3. Lookup or Create the user in the Profile table.
    
    is_dummy_token = credentials and credentials.credentials in (
        "dummy_token", "null", "undefined", ""
    )
    
    if settings.dev_mode and (not credentials or is_dummy_token):
        # Fallback to a hardcoded dev user when testing locally without tokens
        dev_email = "dev@example.com"
        dev_user = db.query(User).filter(User.email == dev_email).first()
        if not dev_user:
            # We use a deterministic UUID so it's consistent across reloads
            dev_user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                email=dev_email,
                name="Dev User",
                hashed_password="not_a_real_password",
                role="admin"
            )
            db.add(dev_user)
            db.commit()
            db.refresh(dev_user)
        return dev_user
        
    if not credentials:
        raise HTTPException(
            status_code=401, detail="Missing or invalid authentication token"
        )
        
    token = credentials.credentials
    # >>> Implement actual JWT verification here using jose or PyJWT <<<
    # For now, we will assume token payload has {"sub": "user-uuid"}
    # payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    # user_id = payload.get("sub")
    
    # Mocking extraction since we don't have the auth provider hooked up:
    user_id = token  # Just as a placeholder to allow passing an arbitrary ID if needed
    
    try:
        parsed_id = uuid.UUID(user_id)
        user = db.query(User).filter(User.id == parsed_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except ValueError as err:
        raise HTTPException(
            status_code=401, detail="Invalid token format"
        ) from err
