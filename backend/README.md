# Cloud SQL 設定指南

## 步驟一：安裝 Cloud SQL Proxy

### Mac 用戶

```bash
# 方法 1：使用 Homebrew
brew install cloud-sql-proxy

# 方法 2：直接下載
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.1/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy
```

### Windows 用戶

1. 下載 [Cloud SQL Auth proxy for Windows](https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe)
2. 將下載的檔案重新命名為 `cloud_sql_proxy.exe`
3. 將檔案移動到專案目錄或添加到系統環境變數

## 步驟二：設定 GCP 認證

### Mac 用戶

```bash
# 安裝 gcloud CLI
brew install --cask google-cloud-sdk
```

### Windows 用戶

1. 從 [Google Cloud SDK 安裝頁面](https://cloud.google.com/sdk/docs/install) 下載安裝包
2. 執行安裝程序
3. 開啟新的終端機視窗

### 所有用戶共同步驟

```bash
# 登入 Google Cloud
gcloud auth login

# 設定專案
gcloud config set project hackathon-450410

# 產生應用程式預設憑證
gcloud auth application-default login
```

## 步驟三：啟動 Cloud SQL Proxy

### Mac 用戶

```bash
cloud-sql-proxy hackathon-450410:us-central1:hackathon --port 3306
```

### Windows 用戶

```bash
cloud_sql_proxy.exe -instances=[專案ID:區域:實例名稱]=tcp:3306
```

成功啟動後會看到：

```
2025/02/10 XX:XX:XX The proxy has started successfully and is ready for new connections!
```

## 步驟四：設定環境變數

1. 在專案根目錄建立 `.env` 檔案：

```env
DB_USER=root
DB_PASS=0000
DB_HOST=127.0.0.1
DB_NAME=hackathon
```

2. 確保 `.env` 已加入 `.gitignore`：

```bash
echo ".env" >> .gitignore
```

3. python 程式參考

```bash
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 使用環境變數構建連線字串
URL_DATABASE = f"mysql+aiomysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"
```

## 重要提醒

-   執行程式時請確保 Cloud SQL Proxy 保持運行
-   不要將 .env 檔案提交到 Git
-   定期檢查 Cloud SQL Proxy 的終端機輸出以排查問題
