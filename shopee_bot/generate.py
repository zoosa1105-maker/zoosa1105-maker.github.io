"""每日產生 3 則草稿(文字/圖片/影片)。用法: python -m shopee_bot.generate [--demo]"""
import argparse
import datetime as dt
import json
import shutil

from . import config, content, feed, media, shopee, store

DEMO = [
    {"id": f"demo{i}", "name": n, "price": 199 + i * 100, "price_max": 199 + i * 100,
     "sales": 90000 - i * 1000, "rating": 4.9, "commission_rate": 0.05,
     "image_url": "", "shop": "示範商店", "link": f"https://shope.ee/demo{i}"}
    for i, n in enumerate(["日本製防水輕量好收納雨傘", "加厚保溫不鏽鋼隨行杯 500ml", "USB 充電式小夜燈"])
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="不連蝦皮/Threads,用假資料測流程")
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()  # 台灣時間
    seen = store.load_seen()
    n = len(config.DAILY_PLAN)

    if args.demo:
        picks = DEMO[:n]
    elif config.SHOPEE_APP_ID and config.SHOPEE_SECRET:
        print("[來源] 蝦皮 Open API")
        picks = shopee.pick_products(shopee.fetch_hot_products(), seen, n)
        if len(picks) < n:
            raise SystemExit(f"可用商品只有 {len(picks)} 個,少於 {n}")
    else:
        print("[來源] Product Feed(feed/*.csv)")
        picks = feed.pick_from_feed(feed.load_feed(), seen, n, today)
        if len(picks) < n:
            raise SystemExit(f"可用商品只有 {len(picks)} 個,少於 {n}")

    draft_dir = config.DRAFTS_DIR / today
    media_dir = config.MEDIA_DIR / today
    if draft_dir.exists() and not args.demo:
        print(f"{today} 草稿已存在,略過(要重做請先刪除 {draft_dir})")
        return
    draft_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    from PIL import Image
    summary = [f"# {today} 草稿預覽\n"]
    for i, (kind, p) in enumerate(zip(config.DAILY_PLAN, picks), 1):
        body = content.write_copy(p, kind)
        text = content.compose_post(body, p["link"])
        media_file = None
        if kind != "text":
            photo = Image.new("RGB", (800, 800), (230, 230, 230)) if args.demo else None
            ext = "jpg" if kind == "image" else "mp4"
            media_file = f"{i:02d}.{ext}"
            path = media_dir / media_file
            (media.make_image if kind == "image" else media.make_video)(p, path, photo=photo)
        draft = {
            "index": i, "kind": kind, "status": "draft", "product": p, "text": text,
            "media_url": (f"{config.MEDIA_BASE_URL}/bot-media/{today}/{media_file}" if media_file else None),
        }
        (draft_dir / f"{i:02d}.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2))
        warn = "" if args.demo or feed.has_affiliate_link(p["link"]) else (
            "\n⚠️ 這個連結看起來不是分潤短連結(沒有 shope.ee 等特徵),貼出去可能沒有佣金,請確認。\n")
        summary.append(f"## {i}. [{kind}] {p['name']}\n\n{text}\n{warn}")
        if media_file:
            summary.append(f"媒體:`bot-media/{today}/{media_file}`\n")
        seen.add(p["id"])

    (draft_dir / "PREVIEW.md").write_text("\n".join(summary))
    if not args.demo:
        store.save_seen(seen)
    print("\n".join(summary))


if __name__ == "__main__":
    main()
