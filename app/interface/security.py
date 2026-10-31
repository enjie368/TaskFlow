'''从 Authorization 头解析当前登录用户'''
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.application.common.token_service import TokenService
from app.domain.shared.vo import UserID
from app.interface.dependency import get_token_service

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
) -> UserID:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供访问凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = token_service.decode(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="凭证已过期，请重新登录",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="凭证无效",
                            headers={"WWW-Authenticate": "Bearer"})

    return UserID(int(payload["sub"]))