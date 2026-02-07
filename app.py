from fastapi import FastAPI, Request, Query, Form, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import boto3
import uuid
import os
from datetime import datetime
import pymysql
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = FastAPI()

# S3 設定
s3 = boto3.client('s3')
BUCKET_NAME = "msgcreator-images"

# CloudFront CDN 設定
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '')

# RDS 資料庫設定（從環境變數讀取）
# 上線後 EC2 可直接連線 RDS（透過 VPC 內網連線，無需公網）
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),  # RDS MySQL 預設 port
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'msgcreator'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10,  # 連線超時設定（秒）
    'read_timeout': 30,     # 讀取超時設定（秒）
    'write_timeout': 30     # 寫入超時設定（秒）
}

def get_db_connection():
    """建立資料庫連線"""
    return pymysql.connect(**DB_CONFIG)

def get_cloudfront_url(s3_key: str) -> str:
    """根據 S3 key 產生 CloudFront CDN URL"""
    if not CLOUDFRONT_DOMAIN:
        raise ValueError("CLOUDFRONT_DOMAIN environment variable is not set")
    
    # CloudFront URL 格式: https://{domain}/{s3_key}
    # 確保 URL 格式正確（移除尾部的斜線）
    domain = CLOUDFRONT_DOMAIN.rstrip('/')
    return f"https://{domain}/{s3_key}"

@app.post("/upload")
async def upload_message(
    file: UploadFile = File(...),
    message: str = Form(...)
):
    """上傳圖片到 S3 並儲存留言到 RDS"""
    try:
        # 檢查必要欄位
        message = message.strip()
        if not message:
            return JSONResponse(
                status_code=400,
                content={"error": "Message is required"}
            )
        
        original_filename = file.filename
        
        # 生成唯一 ID（UUID）
        file_id = str(uuid.uuid4())
        
        # 保留原始檔案的副檔名
        file_extension = os.path.splitext(original_filename)[1] if original_filename else ""
        s3_key = f"{file_id}{file_extension}"
        
        # 上傳圖片到 S3（保持私有，不設定公開存取）
        s3.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        
        # 儲存留言到 RDS
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO messages (message, image_id, file_extension, created_at)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (message, file_id, file_extension, datetime.now()))
                message_id = cursor.lastrowid
                connection.commit()
            
            return JSONResponse(
                status_code=201,
                content={
                    "message": "Upload success",
                    "id": message_id,
                    "image_id": file_id,
                    "s3_key": s3_key
                }
            )
        finally:
            connection.close()
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Upload failed: {str(e)}"}
        )

@app.get("/messages")
async def get_messages():
    """取得所有留言和對應的圖片 URL"""
    try:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT id, message, image_id, file_extension, created_at
                    FROM messages
                    ORDER BY created_at DESC
                """
                cursor.execute(sql)
                messages = cursor.fetchall()
            
            # 為每個留言產生圖片 CloudFront CDN URL
            result = []
            for msg in messages:
                image_id = msg['image_id']
                file_extension = msg.get('file_extension', '.jpg')  # 預設 .jpg
                
                # 產生圖片 CloudFront CDN URL
                try:
                    s3_key = f"{image_id}{file_extension}"
                    image_url = get_cloudfront_url(s3_key)
                except Exception:
                    image_url = None
                
                result.append({
                    "id": msg['id'],
                    "message": msg['message'],
                    "image_id": image_id,
                    "image_url": image_url,
                    "created_at": msg['created_at'].isoformat() if msg['created_at'] else None
                })
            
            return JSONResponse(
                status_code=200,
                content={
                    "messages": result,
                    "count": len(result)
                }
            )
        finally:
            connection.close()
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch messages: {str(e)}"}
        )

@app.get("/get-image-url")
async def get_image_url(
    image_id: str = Query(..., description="圖片 ID"),
    extension: str = Query(".jpg", description="檔案副檔名")
):
    """根據 image_id 取得圖片 CloudFront CDN URL"""
    if not image_id:
        return JSONResponse(
            status_code=400,
            content={"error": "image_id parameter is required"}
        )
    
    # 組合 S3 key
    s3_key = f"{image_id}{extension}"
    
    try:
        # 產生 CloudFront CDN URL
        url = get_cloudfront_url(s3_key)
        
        return JSONResponse(content={"url": url})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate URL: {str(e)}"}
        )



# ========== 靜態頁面 ==========
@app.get("/", include_in_schema=False)
async def index(request: Request):
    return FileResponse("./static/index.html", media_type="text/html")