// src/pages/DashboardPage.tsx
import "./DashboardPage.css";

import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient"; // adjust if needed
type MatchRow = {
  id: string;
  user_low: string;
  user_high: string;
  user_low_name: string | null;
  user_high_name: string | null;
  compatibility_reasons: string | null;
  round_id: string | null;
  created_at: string;
  emailed_at: string | null;
};
const fmtDate = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
};
const DashboardPage: React.FC = () => {
  
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(true); // source of truth for UI
  const [error, setError] = useState<string>("");
  const [profile, setProfile] = useState<any>(null);

  // Matches state
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [matchesError, setMatchesError] = useState<string>("");
  const [matches, setMatches] = useState<MatchRow[]>([]);
  const [userId, setUserId] = useState<string | null>(null);

  //terms of use state
  const [needsTerms, setNeedsTerms] = useState(false);
  const [agreeChecked, setAgreeChecked] = useState(false);
  const [savingTerms, setSavingTerms] = useState(false);

  

  useEffect(() => {
    const load = async () => {
      setError("");
      setLoading(true);

      const { data: authData, error: authErr } = await supabase.auth.getUser();
      if (authErr || !authData?.user) {
        setLoading(false);
        navigate("/login");
        return;
      }

      const userId = authData.user.id;
      setUserId(userId);
     
const { data: prof, error: profErr } = await supabase
  .from("profiles")
  .select("id, active, agreed_to_terms") // log only what you need
  .eq("id", userId)
  .maybeSingle();

if (profErr) {
  console.error("Failed to load profile:", profErr);
  setError(profErr.message);
  setLoading(false);
  return;
}

if (!prof) {
  console.error(
    "[Invariant violated] User reached dashboard but no profile row exists",
    { userId }
  );
  setError("Profile not found. Please log out and log back in.");
  setLoading(false);
  return;
}
//check if user agreed to terms of use
setNeedsTerms(!prof.agreed_to_terms);



// Normal path
setProfile(prof);
setActive(prof.active !== false);
setLoading(false);
  };
    load();
  }, [navigate]);

const handleAgreeTerms = async () => {
  if (!agreeChecked) return;

  setSavingTerms(true);

  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    setSavingTerms(false);
    return;
  }

  const { error } = await supabase
    .from("profiles")
    .update({
      agreed_to_terms: true,
      date_agreed: new Date().toISOString(),
    })
    .eq("id", user.id);

  setSavingTerms(false);

  if (error) {
    alert("Could not save agreement. Try again.");
    return;
  }

  setNeedsTerms(false);
};

useEffect(() => {
  if (!profile) return;
  if (profile.onboarding_email_sent) return;

  const send = async () => {
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("[Onboarding] getSession error:", error);
        return;
      }

      const token = data.session?.access_token;
      if (!token) return;

      const res = await fetch("/api/send-onboarding-email", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const text = await res.text();
        console.error("[Onboarding] API failed:", res.status, text);
      } else {
        console.log("[Onboarding] sent (or skipped)");
        // Optional: update local state to avoid calling again this session
        setProfile((p: any) => (p ? { ...p, onboarding_email_sent: true } : p));
      }
    } catch (e) {
      console.error("[Onboarding] unexpected error:", e);
    }
  };

  send();
}, [profile]);

useEffect(() => {
  if (!userId) return;

  const loadMatches = async () => {
    setMatchesError("");
    setMatchesLoading(true);

    const { data, error } = await supabase
      .from("matches")
      .select(
        "id,user_low,user_high,user_low_name,user_high_name,compatibility_reasons,round_id,created_at,emailed_at"
      )
      .or(`user_low.eq.${userId},user_high.eq.${userId}`)
      .order("created_at", { ascending: false });

    if (error) {
      console.error("[Matches] load error:", error);
      setMatchesError(error.message);
      setMatchesLoading(false);
      return;
    }

    setMatches((data ?? []) as MatchRow[]);
    setMatchesLoading(false);
  };

  loadMatches();
}, [userId]);


  const togglePauseResume = async () => {
    setError("");

    const { data: authData, error: authErr } = await supabase.auth.getUser();
    if (authErr || !authData?.user) {
      navigate("/login");
      return;
    }
    const userId = authData.user.id;

    const nextActive = !active;

    const { error: updErr } = await supabase
      .from("profiles")
      .update({ active: nextActive })
      .eq("id", userId);

    if (updErr) {
      setError(updErr.message);
      return;
    }

    setActive(nextActive);
  };

  const handleUpdatePreference = () => {
    navigate("/survey?mode=update&returnTo=/dashboard");
  };

  const paused = !active;

  const displayMatches = useMemo(() => {
    if (!userId) return [];
    return matches.map((m) => {
      const isLowMe = m.user_low === userId;
      const otherName = (isLowMe ? m.user_high_name : m.user_low_name) || "Your match";
      const myName = (isLowMe ? m.user_low_name : m.user_high_name) || "You";
      const emailed = !!m.emailed_at;
      return { ...m, otherName, myName, emailed };
    });
  }, [matches, userId]);

  return (
    <div className="dashboard">

      {/* ✅ Terms modal (renders only when needsTerms is true) */}
    {needsTerms && (
      <div className="terms-modal-overlay" role="dialog" aria-modal="true">
        <div className="terms-modal">
          <h2 className="terms-modal-title">Terms of Service</h2>

          <p className="terms-modal-text">
            We’ve added Terms of Service to clarify how Genuinely works. Please review and agree to continue to use the platform and receive matches.
          </p>

          <p className="terms-modal-text">
            <a
              className="terms-modal-link"
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
            >
              Read Terms of Service
            </a>{" "}
            (opens in a new tab)
          </p>

          <label className="terms-modal-consent">
            <input
              type="checkbox"
              checked={agreeChecked}
              onChange={(e) => setAgreeChecked(e.target.checked)}
            />
            <span>I agree to the Terms of Service</span>
          </label>

          {/* ✅ HERE is where the handler is called */}
          <button
            className="terms-modal-btn"
            type="button"
            onClick={handleAgreeTerms}
            disabled={!agreeChecked || savingTerms}
          >
            {savingTerms ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    )}{/* ✅ Terms modal (renders only when needsTerms is true) */}
    {needsTerms && (
      <div className="terms-modal-overlay" role="dialog" aria-modal="true">
        <div className="terms-modal">
          <h2 className="terms-modal-title">Terms of Service</h2>

          <p className="terms-modal-text">
            We’ve added Terms of Service to clarify how Genuinely works. Please review and agree to continue.
          </p>

          <p className="terms-modal-text">
            <a
              className="terms-modal-link"
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
            >
              Read Terms of Service
            </a>{" "}
            (opens in a new tab)
          </p>

          <label className="terms-modal-consent">
            <input
              type="checkbox"
              checked={agreeChecked}
              onChange={(e) => setAgreeChecked(e.target.checked)}
            />
            <span>I agree to the Terms of Service</span>
          </label>

          {/* ✅ HERE is where the handler is called */}
          <button
            className="terms-modal-btn"
            type="button"
            onClick={handleAgreeTerms}
            disabled={!agreeChecked || savingTerms}
          >
            {savingTerms ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    )}

      <header className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Dashboard</h1>
          <p className="dashboard-subtitle">
            {loading
              ? "Loading your status..."
              : paused
              ? "Matching is paused. You won’t receive new matches until you resume."
              : "Your matches will appear here, and we’ll also email them to your inbox ✨"}
          </p>
          {error && <p className="error-text">{error}</p>}
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            type="button"
            className={`pause-btn ${paused ? "pause-btn--active" : ""}`}
            onClick={togglePauseResume}
            disabled={loading}
          >
            {paused ? "Resume Matching" : "Pause Matching"}
          </button>

          <button type="button" className="secondary-btn" onClick={handleUpdatePreference} disabled={loading}>
            Update Preference
          </button>
        </div>
      </header>

      <p className="email-note">
        📬 <strong>Email notice:</strong> UCSD Gmail may classify emails from new or unfamiliar domains as spam. During your first time logging in, we’ve
        just sent you a short onboarding email explaining how Genuinely works — if you don’t see it, please check your
        spam folder and mark it as <em>Not spam</em> 🫶.
        <br />
        <br />
        Your matches will appear here on the dashboard and will also be sent to your email, but for security reason, you will only see the contact info of your match in the notification email and not on the dashboard. To make sure you don’t miss
        them, please move emails from <strong>@genuinely.life</strong> to your inbox 🫰.
      </p>

      <main className="dashboard-main">
        <section className="matches-panel">
          <div className="matches-panel__header">
            <h2 className="matches-panel__title">Your Matches</h2>
            <p className="matches-panel__subtitle">A history of who you’ve been matched with.</p>
          </div>

          {matchesLoading ? (
            <div className="matches-empty">
              <p style={{ margin: 0 }}>Loading your matches…</p>
            </div>
          ) : matchesError ? (
            <div className="matches-empty">
              <p className="error-text" style={{ margin: 0 }}>
                Failed to load matches: {matchesError}
              </p>
            </div>
          ) : displayMatches.length === 0 ? (
            <div className="matches-empty">
              <p style={{ margin: 0 }}>
                {paused
                  ? "You’re paused. Resume anytime to receive new matches."
                  : "No matches yet — check back later. We’ll email you when you get one."}
              </p>
            </div>
          ) : (
            <div className="matches-grid">
              {displayMatches.map((m) => (
                <article key={m.id} className="match-card">
                  <div className="match-card__top">
                    <div>
                      <h3 className="match-card__name">{m.otherName}</h3>
                      <p className="match-card__meta">
                        Matched on <strong>{fmtDate(m.created_at)}</strong>
                        {m.round_id ? (
                          <>
                            {" "}
                            • Round <strong>{m.round_id}</strong>
                          </>
                        ) : null}
                      </p>
                    </div>

                    <span className={`match-badge ${m.emailed ? "match-badge--sent" : "match-badge--pending"}`}>
                      {m.emailed ? `Intro emailed ${fmtDate(m.emailed_at)}` : "Intro not emailed yet"}
                    </span>
                  </div>

                  {m.compatibility_reasons ? (
                    <p className="match-card__reasons">
                      <strong>Why you matched:</strong> {m.compatibility_reasons}
                    </p>
                  ) : (
                    <p className="match-card__reasons">
                      <strong>Why you matched:</strong> Shared interests and preferences.
                    </p>
                  )}

                  <div className="match-card__actions">
                    {/* Optional: add buttons later */}
                    {/* <button className="secondary-btn">Resend intro</button> */}
                    {/* <button className="secondary-btn">Reveal email</button> */}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
      <footer className="dashboard-footer">
        <div className="dashboard-footer-inner">
          <p className="dashboard-footer-text">
            © 2026 Genuinely. Student-led project.
          </p>

          <div className="dashboard-footer-links">
            <a
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="dashboard-footer-link"
            >
              Terms of Service
            </a>

            <span className="footer-sep">•</span>

            <a
              href="mailto:contact@send.genuinely.life"
              className="dashboard-footer-link"
            >
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default DashboardPage;
