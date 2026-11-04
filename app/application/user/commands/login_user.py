'''
用户登录命令模块
'''
from dataclasses import dataclass

from app.application.common.exception import AuthError
from app.application.common.login_guard import LoginAttemptGuard
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
    def __init__(self, user_repository: UserRepository,password_hasher:PasswordHasher,token_service:TokenService,guard: LoginAttemptGuard) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.guard = guard

    async def handle(self, command:LoginUserCommand)->LoginUserResult:
        '''处理用户登录命令

        限流埋点：
        ① 进门先看锁（ensure_allowed，被锁抛 RateLimitError → 429）
        ② try 圈住"真正可能登录失败"的代码，AuthError 时记账后重新抛出
        ③ 只有成功才走到 reset 清零（失败路径 raise 后到不了这里）
        '''
        await self.guard.ensure_allowed(command.username)
        try:
            # 查找用户并校验密码——这才是"可能登录失败"的部分
            user=await self.user_repository.find_by_name(command.username)
            if not user or not self.password_hasher.verify(command.password,user.password ):
                raise AuthError("用户名或密码错误")
        except AuthError:
            await self.guard.record_failure(command.username)
            raise
        await self.guard.reset(command.username)

        access_token,expires_in=self.token_service.create_access_token(user.id.value,user.name)
        return LoginUserResult(
            user_id=user.id.value,
            username=user.name,
            access_token=access_token,
            expires_in=expires_in
        )