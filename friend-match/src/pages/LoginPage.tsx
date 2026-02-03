// src/pages/LoginPage.tsx
import "./LoginPage.css";
import React, { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";

const OTP_LEN = 6;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");

  const [step, setStep] = useState<"email" | "code">("email");

  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  // Store per-digit state to power the UI
  const [otp, setOtp] = useState<string[]>(Array(OTP_LEN).fill(""));

  // Refs to move focus
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);

  const fullCode = useMemo(() => otp.join(""), [otp]);

  const focusAt = (i: number) => {
    const el = inputRefs.current[i];
    el?.focus();
    el?.select();
  };

  const resetOtp = () => {
    setOtp(Array(OTP_LEN).fill(""));
   
    // focus first digit next tick
    setTimeout(() => focusAt(0), 0);
  };

  const sendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");

    const trimmedEmail = email.trim().toLowerCase();

    if (!trimmedEmail.endsWith("@ucsd.edu")) {
      setError("Please use your UCSD email address (must end with @ucsd.edu).");
      return;
    }

    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email: trimmedEmail,
      options: { shouldCreateUser: true },
    });
    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    setStep("code");
    setInfo("We sent a 6-digit code to your email. You’ll stay signed in on this device.");
    resetOtp();
  };

  const verifyCode = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError("");
    setInfo("");

    const trimmedEmail = email.trim().toLowerCase();
    const trimmedCode = fullCode.trim();

    if (trimmedCode.length !== OTP_LEN) {
      setError("Please enter the 6-digit code.");
      return;
    }

    setLoading(true);
    const { data, error } = await supabase.auth.verifyOtp({
      email: trimmedEmail,
      token: trimmedCode,
      type: "email",
    });
    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    if (data.session) {
      navigate("/survey", { replace: true });
    } else {
      setError("Signed in, but no session found. Please try again.");
    }
  };

  const resend = async () => {
    setError("");
    setInfo("");
    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim().toLowerCase(),
      options: { shouldCreateUser: true },
    });
    setLoading(false);

    if (error) setError(error.message);
    else {
      setInfo("New code sent.");
      resetOtp();
    }
  };

  // ---- OTP box handlers ----

  const handleOtpChange = (index: number, raw: string) => {
    // Allow only digits. Take last typed digit.
    const digit = raw.replace(/\D/g, "").slice(-1) ?? "";

    const next = [...otp];
    next[index] = digit;
    setOtp(next);
   

    if (digit && index < OTP_LEN - 1) {
      focusAt(index + 1);
    }

    // Optional: auto-submit when complete
    if (next.join("").length === OTP_LEN && next.every((d) => d !== "")) {
      // don't block UI; just attempt verify
      void verifyCode();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (otp[index]) {
        // clear current digit
        const next = [...otp];
        next[index] = "";
        setOtp(next);
   
        return;
      }
      // if already empty, move back
      if (index > 0) {
        focusAt(index - 1);
        const next = [...otp];
        next[index - 1] = "";
        setOtp(next);
      
      }
      return;
    }

    if (e.key === "ArrowLeft" && index > 0) focusAt(index - 1);
    if (e.key === "ArrowRight" && index < OTP_LEN - 1) focusAt(index + 1);
  };

  const handleOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const text = e.clipboardData.getData("text");
    const digits = text.replace(/\D/g, "").slice(0, OTP_LEN).split("");
    if (digits.length === 0) return;

    e.preventDefault();

    const next = Array(OTP_LEN).fill("");
    for (let i = 0; i < OTP_LEN; i++) next[i] = digits[i] ?? "";

    setOtp(next);
   

    const firstEmpty = next.findIndex((d) => d === "");
    if (firstEmpty === -1) {
      focusAt(OTP_LEN - 1);
      void verifyCode();
    } else {
      focusAt(firstEmpty);
    }
  };

  return (
  <main className="login-page">
    <div className="login-card">
      <h1 className="login-title">Log in</h1>

      {error && <p className="error">{error}</p>}
      {info && <p className="info">{info}</p>}

      {step === "email" ? (
        <form className="login-form" onSubmit={sendCode}>
          <label className="login-label">
            UCSD Email
            <input
              className="login-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@ucsd.edu"
              required
              disabled={loading}
            />
          </label>

          <button className="login-primary" type="submit" disabled={loading}>
            {loading ? "Sending…" : "Send code"}
          </button>
        </form>
      ) : (
        <form className="login-form" onSubmit={verifyCode}>
          <p className="login-subtext">
            Code sent to <strong>{email.trim().toLowerCase()}</strong>
          </p>

          <div className="otp-row" aria-label="6-digit code">
            {otp.map((val, i) => (
              <input
                key={i}
                ref={(el) => {
                  inputRefs.current[i] = el;
                }}
                className="otp-box"
                value={val}
                onChange={(e) => handleOtpChange(i, e.target.value)}
                onKeyDown={(e) => handleOtpKeyDown(i, e)}
                onPaste={handleOtpPaste}
                inputMode="numeric"
                autoComplete={i === 0 ? "one-time-code" : "off"}
                maxLength={1}
                aria-label={`Digit ${i + 1}`}
                disabled={loading}
              />
            ))}
          </div>

          <button className="login-primary" type="submit" disabled={loading}>
            {loading ? "Verifying…" : "Verify & continue"}
          </button>

          <div className="login-actions">
            <button className="login-secondary" type="button" onClick={resend} disabled={loading}>
              Resend code
            </button>

            <button
              className="login-secondary"
              type="button"
              onClick={() => {
                setStep("email");
                setInfo("");
                setError("");
              }}
              disabled={loading}
            >
              Use a different email
            </button>
          </div>
        </form>
      )}
    </div>
  </main>
);

};

export default LoginPage;
