'''订单实体'''
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..shared.vo import UserID


@dataclass
class Order:
    id: Optional[int]
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
            status="待处理",
            created_at=now,
            updated_at=now,
        )