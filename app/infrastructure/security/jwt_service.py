import datetime

import jwt

from app.application.common.token_service import TokenService


class JwtTokenService(TokenService):
    def __init__(self, secret: str, algorithm: str = "HS256", expire_minutes: int = 60):
        self.secret = secret
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(self, user_id: int, username: str) -> tuple[str, int]:
        now = datetime.datetime.now(datetime.UTC)
        expire = now + datetime.timedelta(minutes=self.expire_minutes)
        payload = {
            "sub": str(user_id),
            "username": username,
            "iat": now,
            "exp": expire,
        }
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, self.expire_minutes * 60

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])