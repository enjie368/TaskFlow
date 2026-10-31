'''
orm模型
'''

from tortoise import fields
from tortoise.models import Model

class UserORM(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password = fields.CharField(max_length=255)

    class Meta:
        table = "users"

class OrderORM(Model):
    '''订单表'''
    id = fields.IntField(pk=True)
    order_number = fields.CharField(max_length=32, unique=True, description="订单号")
    user_id = fields.IntField(index=True, description="所属用户id")
    total_amount = fields.DecimalField(max_digits=10, decimal_places=2, description="订单金额")
    status = fields.CharField(max_length=20, default="待处理", description="订单状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "orders"
        ordering = ["-created_at"]     # 默认按创建时间倒序，列表接口天然“最新在前”
        indexes = [("user_id", "status")]   # 联合索引：查"我的待处理订单"这种高频条件
