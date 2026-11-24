"""集中管理設定。金鑰一律從環境變數(GitHub Secrets)讀取,不寫進程式。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFTS_DIR = ROOT / "drafts"
MEDIA_DIR = ROOT / "bot-media"
STATE_FILE = ROOT / "shopee_bot" / "state" / "history.json"

# 每天固定 3 則:1 文字、1 圖片、1 影片
DAILY_PLAN = ["text", "image", "video"]

# 蝦皮聯盟
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET", "")
SHOPEE_ENDPOINT = "https://open-api.affiliate.shopee.tw/graphql"

# Threads
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")
THREADS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")

# Claude(寫文案)。沒設定就退回固定範本。
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

# 圖片/影片要有公開網址 Threads 才抓得到,這裡用 GitHub Pages
MEDIA_BASE_URL = os.getenv(
    "MEDIA_BASE_URL", "https://zoosa1105-maker.github.io"
).rstrip("/")

# 是否產生後直接發布。預設 false = 只存草稿,等你確認。
AUTO_PUBLISH = os.getenv("AUTO_PUBLISH", "false").lower() == "true"

DISCLOSURE = "(此為蝦皮分潤連結,透過連結購買我可能獲得佣金)"
