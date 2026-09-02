# 论匠后端容器镜像：多实例部署载体（R13）
# 说明：
#   - 语言/推理栈较重（sentence-transformers → torch CPU），首次构建耗时较长；
#   - 父子镜像 python:3.12-slim 内置无 curl，健康检查用 urllib 拉取 /health；
#   - 运行期嵌入/精排为 CPU 线程池推理，容器内依赖运行时预加载（同态在 main.py lifespan）。
#   构建：  docker build -t lunjiang-app:local .
#   运行：  docker compose up -d --scale app=2   （或其他副本数）
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=0

WORKDIR /app

# torch CPU 运行所需最小系统库（不含编译工具链，减小镜像体积）
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 依赖层缓存：requirements 不变时复用镜像层
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 非 root 运行（安全基线）
RUN useradd --create-home --uid 1000 lunjiang && \
    mkdir -p /app/data/uploads && \
    chown -R lunjiang:lunjiang /app
USER lunjiang

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD ["python", "-c", "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]