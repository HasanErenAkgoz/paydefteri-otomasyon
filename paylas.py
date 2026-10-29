"""Post the next ready queue item through ig_post.py (Telegram approval first).

Usage: python paylas.py [photo|reel]   # preferred type for this slot
       python paylas.py kontrol        # checks token, Telegram and upload host; posts nothing
"reel" posts a reel only if the last one went out REEL_EVERY_DAYS or more calendar days ago, else a photo.
Reels never go out in a photo slot.

Queue: kuyruk/<NNN-slug>/post.json plus rendered media (01.jpg... or video.mp4), oldest name first.
Published -> paylasilanlar/, rejected on Telegram -> reddedilenler/, no answer -> stays for the next slot,
3 failures -> hatali/. Every run is logged to gunluk.txt.
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
QUEUE = ROOT / "kuyruk"
IG_POST = ROOT / "yayin" / "ig_post.py"
sys.path.insert(0, str(IG_POST.parent))
from ig_post import telegram_config  # noqa: E402
LOW = 3  # warn on Telegram when fewer ready items than this remain
REEL_EVERY_DAYS = 3


def log(msg):
    with open(ROOT / "gunluk.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {msg}\n")


def telegram(text):
    try:
        tg = telegram_config()
        data = urllib.parse.urlencode({"chat_id": tg["chat_id"], "text": text}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{tg['bot_token']}/sendMessage", data, timeout=30)
    except Exception as e:  # a missed warning must not stop posting
        log(f"telegram warning failed: {e}")


def media(item, kind):
    if kind == "reel":
        v = item / "video.mp4"
        # no silent videos: a reel counts as ready only with its voiceover
        if not (v.is_file() and (item / "ses.mp3").is_file()):
            return []
        cover = item / "kapak.jpg"  # without it Instagram uses the first frame as the grid thumbnail
        return [str(v), str(cover)] if cover.is_file() else [str(v)]
    return [str(p) for p in sorted(item.glob("[0-9][0-9].jpg"))]


def ready_items():
    out = []
    for item in sorted(p for p in QUEUE.iterdir() if p.is_dir()):
        try:
            spec = json.loads((item / "post.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        files = media(item, spec.get("type"))
        if files:
            out.append((item, spec, files))
    return out


def reel_due(now=None):
    last = None
    for spec_file in (ROOT / "paylasilanlar").glob("*/post.json"):
        res = spec_file.with_name("sonuc.txt")
        try:
            if json.loads(spec_file.read_text(encoding="utf-8")).get("type") == "reel" and res.is_file():
                when = datetime.strptime(res.read_text(encoding="utf-8")[:16], "%Y-%m-%d %H:%M")
                last = max(last or when, when)
        except (OSError, ValueError):
            continue
    return last is None or ((now or datetime.now()).date() - last.date()).days >= REEL_EVERY_DAYS


def pick(items, want):
    """Reel slot: a due reel, else a photo. Photo slot: photos only."""
    by = lambda kind: next((x for x in items if x[1]["type"] == kind), None)
    if want == "reel" and reel_due():
        return by("reel") or by("photo")
    return by("photo")


def move(item, folder, note):
    dest = ROOT / folder / item.name
    shutil.move(str(item), str(dest))
    (dest / "sonuc.txt").write_text(f"{datetime.now():%Y-%m-%d %H:%M} {note}\n", encoding="utf-8")


def kontrol():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(IG_POST), "whoami"], capture_output=True, text=True, encoding="utf-8", env=env)
    print("instagram:", (r.stdout + r.stderr).strip())
    try:
        urllib.request.urlopen(urllib.request.Request("https://catbox.moe/", headers={"User-Agent": "ig-post/1.0"}), timeout=30)
        print("catbox.moe: ok")
    except Exception as e:
        print("catbox.moe: FAIL", e)
    telegram("☁️ PayDefteri bağlantı kontrolü: Telegram mesajı ulaştı. (Test, paylaşım yapılmadı.)")
    print("telegram: test message sent (gunluk.txt shows a failure)")
    if r.returncode != 0:
        sys.exit(1)


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else None
    if want == "kontrol":
        return kontrol()
    items = ready_items()
    if not items:
        log("queue empty, nothing posted")
        telegram("⚠️ PayDefteri kuyruğu boş, bu saatte post paylaşılmadı.")
        return
    chosen = pick(items, want)
    if not chosen:
        log(f"no ready photo for this slot ({want}), nothing posted")
        telegram("⚠️ PayDefteri kuyruğunda hazır görsel post yok, bu saatte paylaşılmadı.")
        return
    item, spec, files = chosen

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(IG_POST), spec["type"], spec["caption"], *files],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 0 and "Published" in out:
        move(item, "paylasilanlar", out)
        log(f"posted {item.name}: {out}")
    elif "Rejected on Telegram" in out:
        move(item, "reddedilenler", out)
        log(f"rejected {item.name}")
    elif "No Telegram answer" in out:
        log(f"no answer for {item.name}, kept in queue")
    else:
        # one line per failed run, so the line count is the failure count
        last = out.splitlines()[-1] if out else f"exit {r.returncode}"
        fails = item / "hatalar.txt"
        with open(fails, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M} {last}\n")
        n = len(fails.read_text(encoding="utf-8").splitlines())
        log(f"error {n}/3 for {item.name}: {last}")
        if n >= 3:
            move(item, "hatali", last)
            telegram(f"⚠️ {item.name} 3 kez paylaşılamadı, hatali/ klasörüne taşındı.\nSon hata: {last[-300:]}")

    left = len(ready_items())
    if left < LOW:
        telegram(f"ℹ️ PayDefteri kuyruğunda {left} hazır post kaldı.")


if __name__ == "__main__":
    main()
