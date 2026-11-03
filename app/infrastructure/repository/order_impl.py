from typing import Optional

from app.domain.order.entity import Order
from app.domain.order.repository import OrderRepository
from app.domain.shared.vo import UserID
from app.infrastructure.database.mappers import OrderMapper
from app.infrastructure.database.orm_models import OrderORM


class OrderRepositoryImpl(OrderRepository):
    async def find_by_user_id(self, user_id: UserID, limit: int, offset: int) -> list[Order]:
        '''按用户查订单'''
        orm_models = await OrderORM.filter(user_id=user_id.value).offset(offset).limit(limit)
        return [OrderMapper.to_entity(m) for m in orm_models]

    async def count_by_user_id(self, user_id: UserID) -> int:
        '''统计用户订单总数'''
        return await OrderORM.filter(user_id=user_id.value).count()

    async def add(self, order: Order) -> Order:
        '''增加订单，返回落库后的实体'''
        orm_model = OrderMapper.to_orm(order)
        await orm_model.save()
        return OrderMapper.to_entity(orm_model)

    async def find_by_id_and_user_id(self, order_id: int, user_id: UserID) -> Optional[Order]:
        '''按 id 查订单，且必须属于该用户；不存在或不是本人的都返回 None'''
        orm_model = await OrderORM.get_or_none(id=order_id, user_id=user_id.value)
        if orm_model is None:
            return None
        return OrderMapper.to_entity(orm_model)

    async def update(self, order: Order) -> Order:
        '''把实体的变更写回数据库'''
        orm_model = await OrderORM.get(id=order.id)
        orm_model.status = order.status
        await orm_model.save(update_fields=["status", "updated_at"])
        return OrderMapper.to_entity(orm_model)


