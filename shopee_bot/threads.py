"""Threads 官方 API:建立容器 → (影片要等處理完) → 發布。"""
import time

import requests

from . import config

BASE = "https://graph.threads.net/v1.0"


def _post(path: str, **params) -> dict:
    params["access_token"] = config.THREADS_TOKEN
    r = requests.post(f"{BASE}/{path}", data=params, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Threads API {r.status_code}: {r.text}")
    return r.json()


def _wait_ready(container_id: str, timeout: int = 300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(
            f"{BASE}/{container_id}",
            params={"fields": "status,error_message", "access_token": config.THREADS_TOKEN},
            timeout=30,
        )
        st = r.json().get("status")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Threads 媒體處理失敗: {r.json()}")
        time.sleep(5)
    raise TimeoutError("Threads 媒體處理逾時")


def publish(kind: str, text: str, media_url: str | None = None) -> str:
    uid = config.THREADS_USER_ID
    if kind == "text":
        c = _post(f"{uid}/threads", media_type="TEXT", text=text)
    elif kind == "image":
        c = _post(f"{uid}/threads", media_type="IMAGE", image_url=media_url, text=text)
    elif kind == "video":
        c = _post(f"{uid}/threads", media_type="VIDEO", video_url=media_url, text=text)
    else:
        raise ValueError(kind)
    _wait_ready(c["id"])
    return _post(f"{uid}/threads_publish", creation_id=c["id"])["id"]


def wait_url_live(url: str, timeout: int = 600):
    """GitHub Pages 剛推上去要等一下才讀得到,Threads 才抓得到圖。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.head(url, timeout=15, allow_redirects=True).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(15)
    raise TimeoutError(f"媒體網址一直打不開: {url}")
