'''
共享值对象定义模板
'''
from dataclasses import dataclass

@dataclass(frozen=True)#datacalss会自动实现__init__和__eq__，frozen=True使实例不可变
class UserID:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("用户ID不能小于0")
