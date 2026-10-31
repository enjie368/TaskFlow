'''
用户登录命令模块
'''
from dataclasses import dataclass

from app.application.common.exception import AuthError
from app.application.common.token_service import TokenService
from app.domain.user.password_hasher import PasswordHasher
from app.domain.user.repository import UserRepository


@dataclass
class LoginUserCommand:
    '''用户登录命令'''
    username: str
    password: str

@dataclass
class LoginUserResult:
    '''用户登录结果'''
    user_id: int
    username: str
    access_token: str
    expires_in: int

class LoginUserHandler:
    '''用户登录命令处理器'''
    def __init__(self, user_repository: UserRepository,password_hasher:PasswordHasher,token_service:TokenService) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def handle(self, command:LoginUserCommand)->LoginUserResult:
        '''处理用户登录命令'''
        if not command.username:
            raise ValueError("用户名不能为空")

        if not command.password:
            raise ValueError("密码不能为空")

        #查找用户
        user=await self.user_repository.find_by_name(command.username)
        if not user or not self.password_hasher.verify(command.password,user.password ):
            raise AuthError("用户名或密码错误")

        access_token,expires_in=self.token_service.create_access_token(user.id.value,user.name)
        return LoginUserResult(
            user_id=user.id.value,
            username=user.name,
            access_token=access_token,
            expires_in=expires_in
        )