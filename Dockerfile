# 使用官方 Python 3.11 作為基礎映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（如果需要）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 文件
COPY requirement.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirement.txt

# 複製應用程式代碼
COPY . .

# 暴露 FastAPI 預設端口（通常為 8000）
EXPOSE 8000

# 啟動 FastAPI 應用程式
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
