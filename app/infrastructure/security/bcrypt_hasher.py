import bcrypt

from app.domain.user.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, raw: str) -> str:
        '''把明文密码加密'''
        return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, raw: str, hashed: str) -> bool:
        '''校验明文与密文是否匹配'''
        try:
            return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False