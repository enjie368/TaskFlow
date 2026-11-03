'''认证接口测试：注册 / 登录 / 受保护接口

这一组测试保护的是"账号系统"的三条命脉：
1. 注册能建号，且不把密码泄露回给前端；
2. 登录能发 token，且失败时不告诉别人"到底哪里错了"；
3. 受保护接口必须持有效 token 才放行。
'''

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


async def test_register_success(client):
    '''注册成功：拿到 201 + 返回的用户信息，且响应里不含密码/密文。

    防的 bug：有人图省事把 ORM 对象直接 return，密码哈希就跟着 JSON 泄露了。
    "password" not in body 这一行就是在卡这个。
    用到的夹具（fixture）：client（把请求直接喂给 ASGI 应用，不开服务器）。
    '''
    resp = await client.post(REGISTER, json={"username": "tom", "password": "pass1234"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "tom"
    assert body["user_id"] > 0
    assert "password" not in body          # 响应里绝不能出现密码/密文


async def test_register_duplicate_username(client):
    '''重名注册：同一用户名注册两次，第二次必须被拒（400 + 中文提示）。

    防的 bug：唯一约束只在数据库层报错，接口层没接住，用户会看到 500。
    这里断言的是"400 + 明确的 detail"，说明校验被正确翻译成了业务错误。
    '''
    payload = {"username": "tom", "password": "pass1234"}
    await client.post(REGISTER, json=payload)

    resp = await client.post(REGISTER, json=payload)

    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户名已经存在"


async def test_login_success(client):
    '''登录成功：返回 200 + bearer token，且 token 是标准 JWT。

    JWT 结构是 header.payload.signature 三段，用点分隔，
    所以 len(split(".")) == 3 是"这确实是个 JWT、没被截断"的最低成本检查。
    '''
    await client.post(REGISTER, json={"username": "tom", "password": "pass1234"})

    resp = await client.post(LOGIN, json={"username": "tom", "password": "pass1234"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert len(body["access_token"].split(".")) == 3      # JWT 就是三段


async def test_login_wrong_password(client):
    '''密码错误：必须登录失败（400 + "用户名或密码错误"）。

    与下一条测试合起来看：密码错和用户不存在，对外话术必须**完全一致**，
    否则攻击者就能拿它当"用户名探测器"——试出哪些账号是真实存在的。
    '''
    await client.post(REGISTER, json={"username": "tom", "password": "pass1234"})

    resp = await client.post(LOGIN, json={"username": "tom", "password": "wrong"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户名或密码错误"


async def test_login_user_not_exists(client):
    '''用户不存在：提示语和"密码错误"一模一样，不暴露账号是否存在。

    防的 bug：有人为了"用户体验"改成"该用户不存在，请先注册"，
    这等于把用户枚举（user enumeration）漏洞白送出去。
    '''
    resp = await client.post(LOGIN, json={"username": "nobody", "password": "pass1234"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "用户名或密码错误"       # 不暴露"用户不存在"


async def test_me_without_token(client):
    '''不带 token 访问受保护接口：必须 401 拒绝，而不是 200 或 500。

    注意这里只声明了 client，没有 auth_headers —— 说明这是一个"裸请求"。
    401 = 未认证（Unauthorized），和 403（已认证但没权限）要区分清楚。
    '''
    resp = await client.get(ME)

    assert resp.status_code == 401
    assert resp.json()["detail"] == "未提供访问凭证"


async def test_me_with_token(client, auth_headers):
    '''带有效 token：正常放行，接口按 token 里的身份认出"你是谁"。

    auth_headers 夹具会自动完成"注册 alice + 登录 + 拼好 Authorization 头"，
    所以函数体里看不到任何登录代码，只有一个 get。
    '''
    resp = await client.get(ME, headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["message"] == "已认证"


async def test_me_with_invalid_token(client):
    '''伪造/损坏的 token：必须 401，绝不能被当成合法用户放行。

    "abc.def.ghi" 是三段结构但签名是假的。如果验签逻辑被跳过
    （例如只 decode 不 verify），这条测试就会红——这就是它的价值。
    '''
    resp = await client.get(ME, headers={"Authorization": "Bearer abc.def.ghi"})

    assert resp.status_code == 401
