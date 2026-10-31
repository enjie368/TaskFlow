'''令牌服务抽象——应用层需要"发一个凭证"，但不关心算法'''
from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: int, username: str) -> tuple[str, int]:
        '''签发令牌，返回 (token, 有效期秒数)'''

    @abstractmethod
    def decode(self, token: str) -> dict:
        '''解析令牌，失败抛异常'''