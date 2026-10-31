from dataclasses import dataclass
from app.application.common.exception import DuplicateError,ValidationError
from app.domain.user.entity import User
from app.domain.user.repository import UserRepository
from app.domain.user.password_hasher import PasswordHasher

@dataclass
class RegisterUserCommand:
    '''用户注册命令'''
    username: str
    password: str

@dataclass
class RegisterUserResult:
    '''用户注册结果'''
    user_id: int
    username: str

class RegisterUserHandler:
    '''用户注册处理器'''
    def __init__(self, user_repository: UserRepository,password_hasher: PasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def handle(self, command: RegisterUserCommand) -> RegisterUserResult:
        '''处理用户注册'''
        #验证
        if not command.username:
            raise ValidationError("用户名不能为空")
        if not command.password:
            raise ValidationError("密码不能为空")
        if await self.user_repository.exist_by_name(command.username):
            raise DuplicateError("用户名已经存在")
        #创建用户实体
        user=User(
            id=None,
            name=command.username,
            password=self.password_hasher.hash(command.password)
        )
        #保存用户
        saved_user=await self.user_repository.save(user)
        return RegisterUserResult(
            user_id=saved_user.id.value,
            username=saved_user.name
        )