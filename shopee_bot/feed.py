"""讀蝦皮聯盟後台下載的 Product Feed(CSV),不需要 Open API。

把檔案放進 repo 的 feed/ 資料夾(可放多個 .csv)。欄位名稱中英文都能自動對應,
對不到時會明確列出缺哪個欄位。
"""
import csv
import random
from pathlib import Path

from . import config

FEED_DIR = config.ROOT / "feed"

# 標準欄位 → 可能的欄位名稱(比對時轉小寫、去空白)
ALIASES = {
    "id": ["itemid", "item_id", "商品id", "商品編號", "商品編碼", "id", "product_id", "productid"],
    "name": ["productname", "product_name", "name", "title", "商品名稱", "商品名", "標題"],
    "price": ["price", "pricemin", "price_min", "商品價格", "價格", "售價", "最低價格", "sale_price", "saleprice"],
    "price_max": ["pricemax", "price_max", "最高價格", "最高價"],
    "sales": ["sales", "sold", "itemsold", "item_sold", "historical_sold", "銷量", "已售", "已售出", "累積銷量", "總銷量"],
    "rating": ["ratingstar", "rating", "rating_star", "評價", "評分", "商品評價"],
    "commission_rate": ["commissionrate", "commission_rate", "commission", "佣金率", "佣金比例", "分潤比例", "佣金"],
    "image_url": ["imageurl", "image_url", "image", "image_link", "imagelink", "圖片", "圖片連結", "主圖", "商品圖片", "圖片網址"],
    "shop": ["shopname", "shop_name", "shop", "賣場名稱", "商店名稱", "賣場", "店家"],
    "link": ["offerlink", "offer_link", "affiliatelink", "affiliate_link", "分潤連結", "推廣連結", "聯盟連結",
             "productlink", "product_link", "link", "url", "商品連結", "商品網址", "連結"],
}
REQUIRED = ["name", "image_url", "link"]


def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "").replace("-", "_")


def _num(x, default=0.0) -> float:
    if x is None:
        return default
    s = str(x).strip().replace(",", "").replace("$", "").replace("NT", "").replace("%", "")
    mult = 1
    if s.lower().endswith("k"):
        mult, s = 1000, s[:-1]
    elif s.endswith("萬"):
        mult, s = 10000, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return default


def _read_rows(path: Path) -> list[dict]:
    for enc in ("utf-8-sig", "utf-8", "cp950"):
        try:
            with open(path, newline="", encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"無法判斷 {path.name} 的編碼,請另存成 UTF-8 CSV")


def _map_columns(headers: list[str]) -> dict[str, str]:
    by_norm = {_norm(h): h for h in headers if h}
    mapping = {}
    for std, names in ALIASES.items():
        for n in names:
            if n in by_norm:
                mapping[std] = by_norm[n]
                break
    missing = [k for k in REQUIRED if k not in mapping]
    if missing:
        raise ValueError(
            f"Feed 對不到必要欄位 {missing}。檔案實際欄位:{headers}。"
            "請把欄位名稱告訴我,或到 shopee_bot/feed.py 的 ALIASES 補上。"
        )
    return mapping


def load_feed() -> list[dict]:
    files = sorted(FEED_DIR.glob("*.csv"))
    if not files:
        raise SystemExit("feed/ 資料夾裡沒有 .csv。請從蝦皮聯盟後台下載 Product Feed 放進去。")
    products, seen_ids = [], set()
    for path in files:
        rows = _read_rows(path)
        if not rows:
            continue
        m = _map_columns(list(rows[0].keys()))
        for i, r in enumerate(rows):
            g = lambda k, d="": (r.get(m[k]) if k in m else d) or d
            name, link, img = g("name").strip(), g("link").strip(), g("image_url").strip()
            if not (name and link and img):
                continue
            pid = g("id").strip() or link
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            price = _num(g("price"))
            comm = _num(g("commission_rate"))
            if comm > 1:  # "5" 或 "5%" → 0.05
                comm /= 100
            products.append({
                "id": str(pid), "name": name, "price": price,
                "price_max": _num(g("price_max"), price) or price,
                "sales": int(_num(g("sales"))), "rating": _num(g("rating")),
                "commission_rate": comm, "image_url": img,
                "shop": g("shop").strip(), "link": link,
            })
    return products


def has_affiliate_link(link: str) -> bool:
    """粗略判斷是不是分潤短連結。不是的話貼了也不會有佣金,產草稿時會警告。"""
    l = link.lower()
    return any(k in l for k in ("shope.ee", "s.shopee.tw", "affiliate", "an_redir", "origin_link"))


def pick_from_feed(products: list[dict], seen: set[str], n: int, today: str) -> list[dict]:
    ok = [p for p in products if p["id"] not in seen and (p["rating"] == 0 or p["rating"] >= 4.5)]
    if any(p["sales"] for p in ok):
        ok.sort(key=lambda p: (p["sales"], p["commission_rate"]), reverse=True)
        return ok[:n]
    # 沒有銷量欄位:佣金優先,同佣金時用日期當亂數種子輪替,避免每天都一樣
    rnd = random.Random(today)
    rnd.shuffle(ok)
    ok.sort(key=lambda p: p["commission_rate"], reverse=True)
    return ok[:n]
