'''订单查询缓存契约——同 LoginAttemptGuard 的定位：用例支撑，不进 domain'''
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.user.queries.get_orders import GetOrdersResult

class OrderQueryCache(ABC):
    '''订单列表缓存的三件套：读 / 存 / 失效'''

    @abstractmethod
    async def get(self, user_id: int, limit: int, offset: int) -> GetOrdersResult | None:
        '''读缓存：命中返回结果，未命中返回 None（由 Handler 决定回源查库）'''

    @abstractmethod
    async def save(self, user_id: int, limit: int, offset: int, result: GetOrdersResult) -> None:
        '''存缓存：把查库结果写入 Redis，带 TTL（过期自动消失）'''

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        '''失效：该用户发生写操作（下单/取消）后调用，让所有旧列表缓存作废'''
