import type { VercelRequest, VercelResponse } from "@vercel/node";
import crypto from "crypto";

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY!;
//const SECRET = process.env.FEEDBACK_SIGNING_SECRET!;
const SECRET = process.env.FEEDBACK_SIGNING_SECRET!;
function b64urlDecodeToString(input: string) {
  // pad base64 if needed
  const pad = input.length % 4 === 0 ? "" : "=".repeat(4 - (input.length % 4));
  const b64 = (input + pad).replace(/-/g, "+").replace(/_/g, "/");
  return Buffer.from(b64, "base64").toString("utf8");
}

function b64urlEncode(buf: Buffer) {
  return buf.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function timingSafeEqual(a: string, b: string) {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

function verifyToken(token: string) {
  const parts = token.split(".");
  if (parts.length !== 2) throw new Error("Bad token format");

  const payloadB64 = parts[0];
  const sigB64 = parts[1];

  const expected = crypto.createHmac("sha256", SECRET).update(payloadB64).digest();
  const expectedB64 = b64urlEncode(expected);

  if (!timingSafeEqual(sigB64, expectedB64)) throw new Error("Invalid signature");

  const payloadJson = b64urlDecodeToString(payloadB64);
  const payload = JSON.parse(payloadJson) as {
    match_id: string;
    rater_id: string;
    rating: "like" | "dislike";
    exp: number;
  };

  if (!payload.match_id || !payload.rater_id || !payload.rating || !payload.exp) {
    throw new Error("Missing payload fields");
  }

  if (payload.rating !== "like" && payload.rating !== "dislike") {
    throw new Error("Invalid rating");
  }

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp < now) throw new Error("Token expired");

  return payload;
}

async function supabaseInsertFeedback(match_id: string, rater_id: string, rating: "like" | "dislike") {
  // Insert into feedback with service role key
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/feedback`, {
    method: "POST",
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "resolution=merge-duplicates,return=representation",
    },
    body: JSON.stringify({ match_id, rater_id, rating }),
  });

  const text = await resp.text();
  if (!resp.ok) {
    // Common case: unique constraint match_feedback_one_per_user violated
    // Supabase returns a JSON error string; we just pass it through.
    throw new Error(text || `Supabase insert failed (${resp.status})`);
  }
  return text;
}

function htmlPage(title: string, body: string) {
  return `<!doctype html>
  <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>${title}</title>
      <style>
        body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0b1020;color:#e7e9ee;margin:0;padding:32px}
        .card{max-width:640px;margin:0 auto;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:20px}
        a{color:#93c5fd}
      </style>
    </head>
    <body>
      <div class="card">
        ${body}
      </div>
    </body>
  </html>`;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    const token = typeof req.query.token === "string" ? req.query.token : "";
    if (!token) {
      res.status(400).send(htmlPage("Missing token", `<h2>Missing link token</h2><p>Please use the buttons from the email.</p>`));
      return;
    }

    const { match_id, rater_id, rating } = verifyToken(token);

    await supabaseInsertFeedback(match_id, rater_id, rating);

    res
      .status(200)
      .setHeader("Content-Type", "text/html")
      .send(
        htmlPage(
          "Thanks!",
          `<h2>Thanks — feedback saved ✅</h2>
           <p>You selected: <strong>${rating}</strong>.</p>
           <p>You can close this tab now.</p>`
        )
      );
  } catch (err: any) {
    // If already rated, unique constraint will throw. We can show a nicer message.
    const msg = String(err?.message || "Unknown error");
    const already = msg.includes("match_feedback_one_per_user") || msg.includes("duplicate key");
    const body = already
      ? `<h2>You already rated this match ✅</h2><p>No worries — we recorded your earlier response.</p>`
      : `<h2>Link failed</h2><p>${msg}</p><p>Please request a new email link.</p>`;

    res.status(400).setHeader("Content-Type", "text/html").send(htmlPage("Link failed", body));
  }
}
