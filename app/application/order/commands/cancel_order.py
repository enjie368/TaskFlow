'''取消订单'''
from dataclasses import dataclass

from app.application.common.exception import ConflictError, NotFoundError
from app.application.common.order_query_cache import OrderQueryCache
from app.domain.order.entity import Order, OrderStatusError
from app.domain.order.repository import OrderRepository
from app.domain.shared.vo import UserID


@dataclass
class CancelOrderCommand:
    order_id: int
    user_id: int


class CancelOrderHandler:
    def __init__(self, order_repository: OrderRepository,cache: OrderQueryCache):
        self.order_repository = order_repository
        self.cache = cache

    async def handle(self, command: CancelOrderCommand) -> Order:
        order = await self.order_repository.find_by_id_and_user_id(
            command.order_id, UserID(command.user_id)
        )
        if order is None:
            raise NotFoundError("订单不存在")

        try:
            order.cancel()
        except OrderStatusError as e:
            raise ConflictError(str(e)) from e

        await self.cache.invalidate(command.user_id)   # 写后失效：版本+1，旧列表缓存全部作废

        return await self.order_repository.update(order)
