from app.domain.order.entity import Order
from app.domain.order.repository import OrderRepository
from app.domain.shared.vo import UserID
from app.infrastruture.database.mappers import OrderMapper
from app.infrastruture.database.orm_models import OrderORM


class OrderRepositoryImpl(OrderRepository):
    async def find_by_user_id(self, user_id: UserID, limit: int, offset: int) -> list[Order]:
        orm_models = await OrderORM.filter(user_id=user_id.value).offset(offset).limit(limit)
        return [OrderMapper.to_entity(m) for m in orm_models]

    async def count_by_user_id(self, user_id: UserID) -> int:
        return await OrderORM.filter(user_id=user_id.value).count()

    async def add(self, order: Order) -> Order:
        orm_model = OrderMapper.to_orm(order)
        await orm_model.save()
        return OrderMapper.to_entity(orm_model)

