// Meta can only push WhatsApp button taps to a public webhook, and the PC is not reachable from outside.
// This Worker takes the webhook and keeps each answer in KV; ig_post.py reads it from /yanit/<nonce>.
const hex = (s) => Uint8Array.from(s.match(/../g) ?? [], (b) => parseInt(b, 16));

async function signed(body, header, secret) {
  if (!/^sha256=[0-9a-f]{64}$/.test(header ?? "")) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);
  return crypto.subtle.verify("HMAC", key, hex(header.slice(7)), new TextEncoder().encode(body));
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const q = url.searchParams;

    if (url.pathname === "/webhook" && req.method === "GET") {
      const ok = q.get("hub.mode") === "subscribe" && q.get("hub.verify_token") === env.VERIFY_TOKEN;
      return ok ? new Response(q.get("hub.challenge")) : new Response("forbidden", { status: 403 });
    }

    if (url.pathname === "/webhook" && req.method === "POST") {
      const body = await req.text();
      if (!await signed(body, req.headers.get("x-hub-signature-256"), env.APP_SECRET)) {
        return new Response("forbidden", { status: 403 });
      }
      for (const entry of JSON.parse(body).entry ?? []) {
        for (const change of entry.changes ?? []) {
          for (const m of change.value?.messages ?? []) {
            // only the owner's tap on a template button counts
            const hit = m.from === env.OWNER && m.type === "button" && /^(ok|no):([0-9a-f]{8})$/.exec(m.button?.payload);
            if (hit) await env.YANITLAR.put(hit[2], hit[1], { expirationTtl: 7200 });
          }
        }
      }
      return new Response("ok");
    }

    const nonce = /^\/yanit\/([0-9a-f]{8})$/.exec(url.pathname)?.[1];
    if (nonce && req.method === "GET") {
      if (req.headers.get("authorization") !== `Bearer ${env.RELAY_KEY}`) {
        return new Response("forbidden", { status: 403 });
      }
      return new Response((await env.YANITLAR.get(nonce)) ?? "");
    }

    // Instagram fetches media from a public URL. The long random name keeps it private, and it expires with the post run.
    const medya = /^\/medya\/([0-9a-f]{32}\.(jpg|jpeg|mp4))$/.exec(url.pathname);
    if (medya && req.method === "PUT") {
      if (req.headers.get("authorization") !== `Bearer ${env.RELAY_KEY}`) {
        return new Response("forbidden", { status: 403 });
      }
      const data = await req.arrayBuffer();
      if (!data.byteLength) return new Response("empty", { status: 400 });
      await env.YANITLAR.put(`medya:${medya[1]}`, data, { expirationTtl: 7200 });
      return new Response("ok");
    }
    if (medya && (req.method === "GET" || req.method === "HEAD")) {
      const data = await env.YANITLAR.get(`medya:${medya[1]}`, "arrayBuffer");
      if (!data) return new Response("not found", { status: 404 });
      return new Response(data, { headers: { "content-type": medya[2] === "mp4" ? "video/mp4" : "image/jpeg" } });
    }
    return new Response("not found", { status: 404 });
  },
};
