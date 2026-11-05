'''CancelOrderHandler 单元测试

单测与集成测试的分工：
- 集成测试（test_order.py）：走 HTTP + 真仓储，验证"接线"对不对
- 单元测试（本文件）：直接 new Handler + 内存假仓储，验证"业务逻辑"对不对
  不起服务、不连库、不需要 Docker，毫秒级跑完
'''
from datetime import datetime
from decimal import Decimal

import pytest

from app.application.common.exception import ConflictError, NotFoundError
from app.application.order.commands.cancel_order import CancelOrderCommand, CancelOrderHandler
from app.domain.order.entity import Order, OrderStatus
from app.domain.shared.vo import UserID


def _make_order(order_id: int, status: str) -> Order:
    '''造一个测试订单：参数只留"影响断言结果"的两项（id、状态），其余给合法默认值'''
    return Order(
        id=order_id,
        order_number=f"ORD-TEST-{order_id}",
        user_id=UserID(4),
        total_amount=Decimal("9.90"),
        status=status,
        created_at=datetime(2026, 11, 5, 12, 0, 0),
        updated_at=datetime(2026, 11, 5, 12, 0, 0),
    )


class FakeOrderRepository:
    '''内存假仓储：替身的关键是"记住发生了什么"，供断言检查'''

    def __init__(self, existing_orders: list[Order]):
        self._orders = {o.id: o for o in existing_orders}   # 用 id 建索引方便查找
        self.update_called_with = None                      # 记录 update 收到的对象

    async def find_by_id_and_user_id(self, order_id: int, user_id: UserID):
        '''按 id 取订单（单测里不校验 user_id 归属，那是集成测试的事）'''
        return self._orders.get(order_id)

    async def update(self, order: Order) -> Order:
        '''记录"被保存的订单"，假装存进了库'''
        self.update_called_with = order
        return order


class FakeCache:
    '''空操作缓存：单测只关心业务逻辑，invalidate 被没被调可以记一笔'''

    def __init__(self):
        self.invalidate_called = 0

    async def get(self, user_id, limit, offset):
        return None

    async def save(self, user_id, limit, offset, result):
        pass

    async def invalidate(self, user_id):
        self.invalidate_called += 1


def _make_handler(orders: list[Order]):
    '''组装被测对象：真 Handler + 两个假依赖——这就是"手动依赖注入"'''
    repo = FakeOrderRepository(orders)
    cache = FakeCache()
    return CancelOrderHandler(repo, cache), repo, cache


# ---------- 四条核心用例，每条一个 3A 结构 ----------

async def test_取消成功_状态变已取消():
    '''待处理订单取消后：状态变已取消，且被保存、缓存被失效'''
    handler, repo, cache = _make_handler([_make_order(1, OrderStatus.PENDING)])

    order = await handler.handle(CancelOrderCommand(order_id=1, user_id=4))   # Act

    assert order.status == OrderStatus.CANCELLED                              # Assert
    assert repo.update_called_with is not None      # 确实发起过保存
    assert cache.invalidate_called == 1             # 写后失效被调了一次


async def test_订单不存在_抛NotFoundError():
    handler, _, _ = _make_handler([])               # 仓储里空空如也

    with pytest.raises(NotFoundError):
        await handler.handle(CancelOrderCommand(order_id=999, user_id=4))


async def test_重复取消_抛ConflictError():
    handler, _, _ = _make_handler([_make_order(1, OrderStatus.CANCELLED)])

    with pytest.raises(ConflictError):
        await handler.handle(CancelOrderCommand(order_id=1, user_id=4))


async def test_已支付订单_抛ConflictError():
    handler, _, _ = _make_handler([_make_order(1, OrderStatus.PAID)])

    with pytest.raises(ConflictError):
        await handler.handle(CancelOrderCommand(order_id=1, user_id=4))
