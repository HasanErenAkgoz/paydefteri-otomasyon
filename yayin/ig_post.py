"""Post to Instagram via the Instagram API with Facebook Login.

Usage:
  python ig_post.py photo "caption" img1.jpg [img2.jpg ...]   # 2-20 images = carousel
  python ig_post.py reel "caption" video.mp4 [cover.jpg]        # cover = grid/profile thumbnail
  python ig_post.py whoami                                     # check token, posts nothing

Every post first goes to Telegram as a preview with Paylaş / İptal buttons, and to WhatsApp too if a
.whatsapp file exists. The script waits up to 1 hour and publishes only after Paylaş on either one
(.telegram holds bot config; .whatsapp holds token, phone_id, to, relay_url, relay_key).

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


def whatsapp_config():
    """The .whatsapp file, or None to approve on Telegram only."""
    f = secret_file(".whatsapp")
    return json.loads(f.read_text()) if f else None
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


def multipart(url, fields, file_field, path, ctype="application/octet-stream", headers={}):
    b = uuid.uuid4().hex
    body = b"".join(
        f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()
    )
    body += (
        f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(url, body, {**UA, **headers, "Content-Type": f"multipart/form-data; boundary={b}"})
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


def wa_api(wa, payload):
    url = f"{API}/{wa['phone_id']}/messages"
    headers = {**UA, "Content-Type": "application/json", "Authorization": f"Bearer {wa['token']}"}
    req = urllib.request.Request(url, json.dumps({"messaging_product": "whatsapp", "to": wa["to"], **payload}).encode(), headers)
    try:
        return json.loads(fetch(req, 60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"WhatsApp API {e.code}: {e.read().decode()[:300]}")


def wa_upload(wa, path, ctype):
    res = multipart(f"{API}/{wa['phone_id']}/media", {"messaging_product": "whatsapp", "type": ctype}, "file", Path(path),
                    ctype, {"Authorization": f"Bearer {wa['token']}"})
    return json.loads(res)["id"]


def wa_body(caption, count):
    # template variables reject line breaks and long space runs
    text = " ".join(caption.split())[:880]
    return f"({count} görsel) {text}" if count > 1 else text


def wa_preview(wa, nonce, caption, files, username):
    """Send the post_onayi template: first JPEG as header, Paylaş / İptal buttons.

    A template is the only message that always arrives. The other media are plain messages, which
    WhatsApp drops when the owner has not written in 24 hours, so the body states the image count.
    """
    jpegs = [f for f in files if f.lower().endswith((".jpg", ".jpeg"))]
    button = lambda i, answer: {"type": "button", "sub_type": "quick_reply", "index": str(i),
                                "parameters": [{"type": "payload", "payload": f"{answer}:{nonce}"}]}
    wa_api(wa, {"type": "template", "template": {"name": "post_onayi", "language": {"code": "tr"}, "components": [
        {"type": "header", "parameters": [{"type": "image", "image": {"id": wa_upload(wa, jpegs[0], "image/jpeg")}}]},
        {"type": "body", "parameters": [{"type": "text", "text": username},
                                        {"type": "text", "text": wa_body(caption, len(jpegs))}]},
        button(0, "ok"), button(1, "no")]}})
    for f in files:
        if f != jpegs[0]:
            kind, ctype = ("video", "video/mp4") if f.lower().endswith(".mp4") else ("image", "image/jpeg")
            wa_api(wa, {"type": kind, kind: {"id": wa_upload(wa, f, ctype)}})


def wa_answer(wa, nonce):
    req = urllib.request.Request(f"{wa['relay_url']}/yanit/{nonce}", headers={**UA, "Authorization": f"Bearer {wa['relay_key']}"})
    try:
        return fetch(req, 30, retry=False).decode()
    except Exception:  # Telegram must keep working while the relay is down
        return ""


def approve(cmd, caption, files, username):
    """Send a preview to Telegram and WhatsApp, block until the owner taps a button. Returns a notify function."""
    tg = telegram_config()
    wa = whatsapp_config()
    api, chat = f"https://api.telegram.org/bot{tg['bot_token']}", int(tg["chat_id"])
    for f in files:
        method, field = ("sendVideo", "video") if f.lower().endswith(".mp4") else ("sendPhoto", "photo")
        if f.startswith("http"):
            call("POST", f"{api}/{method}", {"chat_id": chat, field: f})
        else:
            multipart(f"{api}/{method}", {"chat_id": chat}, field, Path(f))

    nonce = uuid.uuid4().hex[:8]
    warning = ""
    if wa:
        try:
            wa_preview(wa, nonce, caption, files, username)
        except (Exception, SystemExit) as e:  # the Telegram preview above still works
            wa, warning = None, f"\n\n⚠️ WhatsApp önizlemesi gönderilemedi: {str(e)[:200]}"
    buttons = [[{"text": "✅ Paylaş", "callback_data": f"ok:{nonce}"},
                {"text": "❌ İptal", "callback_data": f"no:{nonce}"}]]
    text = f"@{username} hesabına paylaşılsın mı?\n\n{caption}{warning}"
    msg = call("POST", f"{api}/sendMessage",
               {"chat_id": chat, "text": text, "reply_markup": json.dumps({"inline_keyboard": buttons})})["result"]

    def notify(status):
        call("POST", f"{api}/editMessageText",
             {"chat_id": chat, "message_id": msg["message_id"], "text": f"{status}\n\n{caption}"})
        if wa:
            try:
                wa_api(wa, {"type": "text", "text": {"body": status}})
            except Exception:  # a failure here must not look like a failed publish, paylas.py would post again
                pass

    def finish(ok):
        if ok:
            notify("⏳ Onaylandı, paylaşılıyor...")
            return notify
        notify("❌ İptal edildi")
        sys.exit("Rejected at approval, nothing posted")

    offset, deadline = 0, time.time() + 3600
    while time.time() < deadline:
        updates = call("GET", f"{api}/getUpdates",
                       {"offset": offset, "timeout": 5 if wa else 50, "allowed_updates": '["callback_query"]'})["result"]
        for u in updates:
            offset = u["update_id"] + 1
            q = u.get("callback_query")
            # only the owner's tap on this exact preview counts
            if not q or q["from"]["id"] != chat or q.get("data", "")[3:] != nonce:
                continue
            call("POST", f"{api}/answerCallbackQuery", {"callback_query_id": q["id"]})
            return finish(q["data"].startswith("ok:"))
        answer = wa_answer(wa, nonce) if wa else ""
        if answer in ("ok", "no"):
            return finish(answer == "ok")
    notify("⌛ 1 saat içinde cevap gelmedi, paylaşılmadı")
    sys.exit("No approval answer within 1 hour, nothing posted")


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
