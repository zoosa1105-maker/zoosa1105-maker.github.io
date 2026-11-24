# 蝦皮分潤 × Threads 自動化

每天台灣時間 08:00 自動:抓蝦皮全站熱賣 → 挑 3 個沒發過的商品 → 產生 1 則文字、1 則圖片、1 則影片貼文草稿 → 存進 `drafts/日期/`。

## 一次性設定

1. **GitHub Secrets**(repo → Settings → Secrets and variables → Actions → Secrets):
   - `SHOPEE_APP_ID`、`SHOPEE_SECRET`:蝦皮聯盟開放平台
   - `THREADS_USER_ID`、`THREADS_ACCESS_TOKEN`:Meta 開發者後台的 Threads API
   - `ANTHROPIC_API_KEY`:寫文案用(不設就用固定範本)
2. **GitHub Pages** 要開著(圖片、影片靠它提供公開網址給 Threads)。
3. 此資料夾的程式與 `.github/workflows/` 需在預設分支(main)上排程才會跑。

## 每天怎麼用(草稿模式)

1. 早上看 Actions 執行摘要,或打開 `drafts/日期/PREVIEW.md` 檢查內容。
2. 想改字:直接編輯 `drafts/日期/0N.json` 的 `text`。
3. OK 後:Actions → 「蝦皮草稿發到 Threads」→ Run workflow(可填 `only` 只發部分)。

## 改成全自動

Settings → Variables 新增 `AUTO_PUBLISH` = `true`。建議先穩定看過幾天草稿再開。

## 本機測試(不連蝦皮、不發文)

    pip install -r shopee_bot/requirements.txt
    python -m shopee_bot.generate --demo

## 注意

- 每則貼文都會自動附上分潤揭露字樣,請勿移除。
- 蝦皮 API 回傳的欄位若與實際不同,調整 `shopee.py` 的 QUERY 與欄位對應即可。
- Threads 存取權杖約 60 天到期,需要定期更新。
