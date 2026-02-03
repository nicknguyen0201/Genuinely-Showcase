import "./TermsOfUsePage.css";

export default function TermsOfUsePage() {
  return (
    <div className="terms-page">
      <div className="terms-shell">
        <header className="terms-hero">
          <h1 className="terms-title">Terms of Service</h1>
          <p className="terms-subtitle">
            Last updated: <strong>January 31, 2026</strong>
          </p>
        </header>

        <main className="terms-card">
          <section className="terms-section">
            <h2 className="section-title">Overview</h2>
            <p className="section-help">
              These Terms of Service (“Terms”) govern your access to and use of Genuinely (“we,” “us,” or “our”).
              By accessing or using Genuinely, you agree to be bound by these Terms.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">1. What Genuinely Is</h2>
            <p className="section-help">
              Genuinely is a student-led, non-profit project designed to help email-verified UC San Diego students connect
              with other students for friendship and social connection.
            </p>

            <h2 className="subsection-title"> 1.1 Relationship to UC San Diego</h2>
            <p className="section-help">
              Genuinely is an independent, student-led project. It is not managed, endorsed, or sponsored by the
              University of California, San Diego (UCSD) or the Regents of the University of California. Use of the
              platform does not constitute a university-sanctioned activity.
            </p>

            <ul className="terms-list">
              <li>Genuinely facilitates introductions between users.</li>
              <li>Genuinely does not guarantee outcomes or compatibility.</li>
              <li>Genuinely does not supervise, monitor, or control interactions between users.</li>
            </ul>
          </section>

          <section className="terms-section">
            <h2 className="section-title">2. Eligibility</h2>
            <p className="section-help">
              To use Genuinely, you must be a UC San Diego student, verify your account using a valid{" "}
              <code className="terms-code">@ucsd.edu</code> email address, and be at least 18 years old. You are
              responsible for ensuring information you provide is accurate.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">3. User Interactions &amp; Safety</h2>
            <p className="section-help">
              Genuinely facilitates introductions only. All interactions—online or in person—occur at your own
              discretion and risk. We do not conduct background checks and are not responsible for the conduct of any
              user.
            </p>

            <h3 className="subsection-title">3.1 Reporting Misconduct</h3>
            <p className="section-help">
              While Genuinely has no obligation to monitor or mediate disputes between users, we reserve the right to
              investigate reported violations of our Acceptable Use policy and take appropriate action, including
              permanent account bans.
            </p>

            <div className="terms-callout">
              <div className="terms-callout-title">Safety reminder</div>
              <p className="terms-callout-text">
                Meet in public places, trust your instincts, and prioritize personal safety when connecting with other
                users.
              </p>
            </div>
          </section>

          <section className="terms-section">
            <h2 className="section-title">4. Assumption of Risk</h2>
            <p className="section-help">
              By using Genuinely, you voluntarily assume all risks associated with interacting with other users,
              including risks of personal injury, emotional distress, or other harm.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">5. Acceptable Use</h2>
            <p className="section-help">You agree not to:</p>
            <ul className="terms-list">
              <li>Harass, threaten, or harm other users.</li>
              <li>Misrepresent your identity or intentions.</li>
              <li>Use the platform for commercial solicitation, spam, or scams.</li>
              <li>Attempt to scrape, collect, or misuse user data.</li>
            </ul>
            <p className="section-help">We may suspend or remove access for users who violate these Terms.</p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">6. Data Use &amp; Privacy</h2>
            <p className="section-help">
              Genuinely may use anonymized and aggregated data to evaluate and improve matching algorithms, including
              statistical or machine-learning–based approaches. Personal identifiers are removed before analysis.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">7. No Guarantees</h2>
            <p className="section-help">
              Genuinely makes no guarantees regarding compatibility, friendship outcomes, or the frequency/quality of
              matches. Use of the platform does not guarantee any particular result.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">8. Beta Service; As-Is</h2>
            <p className="section-help">
              Genuinely is provided on an “as-is” and “as-available” basis. The service may be modified, interrupted,
              or discontinued at any time without notice.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">9. Limitation of Liability</h2>
            <p className="section-help">
              To the maximum extent permitted by law, Genuinely is not liable for indirect, incidental, or
              consequential damages arising from use of the platform or interactions between users. If liability is
              found, Genuinely’s total liability shall not exceed the amount you paid to use the service (currently{" "}
              <strong>$0</strong>).
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">10. Changes to These Terms</h2>
            <p className="section-help">
              We may update these Terms from time to time. If changes are material, users may be asked to review and
              agree again before continuing to use Genuinely.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">11. Termination</h2>
            <p className="section-help">
              You may stop using Genuinely at any time. We may suspend or terminate access if these Terms are violated
              or continued use poses risk to other users or the platform.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">12. Governing Law</h2>
            <p className="section-help">
              These Terms shall be governed by the laws of the State of California. Any disputes arising from these
              Terms or the use of Genuinely shall be resolved in the courts located in San Diego County, California.
            </p>
          </section>

          <section className="terms-section">
            <h2 className="section-title">13. Contact</h2>
            <p className="section-help">
              Questions or concerns? Contact us via the information provided on the platform.
            </p>
          </section>

          <footer className="terms-footer">
            <p className="terms-footer-text">
              Final note: Genuinely exists to help students form respectful connections. By using the platform, you
              agree to engage thoughtfully and responsibly.
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
