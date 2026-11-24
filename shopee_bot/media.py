"""用商品圖產生:1080x1080 圖片卡、1080x1920 短影片(ffmpeg)。"""
import io
import shutil
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/unifont/unifont_jp.otf",  # 最後備援
]
BG = (255, 247, 240)
ORANGE = (238, 77, 45)
INK = (45, 45, 45)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def _download(url: str) -> Image.Image:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > width:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def _price_text(p):
    if p["price_max"] > p["price"]:
        return f"${p['price']:,.0f} ~ ${p['price_max']:,.0f}"
    return f"${p['price']:,.0f}"


def make_card(p: dict, size=(1080, 1080), photo: Image.Image | None = None) -> Image.Image:
    """商品圖卡:上方商品圖,下方名稱、價格、銷量。"""
    w, h = size
    img = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(img)
    photo = photo or _download(p["image_url"])
    ph = int(h * 0.62)
    photo = ImageOps.fit(photo, (w - 80, ph), Image.LANCZOS)
    img.paste(photo, (40, 40))
    y = 40 + ph + 30
    f_title, f_price, f_small = _font(46), _font(72), _font(36)
    for line in _wrap(d, p["name"], f_title, w - 80)[:2]:
        d.text((40, y), line, font=f_title, fill=INK)
        y += 60
    d.text((40, y + 10), _price_text(p), font=f_price, fill=ORANGE)
    d.text((40, h - 70), f"已售 {p['sales']:,} 件", font=f_small, fill=(120, 120, 120))
    return img


def make_image(p: dict, out: Path, photo=None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    make_card(p, photo=photo).save(out, "JPEG", quality=90)
    return out


def _text_slide(lines, size, accent=False) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, ORANGE if accent else BG)
    d = ImageDraw.Draw(img)
    color = (255, 255, 255) if accent else INK
    fonts = [_font(88), _font(60), _font(44)]
    y = h // 2 - 160
    for i, line in enumerate(lines):
        f = fonts[min(i, 2)]
        for sub in _wrap(d, line, f, w - 160):
            tw = d.textlength(sub, font=f)
            d.text(((w - tw) / 2, y), sub, font=f, fill=color)
            y += f.size + 24
        y += 20
    return img


def make_video(p: dict, out: Path, photo=None, seconds_per_slide: int = 4) -> Path:
    """三張投影片 → 12 秒直式影片:商品圖 → 價格銷量 → 提醒。"""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("找不到 ffmpeg")
    out.parent.mkdir(parents=True, exist_ok=True)
    size = (1080, 1920)
    photo = photo or _download(p["image_url"])
    slide1 = Image.new("RGB", size, BG)
    sq = ImageOps.fit(photo, (1000, 1000), Image.LANCZOS)
    slide1.paste(sq, (40, 260))
    d = ImageDraw.Draw(slide1)
    f = _font(56)
    y = 1330
    for line in _wrap(d, p["name"], f, 960)[:3]:
        d.text((60, y), line, font=f, fill=INK)
        y += 74
    slide2 = _text_slide(["今日蝦皮熱賣", _price_text(p), f"已售 {p['sales']:,} 件"], size, accent=True)
    slide3 = _text_slide(["想看詳情", "連結放在貼文裡", "先逛逛不買也沒關係"], size)

    tmp = out.parent / f".{out.stem}_slides"
    tmp.mkdir(exist_ok=True)
    paths = []
    for i, s in enumerate([slide1, slide2, slide3]):
        pth = tmp / f"s{i}.png"
        s.save(pth)
        paths.append(pth)
    inputs, filters = [], []
    for i, pth in enumerate(paths):
        inputs += ["-loop", "1", "-t", str(seconds_per_slide), "-i", str(pth)]
        filters.append(f"[{i}:v]scale=1080:1920,setsar=1,fps=30[v{i}]")
    chain = "".join(f"[v{i}]" for i in range(len(paths)))
    fc = ";".join(filters) + f";{chain}concat=n={len(paths)}:v=1:a=0[v]"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc,
         "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        check=True,
    )
    shutil.rmtree(tmp, ignore_errors=True)
    return out
