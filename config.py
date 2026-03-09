"""統一設定 — 環境變數 / 資料庫 / 路徑 / 模型"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── 路徑設定 ───
BASE_DIR = Path(__file__).parent
REPORT_DIR = BASE_DIR / "回測報告"
REPORT_DIR.mkdir(exist_ok=True)

# ─── 資料庫設定 ───
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "stock_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "5432"),
}

def get_db_url():
    c = DB_CONFIG
    return f"postgresql+psycopg2://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"

# ─── LINE 設定（僅 Push，無 Webhook）───
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# ─── Groq AI 設定 ───
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ─── 回測預設參數 ───
INIT_CASH = 100_000
DEFAULT_FEES = 0.001425      # 台股手續費 0.1425%
DEFAULT_SLIPPAGE = 0.001
