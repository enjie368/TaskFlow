'''订单接口测试：创建 / 越权隔离 / 分页 / 参数校验

这一组测试保护的是"多用户系统"最容易出事的地方：
1. 谁能下单、下单后状态由谁决定（不能让前端传 status）；
2. 用户 A 绝不能看到用户 B 的订单（越权隔离 / 水平越权）；
3. 分页参数是否真的生效、非法参数是否被拦住。
'''

ORDERS = "/api/v1/orders/"


async def test_create_order_requires_token(client):
    '''未登录下单：必须 401。

    防的 bug：路由上漏写 Depends(get_current_user)，接口裸奔，
    任何人都能往别人账上下单。这条测试只做一件事——确认"门"还在。
    '''
    resp = await client.post(ORDERS, json={"total_amount": 10})

    assert resp.status_code == 401


async def test_create_order_success(client, auth_headers):
    '''登录后下单成功：201 + 服务端生成单号 + 状态固定为"待处理"。

    关键在 status == "待处理"：请求体里只传了 total_amount，
    说明状态是**服务端**决定的。若哪天有人把 status 加进请求模型，
    让前端能直接传"已支付"，这条测试不会马上红——所以还要靠下一步的状态机测试兜住。
    '''
    resp = await client.post(ORDERS, json={"total_amount": 88.5}, headers=auth_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["order_number"].startswith("ORD-")
    assert body["status"] == "待处理"            # 状态只能由服务端决定
    assert float(body["total_amount"]) == 88.5
    assert body["id"] > 0


async def test_create_order_invalid_amount(client, auth_headers):
    '''非法金额（0、负数、超大值）：三个都要被拦成 422。

    用 for 循环把三种坏数据塞进同一个测试，属于"参数化"的手写版。
    422 = 请求体格式合法但取值不合法（Pydantic 校验失败），与 400 的业务错误区分开。
    assert 后面那串 f-string 是失败时的提示语，会直接打印在测试报告里。
    '''
    for bad_amount in (0, -1, 100000000):
        resp = await client.post(ORDERS, json={"total_amount": bad_amount}, headers=auth_headers)
        assert resp.status_code == 422, f"金额 {bad_amount} 应该被拦在接口层"


async def test_list_returns_own_orders_only(client, auth_headers, login_headers):
    '''越权隔离：alice 下 3 单、bob 下 1 单，alice 只能看到自己的 3 单。

    这是整个测试套件里最重要的一条。做法：先用 login_headers("bob")
    造出第二个用户（工厂夹具，要谁就传谁），再回到 alice 的视角查列表。
    两个断言分别管两件事：
      total == 3   → 数量上没串号；
      金额 [30,20,10] → 顺序是"最新在前"，且 bob 的 999 完全没混进来。
    '''
    for amount in (10, 20, 30):
        await client.post(ORDERS, json={"total_amount": amount}, headers=auth_headers)

    bob_headers = await login_headers("bob")
    await client.post(ORDERS, json={"total_amount": 999}, headers=bob_headers)

    resp = await client.get(ORDERS, headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3                                        # bob 的单不算进来
    assert [float(o["total_amount"]) for o in body["orders"]] == [30.0, 20.0, 10.0]   # 最新在前


async def test_list_pagination(client, auth_headers):
    '''分页：共 3 单，取 limit=2 & offset=1 → 返回第 2、3 条（金额 20、10）。

    offset 的含义是"跳过前 N 条"，不是"从第 N 条开始"，所以跳 1 条后从 20 开始。
    total 仍是 3 —— 它表示总数，不随分页变小；前端靠它算总页数。
    若把 offset 误实现成页码，这里拿到的会是 [10, 20]，测试立刻红。
    '''
    for amount in (10, 20, 30):
        await client.post(ORDERS, json={"total_amount": amount}, headers=auth_headers)

    resp = await client.get(ORDERS, params={"limit": 2, "offset": 1}, headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3                     # total 是总数，不随分页变小
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert [float(o["total_amount"]) for o in body["orders"]] == [20.0, 10.0]


async def test_list_invalid_pagination(client, auth_headers):
    '''非法分页参数（limit=0）：必须 422。

    limit=0 会变成"查 0 条"，看起来无害，实则是开发者传错参数时最难查的一类 bug：
    接口返回 200 + 空列表，前端以为"这用户没订单"。所以要在入口拦住。
    '''
    resp = await client.get(ORDERS, params={"limit": 0}, headers=auth_headers)

    assert resp.status_code == 422


async def test_new_user_sees_empty_list(client, login_headers):
    '''全新用户 carol 的订单列表：200 + total=0 + orders=[]。

    防的是"空结果报 500"和"空结果返 null"两种常见坑：
    空列表必须是 []，前端才能安全地 .map()；如果是 null 就会白屏。
    另外注意 carol 是新用户，说明这个测试没有依赖 alice/bob 留下的数据。
    '''
    headers = await login_headers("carol")

    resp = await client.get(ORDERS, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["orders"] == []


async def _create_order(client, headers, amount: float = 10.0) -> int:
    '''建一张单，返回 id；后面取消都要先有单'''
    resp = await client.post(ORDERS, json={"total_amount": amount}, headers=headers)
    assert resp.status_code == 201          # 建单失败就没必要往下测
    return resp.json()["id"]


async def test_cancel_order_success(client, auth_headers):
    '''取消自己的待处理订单：200，且状态真的变成「已取消」'''
    order_id = await _create_order(client, auth_headers)
    resp = await client.post(f"{ORDERS}{order_id}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "已取消"
    assert body["id"] == order_id


async def test_cancel_twice_returns_409(client, auth_headers):
    '''重复取消必须被拦住：第二次 409，而不是静默成功'''
    order_id = await _create_order(client, auth_headers)
    first = await client.post(f"{ORDERS}{order_id}/cancel", headers=auth_headers)
    assert first.status_code == 200
    second = await client.post(f"{ORDERS}{order_id}/cancel", headers=auth_headers)
    assert second.status_code == 409
    assert "已取消" in second.json()["detail"]


async def test_cancel_others_order_returns_404(client, auth_headers, login_headers):
    '''越权取消：bob 拿 alice 的单号去取消，必须 404（不是 403）'''
    order_id = await _create_order(client, auth_headers)
    bob_headers = await login_headers("bob")
    resp = await client.post(f"{ORDERS}{order_id}/cancel", headers=bob_headers)
    assert resp.status_code == 404


async def test_cancel_not_exist_returns_404(client, auth_headers):
    '''取消不存在的订单：404'''
    resp = await client.post(f"{ORDERS}999999/cancel", headers=auth_headers)
    assert resp.status_code == 404


async def test_cancel_requires_token(client):
    '''不带 token 取消：401，说明拦在认证层而不是业务层'''
    resp = await client.post(f"{ORDERS}1/cancel")
    assert resp.status_code == 401
