'''
认证和路由
'''

from fastapi import APIRouter, status, HTTPException,Depends
from pydantic import BaseModel

from app.application.common.exception import DomainException
from app.application.user.commands.login_user import LoginUserHandler, LoginUserCommand
from app.application.user.commands.register_user import RegisterUserCommand,RegisterUserHandler
from app.domain.shared.vo import UserID
from app.interface.dependency import get_register_user_handler, get_login_user_handler
from app.interface.security import get_current_user_id

router = APIRouter(prefix="/auth", tags=["认证"])

class RegisterRequest(BaseModel):
    '''注册请求'''
    username: str
    password: str

class RegisterResponse(BaseModel):
    '''注册响应'''
    username: str
    user_id: int
    message: str

class LoginRequest(BaseModel):
    '''登录请求'''
    username: str
    password: str

class LoginResponse(BaseModel):
    '''登录响应'''
    username: str
    user_id: int
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    message: str

class MeResponse(BaseModel):
    user_id: int
    message: str

@router.post("/register", response_model=RegisterResponse,status_code=status.HTTP_201_CREATED)
async def register_user(
        request: RegisterRequest,
        handler:RegisterUserHandler = Depends(get_register_user_handler)
):
    '''用户注册接口'''
    command=RegisterUserCommand(
    username=request.username,
    password=request.password
    )
    result=await handler.handle(command)
    return RegisterResponse(
        username=result.username,
        user_id=result.user_id,
        message="用户注册成功"
    )

@router.post("/login", response_model=LoginResponse,status_code=status.HTTP_200_OK)
async def login_user(
        request: LoginRequest,
        handler:LoginUserHandler=Depends(get_login_user_handler)
):
    '''用户登录接口'''
    command=LoginUserCommand(
        username=request.username,
        password=request.password
        )
    result=await handler.handle(command)
    return LoginResponse(
        username=result.username,
        user_id=result.user_id,
        access_token=result.access_token,
        expires_in=result.expires_in,
        message="用户登录成功"
        )

@router.get("/me", response_model=MeResponse)
async def me(current_user_id: UserID = Depends(get_current_user_id)):
    '''受保护接口：必须带 Bearer token'''
    return MeResponse(user_id=current_user_id.value, message="已认证")