
//Send user a boring email to train them to look in spam because evil 
//ucsd email spam classifier

import type { VercelRequest, VercelResponse } from "@vercel/node";
import { Resend } from "resend";
import { createClient } from "@supabase/supabase-js";

const resend = new Resend(process.env.RESEND_API_KEY);

const supabaseAdmin = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

    // 1) Verify the caller is the logged-in user (JWT from client)
    const authHeader = req.headers.authorization || "";
    const jwt = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
    if (!jwt) return res.status(401).json({ error: "Missing Authorization bearer token" });

    const { data: userData, error: userErr } = await supabaseAdmin.auth.getUser(jwt);
    if (userErr || !userData?.user) return res.status(401).json({ error: "Invalid token" });

    const userId = userData.user.id;

    // 2) Load profile + check if already sent
    const { data: profile, error: profErr } = await supabaseAdmin
      .from("profiles")
      .select("email, onboarding_email_sent")
      .eq("id", userId)
      .single();

    if (profErr || !profile?.email) {
      return res.status(400).json({ error: "Profile missing email" });
    }

    if (profile.onboarding_email_sent) {
      return res.status(200).json({ status: "already_sent" });
    }

    // 3) Send boring onboarding email
    const to = profile.email;
    const from = "matches@send.genuinely.life"

    const subject = "Welcome to Genuinely";
    const text = [
      "Hi,",
      "",
      "You are receiving this email because you submitted the Genuinely survey using this email address.",
      "",
      "How Genuinely works:",
      "- You completed a short survey about your preferences and interests.",
      "- We periodically match you with another verified UCSD student.",
      "- Our system compares responses and identifies users with similar traits and interests.",
      "- To allow enough participants in the matching pool, we will send you your match every 4 days.",
      "- When a match is available, it will appear in your dashboard and you will receive an email notification.",
      "",
      "If you do not see future messages from us, please check your spam folder and mark emails from @send.genuinely.life as not spam.",
      "",
      "If you did not submit the survey, you may safely ignore this message.",
      "",
      "— Genuinely",
    ].join("\n");

    const send = await resend.emails.send({
      from: `Genuinely <${from}>`,
      to,
      subject,
      text,
    });

    if (send.error) {
    console.log("failed inside resend")
      return res.status(500).json({ error: send.error.message });
    }

    // 4) Mark as sent (idempotent)
    const { error: updErr } = await supabaseAdmin
      .from("profiles")
      .update({ onboarding_email_sent: true })
      .eq("id", userId);

    if (updErr) {
      // Email sent but flag update failed — log it; you can fix manually.
      return res.status(500).json({ error: "Email sent, but failed to update flag" });
    }

    return res.status(200).json({ status: "sent" });
  } catch (e) {
    console.error("[send-onboarding-email] fatal:", e);
    return res.status(500).json({
      error: e instanceof Error ? e.message : String(e),
    });
  }
}
