"""把草稿發到 Threads。用法: python -m shopee_bot.publish [--date YYYY-MM-DD] [--only 1,3]"""
import argparse
import datetime as dt
import json

from . import config, threads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat())
    ap.add_argument("--only", default="", help="只發指定編號,例如 1,3")
    args = ap.parse_args()
    only = {int(x) for x in args.only.split(",") if x.strip()}

    files = sorted((config.DRAFTS_DIR / args.date).glob("[0-9][0-9].json"))
    if not files:
        raise SystemExit(f"找不到 {args.date} 的草稿")
    for f in files:
        d = json.loads(f.read_text())
        if d["status"] == "published" or (only and d["index"] not in only):
            continue
        if d["media_url"]:
            threads.wait_url_live(d["media_url"])
        post_id = threads.publish(d["kind"], d["text"], d["media_url"])
        d.update(status="published", threads_post_id=post_id)
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        print(f"✅ 已發布 #{d['index']} ({d['kind']}) → {post_id}")


if __name__ == "__main__":
    main()
