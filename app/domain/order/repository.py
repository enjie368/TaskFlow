'''订单仓储接口'''
from abc import ABC, abstractmethod

from app.domain.shared.vo import UserID
from .entity import Order


class OrderRepository(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: UserID, limit: int, offset: int) -> list[Order]:
        '''按用户查订单（分页）'''
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: UserID) -> int:
        '''统计用户订单总数'''
        pass

    @abstractmethod
    async def add(self, order: Order) -> Order:
        '''新增订单，返回落库后的实体'''
        pass