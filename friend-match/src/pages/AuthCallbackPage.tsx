// src/pages/AuthCallbackPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("Signing you in…");

  useEffect(() => {
    let alive = true;

    (async () => {
      const hash = window.location.hash.replace(/^#/, "");
      const p = new URLSearchParams(hash);

      // Supabase can put errors in the hash
      const err = p.get("error");
      if (err) {
        const desc = decodeURIComponent(p.get("error_description") || "Link invalid or expired.");
        if (!alive) return;
        setMessage(desc);
        return;
      }

      const access_token = p.get("access_token");
      const refresh_token = p.get("refresh_token");

      // If magic link returned tokens, explicitly set session
      if (access_token && refresh_token) {
        const { error } = await supabase.auth.setSession({ access_token, refresh_token });
        if (error) {
          if (!alive) return;
          setMessage(error.message);
          return;
        }

        // Remove tokens from URL for safety
        window.history.replaceState({}, document.title, "/auth/callback");
      }

      // Confirm session exists, then go survey
      const { data } = await supabase.auth.getSession();
      if (!alive) return;

      if (data.session) navigate("/survey", { replace: true });
      else navigate("/login", { replace: true });
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return <p style={{ padding: 16 }}>{message}</p>;
}
