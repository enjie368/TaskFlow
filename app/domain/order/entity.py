'''订单实体'''
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from ..shared.vo import UserID


class OrderStatus(StrEnum):
    '''订单状态：值仍是中文，但拼错会立刻报错'''
    PENDING = "待处理"
    PAID = "已支付"
    CANCELLED = "已取消"


class OrderStatusError(Exception):
    '''订单当前状态不允许这个操作（领域层自己的异常）'''


@dataclass
class Order:
    id: int | None
    order_number: str
    user_id: UserID
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        if not self.order_number:
            raise ValueError("订单号不能为空")
        if self.total_amount < 0:
            raise ValueError("订单金额不能为负")

    @classmethod
    def create(cls, user_id: UserID, total_amount: Decimal) -> "Order":
        '''新建订单：订单号与初始状态由领域自己决定'''
        now = datetime.now()
        return cls(
            id=None,
            order_number=f"ORD-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            total_amount=total_amount.quantize(Decimal("0.01")),
            status=OrderStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def cancel(self) -> None:
        '''取消订单：只有待处理可以取消，规则写在实体里'''
        if self.status == OrderStatus.CANCELLED:
            raise OrderStatusError("订单已取消，不能重复取消")
        if self.status != OrderStatus.PENDING:
            raise OrderStatusError(f"订单当前状态为「{self.status}」，不能取消")
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
