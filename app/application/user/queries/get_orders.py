'''
订单查询
'''
import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import List

from app.application.common.exception import ValidationError
from app.application.common.order_query_cache import OrderQueryCache
from app.domain.order.repository import OrderRepository
from app.domain.shared.vo import UserID


@dataclass
class GetOrdersQuery:
    '''获取用户订单查询'''
    user_id: int
    limit: int=10
    offset: int=0

@dataclass
class OrderDTO:
    '''获取数据传输对象'''
    id: int
    order_number: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

@dataclass
class GetOrdersResult:
    """获取用户订单结果"""
    total: int
    orders: List[OrderDTO]

class GetOrdersHandler:
    '''获取订单查询处理器'''
    def __init__(self,order_repository: OrderRepository,cache: OrderQueryCache):
        self.order_repository = order_repository
        self.cache = cache

    async def handle(self,query: GetOrdersQuery) -> GetOrdersResult:
        '''处理获取用户订单查询'''
        if query.user_id <= 0:
            raise ValidationError("用户id必须大于0")
        if query.limit <= 0 or query.limit > 100:
            raise ValidationError("限制数量必读大于0且小于100")
        if query.offset < 0:
            raise ValidationError("偏移不能为负数")

        cached = await self.cache.get(query.user_id, query.limit, query.offset)
        if cached is not None:
            return cached

        user_id = UserID(query.user_id)
        orders = await self.order_repository.find_by_user_id(user_id, query.limit, query.offset)
        total = await self.order_repository.count_by_user_id(user_id)


        result = GetOrdersResult(total=total, orders=[
            OrderDTO(
                id=o.id,order_number=o.order_number,total_amount=o.total_amount,
                status=o.status,created_at=o.created_at,updated_at=o.updated_at
            )
            for o in orders
        ])

        await self.cache.save(query.user_id, query.limit, query.offset, result)
        return result


