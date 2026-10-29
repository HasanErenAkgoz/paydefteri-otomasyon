"""Post to Instagram via the Instagram API with Facebook Login.

Usage:
  python ig_post.py photo "caption" img1.jpg [img2.jpg ...]   # 2-20 images = carousel
  python ig_post.py reel "caption" video.mp4 [cover.jpg]        # cover = grid/profile thumbnail
  python ig_post.py whoami                                     # check token, posts nothing

Every post first goes to Telegram as a preview with Paylaş / İptal buttons.
The script waits up to 1 hour and publishes only after Paylaş (.telegram holds bot config).

Files can be local paths or public URLs. Local files are uploaded to catbox.moe
because Instagram only fetches media from a public URL.
Secrets come from env vars IG_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (cloud), else from .token and
.telegram files in IG_SECRETS_DIR, next to this script, or in ~/instagram-poster (local).
.token holds a Page access token of the Facebook Page
linked to the Instagram account (from a long-lived user token, so it does not expire).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API = "https://graph.facebook.com/v26.0"
SECRET_DIRS = [Path(d) for d in (os.environ.get("IG_SECRETS_DIR"), Path(__file__).parent, Path.home() / "instagram-poster") if d]


def secret_file(name):
    return next((d / name for d in SECRET_DIRS if (d / name).is_file()), None)


def ig_token():
    if os.environ.get("IG_TOKEN"):
        return os.environ["IG_TOKEN"].strip()
    f = secret_file(".token")
    if not f:
        sys.exit("Missing Instagram token: set IG_TOKEN or add a .token file")
    return f.read_text().strip()


def telegram_config():
    """{"bot_token": "...", "chat_id": 123} from env or the .telegram file."""
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        return {"bot_token": os.environ["TELEGRAM_BOT_TOKEN"].strip(), "chat_id": int(os.environ["TELEGRAM_CHAT_ID"])}
    f = secret_file(".telegram")
    if not f:
        sys.exit("Missing Telegram config: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID or add a .telegram file")
    return json.loads(f.read_text())
UA = {"User-Agent": "ig-post/1.0"}


def fetch(req, timeout, retry=True):
    """urlopen with 3 tries on network drops (e.g. WinError 10054); HTTP errors are not retried."""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if not retry or attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def call(method, url, params, retry=True):
    data = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data}", headers=UA)
    else:
        req = urllib.request.Request(url, data.encode(), UA, method="POST")
    try:
        return json.loads(fetch(req, 60, retry))
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()}")


def multipart(url, fields, file_field, path):
    b = uuid.uuid4().hex
    body = b"".join(
        f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()
    )
    body += (
        f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(url, body, {**UA, "Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        return fetch(req, 300).decode()
    except urllib.error.HTTPError as e:
        sys.exit(f"Upload error {e.code}: {e.read().decode()}")


def public_url(src):
    if src.startswith(("http://", "https://")):
        return src
    # shortcut: anonymous catbox.moe upload, file stays public forever; move to own S3/Cloudinary if that matters
    url = multipart("https://catbox.moe/user/api.php", {"reqtype": "fileupload"}, "fileToUpload", Path(src)).strip()
    if not url.startswith("https://"):
        sys.exit(f"Upload failed for {src}: {url}")
    return url


def approve(cmd, caption, files, username):
    """Send a preview to Telegram and block until the owner taps a button. Returns a notify function."""
    tg = telegram_config()
    api, chat = f"https://api.telegram.org/bot{tg['bot_token']}", int(tg["chat_id"])
    for f in files:
        method, field = ("sendVideo", "video") if f.lower().endswith(".mp4") else ("sendPhoto", "photo")
        if f.startswith("http"):
            call("POST", f"{api}/{method}", {"chat_id": chat, field: f})
        else:
            multipart(f"{api}/{method}", {"chat_id": chat}, field, Path(f))

    nonce = uuid.uuid4().hex[:8]
    buttons = [[{"text": "✅ Paylaş", "callback_data": f"ok:{nonce}"},
                {"text": "❌ İptal", "callback_data": f"no:{nonce}"}]]
    text = f"@{username} hesabına paylaşılsın mı?\n\n{caption}"
    msg = call("POST", f"{api}/sendMessage",
               {"chat_id": chat, "text": text, "reply_markup": json.dumps({"inline_keyboard": buttons})})["result"]

    def notify(status):
        call("POST", f"{api}/editMessageText",
             {"chat_id": chat, "message_id": msg["message_id"], "text": f"{status}\n\n{caption}"})

    offset, deadline = 0, time.time() + 3600
    while time.time() < deadline:
        updates = call("GET", f"{api}/getUpdates",
                       {"offset": offset, "timeout": 50, "allowed_updates": '["callback_query"]'})["result"]
        for u in updates:
            offset = u["update_id"] + 1
            q = u.get("callback_query")
            # only the owner's tap on this exact preview counts
            if not q or q["from"]["id"] != chat or q.get("data", "")[3:] != nonce:
                continue
            call("POST", f"{api}/answerCallbackQuery", {"callback_query_id": q["id"]})
            if q["data"].startswith("ok:"):
                notify("⏳ Onaylandı, paylaşılıyor...")
                return notify
            notify("❌ İptal edildi")
            sys.exit("Rejected on Telegram, nothing posted")
    notify("⌛ 1 saat içinde cevap gelmedi, paylaşılmadı")
    sys.exit("No Telegram answer within 1 hour, nothing posted")


def wait(token, cid):
    # videos can take minutes to process
    for _ in range(30):
        status = call("GET", f"{API}/{cid}", {"fields": "status_code", "access_token": token})["status_code"]
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} status {status}")
        time.sleep(10)
    sys.exit(f"Container {cid} not ready after 5 minutes")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("photo", "reel", "whoami"):
        sys.exit(__doc__)
    token = ig_token()
    auth = {"access_token": token}

    page = call("GET", f"{API}/me", {**auth, "fields": "name,instagram_business_account{id,username}"})
    if "instagram_business_account" not in page:
        sys.exit(f"Page {page['name']} has no linked Instagram professional account")
    me = page["instagram_business_account"]
    if args[0] == "whoami":
        print(f"Page {page['name']} -> @{me['username']} (IG id {me['id']})")
        return

    if len(args) < 3:
        sys.exit(__doc__)
    cmd, caption, files = args[0], args[1], args[2:]
    for f in files:
        if not f.startswith("http") and not Path(f).is_file():
            sys.exit(f"File not found: {f}")
    if cmd == "photo":
        if len(files) > 20:
            sys.exit("Carousel takes at most 20 images")
        for f in files:
            if not f.startswith("http") and Path(f).suffix.lower() not in (".jpg", ".jpeg"):
                sys.exit(f"Instagram accepts JPEG images only: {f}")

    if cmd == "reel":
        files = files[:2]
        if len(files) == 2 and Path(files[1]).suffix.lower() not in (".jpg", ".jpeg"):
            sys.exit(f"Reel cover must be JPEG: {files[1]}")
    notify = approve(cmd, caption, files, me["username"])
    base = f"{API}/{me['id']}"

    if cmd == "reel":
        params = {**auth, "media_type": "REELS", "video_url": public_url(files[0]), "caption": caption}
        if len(files) == 2:
            params["cover_url"] = public_url(files[1])
        cid = call("POST", f"{base}/media", params)["id"]
    elif len(files) == 1:
        cid = call("POST", f"{base}/media", {**auth, "image_url": public_url(files[0]), "caption": caption})["id"]
    else:
        kids = [call("POST", f"{base}/media", {**auth, "image_url": public_url(f), "is_carousel_item": "true"})["id"]
                for f in files]
        for k in kids:
            wait(token, k)
        cid = call("POST", f"{base}/media",
                   {**auth, "media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]

    wait(token, cid)
    # no retry: a dropped response may hide a publish that went through, and a retry would post twice
    post = call("POST", f"{base}/media_publish", {**auth, "creation_id": cid}, retry=False)
    notify(f"✅ @{me['username']} hesabında paylaşıldı")
    print(f"Published to @{me['username']}, media id {post['id']}")


if __name__ == "__main__":
    main()
