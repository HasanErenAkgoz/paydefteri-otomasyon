"""Run: python yayin/test_whatsapp.py  (no network: Telegram and WhatsApp calls are stubbed)"""
import ig_post as ig

CONFIG = {"token": "t", "phone_id": "1", "to": "905550000000", "relay_url": "https://relay.test", "relay_key": "k"}
sent, edits = [], []


def fake_call(method, url, params, retry=True):
    if url.endswith("/getUpdates"):
        return {"result": []}
    if url.endswith("/sendMessage"):
        sent.append(params["text"])
    if url.endswith("/editMessageText"):
        edits.append(params["text"])
    return {"result": {"message_id": 7}}


def run(config=CONFIG, wa_api=lambda wa, payload: {}, answer="ok", files=("a.jpg",)):
    sent.clear(), edits.clear()
    ig.call, ig.multipart = fake_call, lambda *a, **k: "{}"
    ig.telegram_config = lambda: {"bot_token": "b", "chat_id": 1}
    ig.whatsapp_config = lambda: config
    ig.wa_api, ig.wa_upload, ig.wa_answer = wa_api, lambda wa, path, ctype: "mid", lambda wa, nonce: answer
    ig.Path.read_bytes = lambda self: b""
    return ig.approve("photo", "satır bir\nsatır  iki", list(files), "paydefteri")


# a WhatsApp tap approves, and Telegram shows the result
assert callable(run())
assert edits[-1].startswith("⏳ Onaylandı")

# a WhatsApp rejection stops the post
try:
    run(answer="no")
    raise AssertionError("rejected post went on")
except SystemExit as e:
    assert "Rejected" in str(e)

# a broken WhatsApp must not take Telegram down: the warning reaches Telegram, approval keeps waiting there
def broken(wa, payload):
    raise RuntimeError("token expired")

ig.time.time = iter([0, 0, 9999, 9999]).__next__
try:
    run(wa_api=broken)
    raise AssertionError("no answer still went on")
except SystemExit as e:
    assert "No approval answer" in str(e)
assert "WhatsApp önizlemesi gönderilemedi" in sent[0]

# the template refuses line breaks in variables, and a carousel says its size
assert ig.wa_body("satır bir\nsatır  iki", 3) == "(3 görsel) satır bir satır iki"
assert "\n" not in ig.wa_body("a\n\n\nb" * 900, 1) and len(ig.wa_body("a" * 2000, 1)) <= 900
print("whatsapp ok")
