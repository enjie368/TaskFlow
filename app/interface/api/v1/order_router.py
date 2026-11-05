'''订单路由'''
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.application.order.commands.cancel_order import CancelOrderCommand, CancelOrderHandler
from app.application.order.commands.create_order import CreateOrderCommand, CreateOrderHandler
from app.application.user.queries.get_orders import GetOrdersHandler, GetOrdersQuery
from app.domain.shared.vo import UserID
from app.interface.dependency import (
    get_cancel_order_handler,
    get_create_order_handler,
    get_order_handler,
)
from app.interface.security import get_current_user_id

router = APIRouter(prefix="/orders", tags=["订单"])

class OrderResponse(BaseModel):
    '''订单响应'''
    id: int
    order_number: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

class GetOrdersResponse(BaseModel):
    '''获取订单响应'''
    orders: list[OrderResponse]
    total: int
    limit: int
    offset: int

class CreateOrderRequest(BaseModel):
    '''下单请求体：只允许客户端提供金额'''
    total_amount: Decimal = Field(
        gt=0,
        le=Decimal("99999999.99"),
        description="订单金额，最多两位小数",
    )

def _to_order_response(order) -> OrderResponse:
    '''实体 / DTO → 响应模型'''
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )

@router.get("/", response_model=GetOrdersResponse,summary="查询我的订单")
async def get_orders(
        limit:int | None=Query(10,ge=1,le=100,description="每页数量"),
        offset:int | None=Query(0,ge=0,description="偏移量"),
        current_user_id: UserID = Depends(get_current_user_id),
        handler:GetOrdersHandler=Depends(get_order_handler)
):
    '''获取当前登录用户的订单列表'''

    query = GetOrdersQuery(user_id=current_user_id.value, limit=limit, offset=offset)
    re=await handler.handle(query)
    return GetOrdersResponse(
        orders=[_to_order_response(order) for order in re.orders],
        total=re.total,
        limit=limit or 10,
        offset=offset or 0,
        )

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="创建订单")
async def create_order(
        payload: CreateOrderRequest,
        current_user_id: UserID = Depends(get_current_user_id),
        handler: CreateOrderHandler = Depends(get_create_order_handler),
):
    '''创建订单：用户身份取自 token，金额取自请求体'''

    order = await handler.handle(
        CreateOrderCommand(
            user_id=current_user_id.value,
            total_amount=payload.total_amount,
         )
     )
    return _to_order_response(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse, summary="取消订单")
async def cancel_order(
        order_id: int,
        current_user_id: UserID = Depends(get_current_user_id),
        handler: CancelOrderHandler = Depends(get_cancel_order_handler),
):
    '''取消当前登录用户自己的待处理订单'''
    order = await handler.handle(
        CancelOrderCommand(order_id=order_id, user_id=current_user_id.value)
    )
    return _to_order_response(order)

