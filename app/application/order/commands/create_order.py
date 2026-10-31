'''创建订单'''
from dataclasses import dataclass
from decimal import Decimal

from app.application.common.exception import ValidationError
from app.domain.order.entity import Order
from app.domain.order.repository import OrderRepository
from app.domain.shared.vo import UserID


@dataclass
class CreateOrderCommand:
    user_id: int
    total_amount: Decimal


class CreateOrderHandler:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def handle(self, command: CreateOrderCommand) -> Order:
        if command.user_id <= 0:
            raise ValidationError("用户id必须大于0")

        amount = Decimal(str(command.total_amount))
        if amount <= 0:
            raise ValidationError("订单金额必须大于0")

        order = Order.create(UserID(command.user_id), amount)
        return await self.order_repository.add(order)
