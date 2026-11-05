'''
用户仓储接口
'''
from abc import ABC, abstractmethod

from ..shared.vo import UserID
from .entity import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User)->User:
        '''保存用户'''
        ...
    @abstractmethod
    async def find_by_id(self, user_id: UserID)->User | None:
        '''通过id查找用户'''
        ...
    @abstractmethod
    async def find_by_name(self, name: str) -> User | None:
        '''通过用户名查找用户'''
        ...
    @abstractmethod
    async def exist_by_name(self, name: str) -> bool:
        '''检查用户是否存在'''
        ...
    @abstractmethod
    async def delete(self, user_id: UserID)->bool:
        '''删除用户'''
        ...
    @abstractmethod
    async def search_all(self) -> list[User]:
        '''查找所有用户'''
        ...

