'''
实体与ORM的映射器
'''
from ..database.orm_models import UserORM, OrderORM
from app.domain.user.entity import User
from app.domain.shared.vo import UserID
from ...domain.order.entity import Order


class UserMapper:
    '''用户映射器'''
    @staticmethod
    def to_entity(orm_model:UserORM):
        '''将ORM对象转换为实体对象'''
        return User(
            id=UserID(orm_model.id),
            name=orm_model.username,
            password=orm_model.password,
        )

    @staticmethod
    def to_orm(user:User):
        '''将实体对象转换为ORM对象'''
        orm_model = UserORM()
        if user.id:
            orm_model.id = user.id.value
        orm_model.username = user.name
        orm_model.password = user.password
        return orm_model

class OrderMapper:
    @staticmethod
    def to_entity(orm_model: OrderORM) -> Order:
        return Order(
            id=orm_model.id,
            order_number=orm_model.order_number,
            user_id=UserID(orm_model.user_id),
            total_amount=orm_model.total_amount,
            status=orm_model.status,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    @staticmethod
    def to_orm(order: Order) -> OrderORM:
        orm_model = OrderORM()
        if order.id:
            orm_model.id = order.id
        orm_model.order_number = order.order_number
        orm_model.user_id = order.user_id.value
        orm_model.total_amount = order.total_amount
        orm_model.status = order.status
        return orm_model




