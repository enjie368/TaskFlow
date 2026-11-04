'''
依赖注入模块
'''

from fastapi import Depends

from app.application.order.commands.cancel_order import CancelOrderHandler
from app.application.order.commands.create_order import CreateOrderHandler
from app.application.user.commands.login_user import LoginUserHandler
from app.application.user.commands.register_user import RegisterUserHandler
from app.application.user.queries.get_orders import GetOrdersHandler
from app.domain.order.repository import OrderRepository
from app.domain.user.repository import UserRepository
from app.infrastructure.repository.order_impl import OrderRepositoryImpl
from app.infrastructure.repository.user_impl import UserRepositoryImpl
from app.domain.user.password_hasher import PasswordHasher
from app.application.common.token_service import TokenService
from app.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher
from app.infrastructure.security.jwt_service import JwtTokenService
from config.settings import settings
from redis.asyncio import Redis
from app.infrastructure.cache.redis_guard import RedisLoginAttemptGuard
from app.application.common.login_guard import LoginAttemptGuard

def get_password_hasher() -> PasswordHasher:
    '''获取密码哈希'''
    return BcryptPasswordHasher()


def get_token_service() -> TokenService:
    '''获取token'''
    return JwtTokenService(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.access_token_expire_minutes,
    )


def get_user_repository()->UserRepository:
    '''获取用户仓储'''
    return UserRepositoryImpl()

def get_register_user_handler(
        user_repository: UserRepository=Depends(get_user_repository),
        hasher:PasswordHasher=Depends(get_password_hasher),
        )->RegisterUserHandler:
    '''获取注册用户处理器'''
    return RegisterUserHandler(user_repository, hasher)

def get_login_attempt_guard() -> LoginAttemptGuard:
    return RedisLoginAttemptGuard(Redis.from_url(settings.redis_url))

def get_login_user_handler(
        user_repository: UserRepository=Depends(get_user_repository),
        hasher:PasswordHasher=Depends(get_password_hasher),
        token_service:TokenService=Depends(get_token_service),
        guard:LoginAttemptGuard = Depends(get_login_attempt_guard),
        )->LoginUserHandler:
    '''获取登录用户处理器'''
    return LoginUserHandler(user_repository,hasher,token_service,guard)

def get_order_repository()->OrderRepository:
    '''获取订单仓储'''
    return OrderRepositoryImpl()

def get_order_handler(
    order_repository: OrderRepository = Depends(get_order_repository)
)->GetOrdersHandler:
    '''获取订单处理器'''
    return GetOrdersHandler(order_repository)

def get_create_order_handler(
    order_repository: OrderRepository = Depends(get_order_repository),
) -> CreateOrderHandler:
    '''获取创建订单处理器'''
    return CreateOrderHandler(order_repository)

def get_cancel_order_handler(
    order_repository: OrderRepository = Depends(get_order_repository),
) -> CancelOrderHandler:
    '''获取取消订单处理器'''
    return CancelOrderHandler(order_repository)



