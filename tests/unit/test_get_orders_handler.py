'''GetOrdersHandler 单元测试

覆盖目标（来自 coverage 报告的 4 个盲区）：
- 47/49/51 行：三个参数校验分支从没被触发过
- 55 行：缓存命中路径（return cached）从未被执行——重点补测
'''
from datetime import datetime
from decimal import Decimal

import pytest

from app.application.common.exception import ValidationError
from app.application.user.queries.get_orders import (
    GetOrdersHandler,
    GetOrdersQuery,
    GetOrdersResult,
    OrderDTO,
)
from app.domain.shared.vo import UserID


def _make_result() -> GetOrdersResult:
    '''造一份查询结果：作为"缓存里预存的内容"，供命中测试使用'''
    return GetOrdersResult(
        total=1,
        orders=[
            OrderDTO(
                id=1,
                order_number="ORD-TEST-1",
                total_amount=Decimal("9.90"),
                status="待处理",
                created_at=datetime(2026, 11, 5, 12, 0, 0),
                updated_at=datetime(2026, 11, 5, 12, 0, 0),
            )
        ],
    )


class FakeOrderRepository:
    '''内存假仓储：不连库，只记账——被调过几次、该返回什么全由测试控制'''

    def __init__(self):
        self.find_called = 0        # find_by_user_id 被调次数（穿透指标）
        self.count_called = 0       # count_by_user_id 被调次数

    async def find_by_user_id(self, user_id: UserID, limit: int, offset: int):
        '''假装查库：返回空列表（本文件不关心内容，只关心"调没调"）'''
        self.find_called += 1
        return []

    async def count_by_user_id(self, user_id: UserID) -> int:
        '''假装数总数'''
        self.count_called += 1
        return 0


class FakeCache:
    '''可预设返回值的假缓存：preset 非空时模拟"缓存命中"'''

    def __init__(self, preset: GetOrdersResult | None = None):
        self.preset = preset        # 预设的命中结果（None = 模拟未命中）
        self.save_called = 0        # save 被调次数（回填指标）

    async def get(self, user_id, limit, offset):
        '''命中则返回预设结果，未命中返回 None'''
        return self.preset

    async def save(self, user_id, limit, offset, result):
        '''记账：回填发生过'''
        self.save_called += 1

    async def invalidate(self, user_id):
        '''本文件的用例都是读操作，用不到失效'''

    # ---------- 参数校验分支（覆盖 47/49/51 行） ----------


async def test_user_id非法_抛ValidationError():
    '''user_id <= 0 直接拒绝，不该摸缓存也不该查库'''
    repo, cache = FakeOrderRepository(), FakeCache()
    handler = GetOrdersHandler(repo, cache)

    with pytest.raises(ValidationError):
        await handler.handle(GetOrdersQuery(user_id=0))

    assert repo.find_called == 0     # 校验失败必须拦在查库之前


async def test_limit越界_抛ValidationError():
    '''limit=0 或超过 100 都非法（49 行的 or 两个分支）'''
    repo, cache = FakeOrderRepository(), FakeCache()
    handler = GetOrdersHandler(repo, cache)

    with pytest.raises(ValidationError):
        await handler.handle(GetOrdersQuery(user_id=4, limit=0))
    with pytest.raises(ValidationError):
        await handler.handle(GetOrdersQuery(user_id=4, limit=101))


async def test_offset为负_抛ValidationError():
    '''offset < 0 拒绝（分页没有"往回翻"）'''
    repo, cache = FakeOrderRepository(), FakeCache()
    handler = GetOrdersHandler(repo, cache)

    with pytest.raises(ValidationError):
        await handler.handle(GetOrdersQuery(user_id=4, offset=-1))


# ---------- 缓存命中/未命中两条主路径（覆盖 55 行） ----------


async def test_缓存命中_直接返回不查库():
    '''命中时：原样返回缓存对象，仓储一次都不该被调，也不该回填'''
    preset = _make_result()
    repo = FakeOrderRepository()
    cache = FakeCache(preset=preset)                 # 预设 → 模拟 60 秒内第二次查询
    handler = GetOrdersHandler(repo, cache)

    result = await handler.handle(GetOrdersQuery(user_id=4))

    assert result is preset                          # 同一个对象（不是查库新造的副本）
    assert repo.find_called == 0                     # 没穿透到仓储
    assert repo.count_called == 0
    assert cache.save_called == 0                    # 命中路径不做回填


async def test_缓存未命中_查库并回填():
    '''未命中时：查库两次（分页数据+总数），结果回填缓存供下次用'''
    repo = FakeOrderRepository()
    cache = FakeCache(preset=None)                   # 未命中 → 走真实查库路径
    handler = GetOrdersHandler(repo, cache)

    result = await handler.handle(GetOrdersQuery(user_id=4))

    assert repo.find_called == 1                     # 查了一次分页数据
    assert repo.count_called == 1                    # 查了一次总数
    assert cache.save_called == 1                    # 回填发生过
    assert isinstance(result, GetOrdersResult)
