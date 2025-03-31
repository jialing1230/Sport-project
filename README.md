"# Sport-project" 
"# Sport-project" 
### 1️⃣ Clone 專案

```bash
git clone https://github.com/jialing1230/Sport-project.git

2️⃣ 建立虛擬環境並啟動
py -3.11 -m venv venv
venv\Scripts\activate

python3.11 -m venv venv
source venv/bin/activate

3️⃣ 安裝套件
pip install -r requirements.txt

4️⃣ 建立 .env 檔案
DB_NAME=sport_db
DB_USER=你的MySQL帳號
DB_PASSWORD=你的MySQL密碼
DB_HOST=localhost
DB_PORT=3306
如果你還沒建立資料庫，請先進入 MySQL 建立：
CREATE DATABASE sport_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
5️⃣ 確保 __init__.py 中有以下內容：
import pymysql
pymysql.install_as_MySQLdb()

6️⃣ 建立資料表
python manage.py migrate

7️⃣ 執行伺服器
python manage.py runserver
打開瀏覽器： http://127.0.0.1:8000

建立.gitignore避免虛擬環境及其他不必要的東西到git
# 忽略虛擬環境
venv/

# 忽略 Python 快取檔
__pycache__/
*.pyc

# 忽略環境變數檔
.env

# 忽略資料庫或機密設定（如有）
*.sqlite3
✅ 注意事項
.env 請勿上傳 GitHub，已加進 .gitignore

若新增套件，請執行：pip freeze > requirements.txt 再 commit

若建立新 App，記得加進 INSTALLED_APPS 並執行 migrate
