# ===== Dockerfile：把 TaskFlow 应用打包成一个镜像 =====
# 构建：docker build -t taskflow .
# 运行：通常不单独 docker run，而是由 docker-compose.yml 编排（带 MySQL/Redis）

# 基础镜像：slim = 精简版 Debian（约 130MB），只含 Python 运行时
# 不用 alpine：bcrypt/aiomysql 这类带 C 扩展的包在 alpine 上要额外编译，踩坑多
FROM python:3.13-slim

# PYTHONUNBUFFERED=1        让 print/日志实时输出到 docker logs（否则被缓冲看不到）
# PYTHONDONTWRITEBYTECODE=1 不生成 .pyc（容器里没有复用价值，纯占空间）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 容器内工作目录（后面所有相对路径都基于它）
WORKDIR /app

# 【层缓存优化】先只复制依赖清单并安装：
# 只要 requirements.txt 没变，重新 build 时这一层直接用缓存，
# 哪怕业务代码天天改也不用重装几百 MB 的依赖 —— 这是 Dockerfile 最重要的顺序技巧
COPY requirements.txt .
# -i 清华镜像源：国内服务器/CI 直连 pypi.org 龟速甚至超时，换国内源构建从 6 分钟降到 40 秒
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 再复制业务代码（.dockerignore 会排除 .git/测试/__pycache__ 等）
COPY . .

# 声明容器对外提供服务的端口（纯文档作用，真正的映射在 compose 里写）
EXPOSE 8000

# 容器启动命令：0.0.0.0 是关键 —— 容器里的服务必须监听所有网卡，
# 写 127.0.0.1 的话宿主机的端口映射进来也连不上（新手第一大坑）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
