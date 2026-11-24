"""用 Claude 寫貼文文案;沒有金鑰時退回固定範本。"""
import requests

from . import config

SYSTEM = (
    "你是台灣 Threads 上的生活分享者,對象是勞工、單身、小資族。"
    "語氣溫暖、接地氣、像朋友聊天,不油條、不說教、不浮誇推銷。"
    "只能根據提供的商品資料寫,不可編造功效、規格、折扣或使用心得。"
    "全程使用繁體中文,不要放連結與 hashtag(系統會加)。"
)


def _fallback(p: dict) -> str:
    return (
        f"今天蝦皮熱賣榜上的它:{p['name'][:40]}\n"
        f"已經賣出 {p['sales']:,} 件,{_price(p)}。\n"
        "想看看大家都在買什麼的人,可以順手逛逛。"
    )


def _price(p: dict) -> str:
    if p["price_max"] > p["price"]:
        return f"約 ${p['price']:,.0f}~${p['price_max']:,.0f}"
    return f"約 ${p['price']:,.0f}"


def write_copy(p: dict, kind: str) -> str:
    """kind: text / image / video。回傳 150 字內的貼文本文(不含連結)。"""
    if not config.ANTHROPIC_API_KEY:
        return _fallback(p)
    style = {
        "text": "像朋友隨口分享,100 字內,先一句生活情境再帶商品。",
        "image": "搭配商品圖的圖說,80 字內,一句情境加一句重點。",
        "video": "搭配短影片的旁白式文案,60 字內,輕鬆好讀。",
    }[kind]
    user = (
        f"商品:{p['name']}\n價格:{_price(p)}\n已售:{p['sales']:,} 件\n"
        f"評價:{p['rating'] or '無資料'}\n賣場:{p['shop']}\n\n"
        f"請寫一則 Threads 貼文本文。風格:{style}"
    )
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.CLAUDE_MODEL,
                "max_tokens": 400,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip()
        return text[:300]
    except Exception as e:  # 文案失敗不該讓整天停擺
        print(f"[content] Claude 失敗,改用範本: {e}")
        return _fallback(p)


def compose_post(body: str, link: str) -> str:
    """Threads 單則上限 500 字,連結與揭露字樣一定要留得下。"""
    tail = f"\n\n👉 {link}\n{config.DISCLOSURE}"
    return body[: 500 - len(tail)] + tail
