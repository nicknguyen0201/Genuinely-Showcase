import React, { useEffect, useState} from "react";
import { createClient } from "@supabase/supabase-js";
import { useLocation, useNavigate } from "react-router-dom";
import "./SurveyPage.css";


const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true, // important for magic links
    },
  }
);





const SurveyPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [needsLogin, setNeedsLogin] = useState(false);
  
  const location = useLocation();
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const params = new URLSearchParams(location.search);
  const mode = params.get("mode");                  // "update" or null
  const isUpdateFlow = mode === "update";           // ✅
 
  useEffect(() => {
  let alive = true;

  const run = async () => {
    setLoading(true);
    setNeedsLogin(false);

    // ✅ Check auth
    const { data: { user }, error: userErr } = await supabase.auth.getUser();
    if (!alive) return;

    if (userErr) {
      console.error("[SurveyRoute] getUser error:", userErr);
      setNeedsLogin(true);
      setLoading(false);
      return;
    }

    if (!user) {
      setNeedsLogin(true);
      setLoading(false);
      return;
    }

    // ✅ If user came from dashboard to update, stay on /survey
    if (isUpdateFlow) {
      console.log("[SurveyRoute] update flow → stay on /survey");
      setLoading(false);
      return;
    }

    const userId = user.id;

    // ✅ Check if profile already exists
    const { data, error } = await supabase
      .from("profiles")
      .select("id")
      .eq("id", userId)
      .maybeSingle();

    if (!alive) return;

    if (error) {
      console.error("[SurveyRoute] profile check failed:", error);
      // If it fails, let them stay on survey instead of blocking
      setLoading(false);
      return;
    }

    if (data?.id) {
      console.log("[SurveyRoute] profile exists → redirect to /dashboard");
      navigate("/dashboard", { replace: true });
      return;
    }

    console.log("[SurveyRoute] profile missing → stay on /survey");
    setLoading(false);
  };

  run();

  return () => {
    alive = false;
  };
}, [navigate, isUpdateFlow]);
if (loading) return <p>Checking your session…</p>;

if (needsLogin) {
  return (
    <p>
      Please log in first at <a href="/">/login</a>.
    </p>
  );
}

  

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  const form = e.currentTarget;
  if (!form.reportValidity()) return;

  // ✅ Get the logged-in user at submit time (works after /auth/callback setSession)
  const { data: { user }, error: userErr } = await supabase.auth.getUser();
  if (userErr || !user) {
    alert("Your session expired. Please log in again.");
    navigate("/login", { replace: true });
    return;
  }

  const userId = user.id;
  const email = (user.email ?? "").toLowerCase();

  const formData = new FormData(form);
  const raw = Object.fromEntries(formData.entries()) as Record<string, string>;

  const name = (raw.name as string).trim();
  if (!name || name.length > 50) {
    alert("Please enter your name (max 50 chars).");
    return;
  }

  const gender = raw.gender;
  const year = raw.year;
  if (!gender || !year) {
    alert("Please fill out gender and year.");
    return;
  }

  const sameGender = raw.friendSameGender === "yes" ? 1 : 0;
  const sameYear   = raw.matchSameYear === "yes" ? 1 : 0;

  const featureVector = buildFeatureVector(raw);

  const {  error } = await supabase
    .from("profiles")
    .upsert(
      {
        id: userId, // ✅ tied to auth uid
        email,      // store for convenience/display (not for security)
        name,
        survey_vec: featureVector,
        same_gender: sameGender,
        same_year: sameYear,
        active: true,
        updated_at: new Date().toISOString(),
        agreed_to_terms: true,
        date_agreed: new Date().toISOString(),
      },
      { onConflict: "id" }
    );

  if (error) {
    console.error("❌ Supabase upsert failed:", error);
    alert("Something went wrong saving your survey.");
    return;
  }
  

  alert("✅ Survey submitted successfully!");
  form.reset();
  navigate("/dashboard");
};


const vibeQuestions = [
  { id: "introvert", label: "Introvert" },
  { id: "extrovert", label: "Extrovert" },
  { id: "spontaneous", label: "Spontaneous" },
  { id: "planner", label: "Plan (likes planning ahead)" },
  { id: "indoor", label: "Indoor (homebody vibes)" },
  { id: "adventurous", label: "Adventurous" },
];

const interestQuestions = [
  { id: "studyTogether", label: "Study together" },
  { id: "gaming", label: "Gaming" },
  { id: "eatOutCooking", label: "Eat out / cooking" },
  { id: "exploreSD", label: "Explore San Diego" },
  { id: "shoppingFashion", label: "Shopping / fashion" },
  { id: "chillHangouts", label: "Chill hangouts (Netflix, Glider Port late stroll)" },
  { id: "partying", label: "Partying" },
  { id: "music", label: "Music (K-pop, Taylor Swift, etc.)" },
  { id: "fitness", label: "Fitness (gym)" },
  { id: "ucsdTypicals", label: "UCSD typicals (Trader Joe's run, Price Center lunch, La Jolla Shores)" },
  { id: "artDrawing", label: "Art / drawing" },
  { id: "anime", label: "Anime" },
  { id: "movies", label: "Movies" },
  { id: "outdoorActivities", label: "Outdoor activities (hiking, biking, climbing, etc.)" },
  { id: "entrepreneurship", label: "Entrepreneurship" },
  { id: "tech", label: "Tech" },
];
// Build a fixed-order feature vector from form data
const buildFeatureVector = (data: Record<string, string>): number[] => {
  const vector: number[] = [];

  // ---- Gender one-hot (4 dims) ----
  const gender = data.gender;
  const genderOptions = ["male", "female", "non-binary", "other"] as const;
  genderOptions.forEach((g) => vector.push(gender === g ? 1 : 0));

  // ---- Year one-hot (6 dims) ----
  const year = data.year;
  const yearOptions = ["freshman", "sophomore", "junior", "junior-transfer", "senior", "grad"] as const;
  yearOptions.forEach((y) => vector.push(year === y ? 1 : 0));

  // ---- Vibes (6 dims) ----
  vibeQuestions.forEach((q) => vector.push(data[q.id] === "yes" ? 1 : 0));

  // ---- Interests (16 dims) ----
  interestQuestions.forEach((q) => vector.push(data[q.id] === "yes" ? 1 : 0));

  // ---- Bias dim to reach 33 features ----
  vector.push(1);

  return vector; // total = 4 + 6 + 6 + 16 + 1 = 33
};

  return (
  <main className="survey-page">
    <div className="survey-shell">
      <header className="survey-hero">
        <h1 className="survey-title">Genuinely Friend Match – Survey</h1>
        <p className="survey-subtitle">
          Tell us about yourself so we can match you with friends who vibe with you.
        </p>
      </header>

      <form className="survey-card" onSubmit={handleSubmit}>
        {/* ---------------- Basic Info ---------------- */}
        <section className="survey-section">
          <h2 className="section-title">Basic info</h2>

          <div className="field">
            <label className="label" htmlFor="name">
              What is your name?
            </label>
            <input
              className="input"
              id="name"
              name="name"
              type="text"
              required
              maxLength={50}
              placeholder="Preferred name"
            />
            <p className="hint">Max 50 characters.</p>
          </div>

          <div className="field">
            <label className="label" htmlFor="gender">
              1. What is your gender?
            </label>
            <select className="select" id="gender" name="gender" required>
              <option value="">Select your gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Same-gender preference */}
          <div className="pref-block">
            <p className="pref-title">Do you prefer friends of the same gender?</p>
            

            <div className="pills">
              <label className="pill pill--yes">
                <input type="radio" name="friendSameGender" value="yes" required />
           
                <span className="pill-label">Yes</span>
              </label>

              <label className="pill pill--no">
                <input type="radio" name="friendSameGender" value="no" />
        
                <span className="pill-label">Any</span>
              </label>
            </div>
          </div>

          <div className="field">
            <label className="label" htmlFor="year">
              2. What year are you?
            </label>
            <select className="select" id="year" name="year" required>
              <option value="">Select your year</option>
              <option value="freshman">Freshman</option>
              <option value="sophomore">Sophomore</option>
              <option value="junior">Junior</option>
              <option value="junior-transfer">Junior transfer</option>
              <option value="senior">Senior</option>
              <option value="grad">Grad</option>
            </select>
          </div>

          {/* Same-year preference */}
          <div className="pref-block">
            <p className="pref-title">Do you prefer to match with someone of the same year?</p>
          
            <div className="pills">
              <label className="pill pill--yes">
                <input type="radio" name="matchSameYear" value="yes" required />
                
                <span className="pill-label">Yes</span>
              </label>

              <label className="pill pill--no">
                <input type="radio" name="matchSameYear" value="no" />
              
                <span className="pill-label">Any</span>
              </label>
            </div>
          </div>
        </section>

        {/* ---------------- Vibes ---------------- */}
        <section className="survey-section">
          <h2 className="section-title">Vibes</h2>
          <p className="section-help">Click Yes if it fits you, otherwise No.</p>

          {vibeQuestions.map((q, i) => (
            <div className="q-row" key={q.id}>
              <p className="q-text">
                {i + 3}. {q.label}
              </p>

              <div className="pills">
                <label className="pill pill--yes">
                  <input type="radio" name={q.id} value="yes" required />
                  
                  <span className="pill-label">Yes</span>
                </label>

                <label className="pill pill--no">
                  <input type="radio" name={q.id} value="no" />
              
                  <span className="pill-label">No</span>
                </label>
              </div>
            </div>
          ))}
        </section>

        {/* ---------------- Interests ---------------- */}
        <section className="survey-section">
          <h2 className="section-title">Common interests</h2>
          <p className="section-help">Click Yes for things you’d like to share with a friend.</p>

          {interestQuestions.map((q, idx) => (
            <div className="q-row" key={q.id}>
              <p className="q-text">
                {9 + idx}. {q.label}
              </p>

              <div className="pills">
                <label className="pill pill--yes">
                  <input type="radio" name={q.id} value="yes" required />
            
                  <span className="pill-label">Yes</span>
                </label>

                <label className="pill pill--no">
                  <input type="radio" name={q.id} value="no" />
             
                  <span className="pill-label">No</span>
                </label>
              </div>
            </div>
          ))}
        </section>

        {/* ---------------- Submit ---------------- */}
        <div className="submit-bar">
          <div className="submit-left">
            <p className="submit-note">✨ We’ll email your match. No DMs inside the app (for now).</p>

            <label className="terms-consent">
              <input
                type="checkbox"
                required
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <span>
                I agree to the{" "}
                <a
                  className="terms-link"
                  href="/terms"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Terms of Service
                </a>{" "}
                (opens in a new tab)
              </span>
            </label>
          </div>

          <button className="submit-btn" type="submit" disabled={!acceptedTerms}>
            Submit survey
          </button>
        </div>

      </form>
    </div>
  </main>
);


};

export default SurveyPage;
