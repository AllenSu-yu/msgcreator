# Docker 部署指南

本指南將教您如何使用 Docker 將應用程式部署到 AWS EC2 實例。

## 📋 部署流程概覽

根據流程圖，Docker 部署分為三個階段：
1. **本地機器 (Local Machine)**: 構建 Docker 映像檔
2. **Docker Hub**: 推送映像檔到 Docker Hub
3. **EC2 實例**: 從 Docker Hub 拉取並運行容器

---

## 🚀 步驟 1: 本地準備

### 1.1 確保已安裝 Docker

在本地機器上確認 Docker 已安裝：
```bash
docker --version
```

如果未安裝，請前往 [Docker 官網](https://www.docker.com/get-started) 下載安裝。

### 1.2 構建 Docker 映像檔

在專案根目錄執行以下命令：

```bash
# 構建映像檔（請替換 YOUR_DOCKERHUB_USERNAME 為您的 Docker Hub 用戶名）
docker build -t YOUR_DOCKERHUB_USERNAME/msgcreator:latest .
docker build -t Hueiyu/msgcreator:latest .
```

範例：
```bash
docker build -t myusername/msgcreator:latest .
```

### 1.3 本地測試（可選）

在推送之前，可以先在本地測試：

```bash
# 運行容器（確保 .env 文件存在）
docker run -d -p 8000:8000 --env-file .env --name msgcreator-test YOUR_DOCKERHUB_USERNAME/msgcreator:latest
docker run -d -p 8000:8000 --env-file .env --name msgcreator-test Hueiyu/msgcreator:latest

# 測試應用程式
# 瀏覽器開啟 http://localhost:8000

# 停止並刪除測試容器
docker stop msgcreator-test
docker rm msgcreator-test
```

---

## 📤 步驟 2: 推送到 Docker Hub

### 2.1 登入 Docker Hub

```bash
docker login
```

輸入您的 Docker Hub 用戶名和密碼。

### 2.2 推送映像檔

```bash
docker push YOUR_DOCKERHUB_USERNAME/msgcreator:latest
docker push Hueiyu/msgcreator:latest
```

---

## 🖥️ 步驟 3: 在 EC2 實例上部署

### 3.1 連接到 EC2 實例

使用 SSH 連接到您的 EC2 實例：

**Amazon Linux / Amazon Linux 2:**
```bash
ssh -i msgcreator.pem ec2-user@YOUR_EC2_IP
```

**Ubuntu:**
```bash
ssh -i msgcreator.pem ubuntu@YOUR_EC2_IP
```

### 3.2 在 EC2 上安裝 Docker

如果 EC2 實例尚未安裝 Docker，請根據您的作業系統選擇對應的安裝方式：

#### Amazon Linux / Amazon Linux 2

```bash
# 更新系統套件
sudo yum update -y

# 安裝 Docker
sudo yum install docker -y

# 啟動 Docker 服務
sudo systemctl start docker
sudo systemctl enable docker

# 將當前用戶加入 docker 群組（避免每次都用 sudo）
sudo usermod -aG docker ec2-user

# 登出並重新登入以套用群組變更
exit
```

重新登入後：
```bash
ssh -i msgcreator.pem ec2-user@YOUR_EC2_IP
```

#### Ubuntu

**方式一：使用官方安裝腳本（推薦）**

```bash
# 使用 Docker 官方提供的簡化安裝腳本
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 將當前用戶加入 docker 群組（避免每次都用 sudo）
sudo usermod -aG docker ubuntu

# 登出並重新登入以套用群組變更
exit
```

重新登入後：
```bash
ssh -i msgcreator.pem ubuntu@YOUR_EC2_IP
```

**方式二：手動安裝（進階）**

```bash
# 更新系統套件
sudo apt update

# 安裝必要的套件
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 添加 Docker 官方 GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新套件列表
sudo apt update

# 安裝 Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 啟動 Docker 服務
sudo systemctl start docker
sudo systemctl enable docker

# 將當前用戶加入 docker 群組（避免每次都用 sudo）
sudo usermod -aG docker ubuntu

# 登出並重新登入以套用群組變更
exit
```

重新登入後：
```bash
ssh -i msgcreator.pem ubuntu@YOUR_EC2_IP
```

**驗證 Docker 安裝（兩種系統都適用）：**
```bash
docker --version
docker ps
```

### 3.3 登入 Docker Hub（在 EC2 上）

```bash
docker login
```

### 3.4 拉取映像檔

```bash
docker pull YOUR_DOCKERHUB_USERNAME/msgcreator:latest
docker pull hueiyu/msgcreator:latest
```

### 3.5 創建環境變數文件

在 EC2 實例上創建 `.env` 文件：

```bash
# 創建應用程式目錄
mkdir -p ~/msgcreator
cd ~/msgcreator

# 創建 .env 文件
nano .env
```

將以下內容貼上（請根據您的實際設定修改）：
```
DB_HOST=db-msgcreator.ctamgak26co2.ap-northeast-1.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=25DxrHV.H!sjeSd
DB_NAME=msgcreator
DB_PORT=3306

CLOUDFRONT_DOMAIN=d1lpoag57byp2r.cloudfront.net
```

按 `Ctrl+X`，然後 `Y`，最後 `Enter` 儲存。

### 3.6 運行容器

#### 方式一：使用 Docker Compose（推薦，包含 Nginx）

如果您使用 `docker-compose.yml`，可以這樣運行：

```bash
# 確保在專案目錄中
cd ~/msgcreator

# 上傳 nginx 配置文件到 EC2（如果還沒有）
# 確保 nginx/nginx.conf 文件存在

# 使用 docker-compose 啟動所有服務（包括 Nginx）
docker-compose up -d

# 檢查服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f

# 查看特定服務的日誌
docker-compose logs -f app
docker-compose logs -f nginx
```

#### 方式二：手動運行容器（包含 Nginx）

```bash
# 創建網路
docker network create app-network

# 運行應用程式容器（不直接暴露端口）
docker run -d \
  --name msgcreator-app \
  --network app-network \
  --env-file .env \
  --restart unless-stopped \
  hueiyu/msgcreator:latest

# 運行 Nginx 容器
docker run -d \
  --name msgcreator-nginx \
  --network app-network \
  -p 80:80 \
  -v $(pwd)/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v $(pwd)/static:/app/static:ro \
  --restart unless-stopped \
  nginx:alpine
```

#### 方式三：僅運行應用程式（不使用 Nginx）

如果您不想使用 Nginx，可以繼續使用舊的方式：

```bash
docker run -d \
  --name msgcreator \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  hueiyu/msgcreator:latest
```

### 3.7 檢查容器狀態

#### 使用 Docker Compose

```bash
# 查看運行中的容器
docker-compose ps

# 查看所有服務的日誌
docker-compose logs

# 持續查看日誌
docker-compose logs -f

# 查看特定服務的日誌
docker-compose logs -f app
docker-compose logs -f nginx
```

#### 手動運行容器

```bash
# 查看運行中的容器
docker ps

# 查看應用程式容器日誌
docker logs msgcreator-app

# 查看 Nginx 容器日誌
docker logs msgcreator-nginx

# 持續查看日誌
docker logs -f msgcreator-app
docker logs -f msgcreator-nginx
```

---

## 🔧 常用 Docker 命令

### 查看映像檔
```bash
docker images
```

### 查看容器
```bash
# 查看運行中的容器
docker ps

# 查看所有容器（包括已停止的）
docker ps -a
```

### 停止容器
```bash
docker stop msgcreator
```

### 啟動容器
```bash
docker start msgcreator
```

### 重啟容器
```bash
docker restart msgcreator
```

### 刪除容器
```bash
# 先停止容器
docker stop msgcreator

# 刪除容器
docker rm msgcreator
```

### 刪除映像檔
```bash
docker rmi YOUR_DOCKERHUB_USERNAME/msgcreator:latest
```

### 更新應用程式（重新部署）

當您更新了程式碼後，需要重新部署：

#### 使用 Docker Compose

```bash
# 1. 在本地重新構建並推送
docker build -t YOUR_DOCKERHUB_USERNAME/msgcreator:latest .
docker push YOUR_DOCKERHUB_USERNAME/msgcreator:latest

# 2. 在 EC2 上拉取最新映像檔
cd ~/msgcreator
docker-compose pull app

# 3. 重新啟動服務（會自動使用新映像檔）
docker-compose up -d --force-recreate app

# 或者重新啟動所有服務
docker-compose up -d --force-recreate
```

#### 手動運行容器

```bash
# 1. 在本地重新構建並推送
docker build -t YOUR_DOCKERHUB_USERNAME/msgcreator:latest .
docker push YOUR_DOCKERHUB_USERNAME/msgcreator:latest

# 2. 在 EC2 上停止舊容器
docker stop msgcreator-app
docker rm msgcreator-app

# 3. 拉取最新映像檔
docker pull YOUR_DOCKERHUB_USERNAME/msgcreator:latest

# 4. 運行新容器
docker run -d \
  --name msgcreator-app \
  --network app-network \
  --env-file .env \
  --restart unless-stopped \
  YOUR_DOCKERHUB_USERNAME/msgcreator:latest
```

---

## 🌐 設定 EC2 安全群組

確保您的 EC2 安全群組允許以下流量：

### 使用 Nginx（推薦）

- **入站規則**: 
  - 類型: HTTP
  - 協議: TCP
  - 端口: 80
  - 來源: 0.0.0.0/0（或您的特定 IP）
  
  - 類型: HTTPS（如果使用 SSL）
  - 協議: TCP
  - 端口: 443
  - 來源: 0.0.0.0/0（或您的特定 IP）

### 不使用 Nginx（直接訪問應用程式）

- **入站規則**: 
  - 類型: HTTP
  - 協議: TCP
  - 端口: 8000
  - 來源: 0.0.0.0/0（或您的特定 IP）

---

## 🔍 故障排除

### 容器無法啟動

1. 檢查日誌：
```bash
docker logs msgcreator
```

2. 檢查環境變數是否正確：
```bash
docker exec msgcreator env
```

### 無法連接到資料庫

- 確認 EC2 安全群組允許連接到 RDS
- 確認 RDS 安全群組允許來自 EC2 的連線
- 檢查 `.env` 文件中的資料庫設定是否正確

### 端口已被佔用

如果 8000 端口已被使用，可以改用其他端口：

```bash
docker run -d \
  --name msgcreator \
  -p 8080:8000 \
  --env-file .env \
  --restart unless-stopped \
  YOUR_DOCKERHUB_USERNAME/msgcreator:latest
```

這樣應用程式會在 EC2 的 8080 端口運行。

---

## 📝 注意事項

1. **安全性**: `.env` 文件包含敏感資訊，請勿提交到 Git
2. **備份**: 定期備份您的資料庫和環境設定
3. **監控**: 建議設定 CloudWatch 或其他監控工具來追蹤應用程式狀態
4. **日誌**: 定期檢查容器日誌以發現問題

---

## 🎉 完成！

部署完成後，您可以透過以下網址訪問應用程式：

### 使用 Nginx + HTTPS（推薦）
```
https://YOUR_DOMAIN_NAME
```
HTTP 會自動重定向到 HTTPS

### 使用 Nginx（僅 HTTP）
```
http://YOUR_EC2_PUBLIC_IP
```
或
```
http://YOUR_DOMAIN_NAME
```

### 不使用 Nginx
```
http://YOUR_EC2_PUBLIC_IP:8000
```

---

## 🔧 Nginx 配置說明

### Nginx 的優勢

1. **反向代理**: 隱藏應用程式的實際端口，提供更專業的訪問方式
2. **靜態文件服務**: 直接由 Nginx 提供靜態文件，提升效能
3. **負載均衡**: 未來可以輕鬆擴展多個應用程式實例
4. **SSL/TLS**: 更容易配置 HTTPS
5. **安全性**: 可以添加額外的安全頭和限制

### 上傳 Nginx 配置文件到 EC2

如果您使用手動運行容器的方式，需要將 `nginx/nginx.conf` 文件上傳到 EC2：

```bash
# 在本地機器上使用 SCP 上傳
scp -i msgcreator.pem nginx/nginx.conf ec2-user@YOUR_EC2_IP:~/msgcreator/nginx/nginx.conf

# 或使用 Ubuntu 用戶
scp -i msgcreator.pem nginx/nginx.conf ubuntu@YOUR_EC2_IP:~/msgcreator/nginx/nginx.conf
```

### 測試 Nginx 配置

在 EC2 上測試 Nginx 配置是否正確：

```bash
# 進入 Nginx 容器
docker exec -it msgcreator-nginx sh

# 測試配置
nginx -t

# 重新載入配置（如果修改了配置）
nginx -s reload
```

## 🔒 配置 HTTPS（使用 Let's Encrypt）

### 前置需求

1. **域名**: 您需要有一個域名（例如：example.com）
2. **DNS 設定**: 將域名 A 記錄指向您的 EC2 公網 IP
3. **端口開放**: 確保 EC2 安全群組開放 80 和 443 端口

### 步驟 1: 安裝 Certbot

在 EC2 上安裝 Certbot（Let's Encrypt 客戶端）：

**Amazon Linux / Amazon Linux 2:**
```bash
sudo yum install -y certbot
```

**Ubuntu:**
```bash
sudo apt update
sudo apt install -y certbot
```

### 步驟 2: 暫時修改 Nginx 配置

在取得憑證之前，需要暫時修改 `nginx/nginx.conf`，移除 SSL 相關設定，只保留 HTTP：

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_NAME;  # 改為您的域名

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://app;
        # ... 其他配置
    }
}
```

### 步驟 3: 啟動 Nginx（僅 HTTP）

```bash
cd ~/msgcreator
docker-compose up -d
```

### 步驟 4: 取得 SSL 憑證

```bash
# 創建 certbot 目錄
mkdir -p ~/msgcreator/certbot/www
mkdir -p ~/msgcreator/certbot/conf

# 使用 certbot 取得憑證（替換 YOUR_DOMAIN 和 YOUR_EMAIL）
sudo certbot certonly --webroot \
  -w ~/msgcreator/certbot/www \
  -d YOUR_DOMAIN \
  --email YOUR_EMAIL \
  --agree-tos \
  --non-interactive

# 憑證會儲存在 /etc/letsencrypt/live/YOUR_DOMAIN/
```

### 步驟 5: 複製憑證到專案目錄

```bash
# 複製憑證文件
sudo cp -r /etc/letsencrypt/live/YOUR_DOMAIN ~/msgcreator/certbot/conf/live/
sudo cp -r /etc/letsencrypt/archive/YOUR_DOMAIN ~/msgcreator/certbot/conf/archive/
sudo cp -r /etc/letsencrypt/renewal ~/msgcreator/certbot/conf/

# 設定權限
sudo chown -R $USER:$USER ~/msgcreator/certbot
```

### 步驟 6: 更新 Nginx 配置

編輯 `nginx/nginx.conf`，將 `YOUR_DOMAIN` 替換為您的實際域名：

```bash
cd ~/msgcreator
nano nginx/nginx.conf
```

將 `YOUR_DOMAIN` 替換為您的域名（例如：`example.com`）

### 步驟 7: 重新啟動服務

```bash
docker-compose down
docker-compose up -d
```

### 步驟 8: 測試 HTTPS

訪問 `https://YOUR_DOMAIN`，應該可以看到綠色的鎖頭標誌。

### 自動續約憑證

Let's Encrypt 憑證有效期為 90 天，需要定期續約。設定自動續約：

```bash
# 測試續約
sudo certbot renew --dry-run

# 設定 cron job 自動續約（每月執行一次）
sudo crontab -e

# 添加以下行（每月 1 號凌晨 3 點執行）
0 3 1 * * certbot renew --quiet --deploy-hook "cd ~/msgcreator && docker-compose restart nginx"
```

### 使用其他 SSL 憑證

如果您使用其他 SSL 憑證服務（如 AWS Certificate Manager, Cloudflare 等），請：

1. 將憑證文件放在 `certbot/conf/live/YOUR_DOMAIN/` 目錄
2. 確保文件名為：
   - `fullchain.pem`（完整憑證鏈）
   - `privkey.pem`（私鑰）
3. 更新 `nginx/nginx.conf` 中的路徑

### 故障排除

**憑證路徑錯誤：**
```bash
# 檢查憑證是否存在
ls -la ~/msgcreator/certbot/conf/live/YOUR_DOMAIN/

# 檢查 Nginx 日誌
docker-compose logs nginx
```

**無法訪問 HTTP-01 驗證：**
- 確保端口 80 已開放
- 確保 Nginx 正在運行
- 檢查 `/.well-known/acme-challenge/` 路徑是否正確
