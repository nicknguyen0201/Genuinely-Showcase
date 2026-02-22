# Genuinely — Friend Matching Platform

> A deployed, full-stack friend-matching platform for UCSD students — built and operated solo.

**Live at:** [genuinely.life](https://www.genuinely.life)

## [Video Demo](https://youtu.be/3h24wamH_04)

---

## 🚧 Project Status

- 🟢 **Active** — currently live and running
- 👥 **100+ users** onboarded in the first month
- 💌 **150+ matches** sent via automated email pipeline
- 🤝 **Partnered with 2 on-campus restaurants** to offer users 10–20% discounts for in-person meetups
- 🔁 Iterating on matching logic, UX, and feedback loops

> **Note:** Matching runs on a private repo to protect user data (PR history contains PII). This showcase repo mirrors the core matching logic and automation pipeline.

---

## 🧠 What This Repo Shows

This repo contains the **matching engine and automation pipeline** — the most technically interesting part of the system.

### The stack

- **Frontend:** Next.js + Supabase Auth (private repo)
- **Database:** Supabase (Postgres + RLS)
- **Emails:** Resend API
- **Matching:** Irving's Stable Roommates algorithm (Python)
- **Automation:** GitHub Actions (scheduled, 4-day cycle)

---

## 📐 Matching Algorithm

### Problem

Given n users, find a **stable pairing** (no two people would both prefer each other over their current match).

This is the **Stable Roommates Problem** — harder than Stable Marriage because it is not bipartite.

### Approach

1. **Feature vectors** — each user fills out a survey encoded as a 33-dim binary vector:
   - Gender (4 dims, one-hot)
   - Year (6 dims, one-hot)
   - Vibes: introvert/extrovert/spontaneous/etc. (6 dims)
   - Interests: gaming/fitness/music/etc. (16 dims)
  

2. **Weighted MSE distance matrix** — pairwise distance between users i and j:

$$X[i,j] = \sum_k w_k (F[i,k] - F[j,k])^2$$

where `w` is a weight vector (currently hand-tuned, designed to be learned from feedback data).

3. **Ban penalty** — previously matched pairs get `X[i,j] = 300` to avoid repeat matches.

4. **Preference matrix** — each user's preference list is their row of `X` sorted ascending (closer = more preferred).

5. **Irving's algorithm** — finds a stable matching if one exists. Dummy user appended if `n` is odd.

6. **Email delivery** — match emails sent via Resend with decoded profile info (name, year, gender, things in common).

---

## 🔁 Automated 4-Day Cycle (GitHub Actions)

The pipeline runs fully automated on a 4-day repeating schedule:

| Day       | What runs                                                            |
| --------- | -------------------------------------------------------------------- |
| **Day 0** | `main()` — compute matches, send match emails, write to DB           |
| **Day 1** | `send_feedback_for_latest_round()` — ask users if the match was good |
| **Day 2** | skip                                                                 |
| **Day 3** | skip                                                                 |

Triggered daily at **12pm PST / 1pm PDT** via GitHub Actions cron.

Manual override available via `workflow_dispatch` (Actions tab).

---

## 📁 Repo Structure

```
Genuinely/
├── Matching.py              # Full matching pipeline
├── run_matching_cli.py      # CLI entry point for GitHub Actions
├── requirements.txt
└── README.md

.github/
└── workflows/
    └── genuinely-cycle.yml  # Scheduled 4-day automation
```

---

## ⚙️ How to Run Locally

### 1. Install dependencies

```bash
pip install -r Genuinely/requirements.txt
```

### 2. Set environment variables

Create a `.env.local` in the project root:

```env
SUPABASE_URL="https://<project>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="..."
RESEND_API_KEY="..."
RESEND_FROM="Genuinely <matches@send.genuinely.life>"
FEEDBACK_SIGNING_SECRET="..."
```

### 3. Run

```bash
# Run matching + send match emails
python Genuinely/run_matching_cli.py --task main

# Send feedback emails for the previous round
python Genuinely/run_matching_cli.py --task feedback
```

---

## 🔐 Security Notes

- `SUPABASE_SERVICE_ROLE_KEY` bypasses RLS — never exposed client-side
- `.env.local` is gitignored
- Feedback links are HMAC-signed with expiry (7 days)
- Private repo holds user data; this repo contains logic only

---

## 📈 Roadmap

- [ ] Learn weight vector `w` from feedback signal (liked/disliked match) to further improve matching algorithm

---

## 👤 Author

Built and operated solo by **Nick** — UCSD student  
Questions? → [contact@send.genuinely.life](mailto:contact@send.genuinely.life)
