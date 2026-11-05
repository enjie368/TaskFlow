'''订单仓储接口'''
from abc import ABC, abstractmethod

from app.domain.shared.vo import UserID

from .entity import Order


class OrderRepository(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: UserID, limit: int, offset: int) -> list[Order]:
        '''按用户查订单（分页）'''
        ...

    @abstractmethod
    async def count_by_user_id(self, user_id: UserID) -> int:
        '''统计用户订单总数'''
        ...

    @abstractmethod
    async def add(self, order: Order) -> Order:
        '''新增订单，返回落库后的实体'''
        ...

    @abstractmethod
    async def find_by_id_and_user_id(self, order_id: int, user_id: UserID) -> Order | None:
        '''按 id 查订单，且必须属于该用户；不存在或不是本人的都返回 None'''
        ...

    @abstractmethod
    async def update(self, order: Order) -> Order:
        '''把实体的变更写回数据库'''
        ...
