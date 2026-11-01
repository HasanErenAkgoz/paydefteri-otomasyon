// Run: node whatsapp-relay/worker.test.mjs
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import worker from "./worker.js";

const store = new Map();
const env = {
  VERIFY_TOKEN: "dogrula", APP_SECRET: "gizli", RELAY_KEY: "anahtar", OWNER: "905550000000",
  YANITLAR: { put: async (k, v) => store.set(k, v), get: async (k) => store.get(k) ?? null },
};
const base = "https://relay.test";
const tap = (from, payload) => JSON.stringify({ entry: [{ changes: [{ value: { messages: [
  { from, type: "button", button: { payload } },
] } }] }] });
const post = (body, secret = env.APP_SECRET) => worker.fetch(new Request(`${base}/webhook`, {
  method: "POST", body,
  headers: { "x-hub-signature-256": `sha256=${createHmac("sha256", secret).update(body).digest("hex")}` },
}), env);
const read = (nonce, key = env.RELAY_KEY) => worker.fetch(new Request(`${base}/yanit/${nonce}`, {
  headers: { authorization: `Bearer ${key}` },
}), env);

// Meta's subscribe handshake
let r = await worker.fetch(new Request(`${base}/webhook?hub.mode=subscribe&hub.verify_token=dogrula&hub.challenge=42`), env);
assert.equal(await r.text(), "42");
r = await worker.fetch(new Request(`${base}/webhook?hub.mode=subscribe&hub.verify_token=yanlis&hub.challenge=42`), env);
assert.equal(r.status, 403);

// a forged signature stores nothing
assert.equal((await post(tap(env.OWNER, "ok:aaaaaaaa"), "sahte")).status, 403);
assert.equal(store.size, 0);

// a stranger or a free-typed payload stores nothing
await post(tap("905551111111", "ok:aaaaaaaa"));
await post(tap(env.OWNER, "evet:aaaaaaaa"));
assert.equal(store.size, 0);

// the owner's tap reaches the reader, and only with the key
await post(tap(env.OWNER, "ok:aaaaaaaa"));
assert.equal(await (await read("aaaaaaaa")).text(), "ok");
assert.equal((await read("aaaaaaaa", "yanlis")).status, 403);
assert.equal(await (await read("bbbbbbbb")).text(), "");

// media needs the key to go up, is public to come down, and an empty upload is refused
const name = `${"a".repeat(32)}.jpg`;
const put = (body, key = env.RELAY_KEY) => worker.fetch(new Request(`${base}/medya/${name}`, {
  method: "PUT", body, headers: { authorization: `Bearer ${key}` },
}), env);
assert.equal((await put(new Uint8Array([1, 2, 3]), "yanlis")).status, 403);
assert.equal((await worker.fetch(new Request(`${base}/medya/${name}`), env)).status, 404);
assert.equal((await put(new Uint8Array())).status, 400);
assert.equal((await put(new Uint8Array([1, 2, 3]))).status, 200);
r = await worker.fetch(new Request(`${base}/medya/${name}`), env);
assert.equal(r.headers.get("content-type"), "image/jpeg");
assert.deepEqual([...new Uint8Array(await r.arrayBuffer())], [1, 2, 3]);

console.log("worker ok");
