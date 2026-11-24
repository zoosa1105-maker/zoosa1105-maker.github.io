"""蝦皮聯盟開放 API(GraphQL)。簽章規則:SHA256(AppId + Timestamp + Payload + Secret)。"""
import hashlib
import json
import time

import requests

from . import config

QUERY = """
query ($page: Int, $limit: Int, $sort: Int) {
  productOfferV2(listType: 0, sortType: $sort, page: $page, limit: $limit) {
    nodes {
      itemId productName price priceMin priceMax sales ratingStar
      commissionRate imageUrl shopName productLink offerLink
    }
    pageInfo { hasNextPage }
  }
}
"""
SORT_ITEM_SOLD_DESC = 2  # 依銷量由高到低


def _call(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = hashlib.sha256(
        f"{config.SHOPEE_APP_ID}{ts}{payload}{config.SHOPEE_SECRET}".encode()
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={config.SHOPEE_APP_ID}, Timestamp={ts}, Signature={sig}",
    }
    r = requests.post(config.SHOPEE_ENDPOINT, data=payload, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"Shopee API 錯誤: {data['errors']}")
    return data["data"]


def _num(x, default=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def fetch_hot_products(pages: int = 2, limit: int = 20) -> list[dict]:
    """抓全站熱賣商品(依銷量排序),整理成統一格式。"""
    out = []
    for page in range(1, pages + 1):
        data = _call(QUERY, {"page": page, "limit": limit, "sort": SORT_ITEM_SOLD_DESC})
        block = data["productOfferV2"]
        for n in block["nodes"]:
            price = _num(n.get("priceMin") or n.get("price"))
            price_max = _num(n.get("priceMax"), price)
            out.append({
                "id": str(n["itemId"]),
                "name": n["productName"],
                "price": price,
                "price_max": price_max,
                "sales": int(_num(n.get("sales"))),
                "rating": _num(n.get("ratingStar")),
                "commission_rate": _num(n.get("commissionRate")),
                "image_url": n["imageUrl"],
                "shop": n.get("shopName", ""),
                "link": n.get("offerLink") or n.get("productLink"),
            })
        if not block["pageInfo"]["hasNextPage"]:
            break
    return out


def pick_products(products: list[dict], seen: set[str], n: int) -> list[dict]:
    """去掉發過的、評價太低的,再挑前 n 個(銷量優先,同量比佣金)。"""
    ok = [p for p in products if p["id"] not in seen and p["link"]
          and (p["rating"] == 0 or p["rating"] >= 4.5)]
    ok.sort(key=lambda p: (p["sales"], p["commission_rate"]), reverse=True)
    return ok[:n]
