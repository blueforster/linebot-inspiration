FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 複製 requirements 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 建立必要目錄並設定權限
RUN mkdir -p config logs backups && \
    chown -R appuser:appuser /app

# 切換到非 root 使用者
USER appuser

# 暴露端口
EXPOSE 5000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# 啟動命令
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]