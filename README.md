# Genuinely 🫶

_A student-led friendship matching platform for UC San Diego students_

Genuinely is a non-profit, student-built web platform that helps verified UC San Diego students connect with new friends based on shared interests, preferences, and personality “vibes”.

This project was created to address a common experience at large universities:

> _It can be surprisingly hard to form meaningful friendships, even when you’re trying._

Genuinely focuses on **friendship only** — not dating, not social media, not clubs — just genuine 1-on-1 connections.

---

## ✨ Features

- 🔐 **UCSD-only access** via `@ucsd.edu` email verification
- 🧠 **Survey-based matching** using a fixed-dimension feature vector (33 dims)
- 🤖 **Algorithmic matching** based on similarity scoring (statistical / ML-ready)
- 📧 **Email-based introductions** (no in-app DMs)
- 🧩 **User preferences** (same year / same gender optional)
- 🪟 **Privacy-first design** (no public profiles, no shame in participation )
- 📜 **Explicit Terms of Service consent** before participation

---

## 🧭 How it works

1. User logs in with a UCSD email (OTP)
2. User completes a short survey about:
   - basic info (name, year, gender)
   - personality vibes
   - interests
   - matching preferences
3. Survey responses are converted into a **fixed-order feature vector**
4. Users are matched with other compatible students every 4 days
5. Both users receive an **email introduction** and can choose to reach out

All interactions happen **outside the platform** and are fully optional.

---

## 🛠 Tech Stack

### Frontend

- **React + TypeScript**
- **Vite**
- **React Router**
- Custom CSS

### Backend / Infrastructure

- **Supabase**
  - Auth (OTP)
  - Postgres
  - Row-level security
- **Serverless functions** (for email + terms acceptance)
- **Resend** (transactional emails)

### Data / Matching

- Survey → **33-dimensional vector**
- Regularly send users email asking for their match feedback (eg. Is Jonathan a good match? Yes/No)
- Similarity-based matching (extensible to ML approaches)
- Aggregated, anonymized analysis for improving matching logic

---

## 🔐 Privacy & Safety

- Only verified UCSD students can use the platform
- Profiles are **not public**
- Genuinely facilitates introductions only
- All interactions are at users’ own discretion
- Survey and feedback data may be analyzed **only in anonymized and aggregated form**
- Personal identifiers are removed before analysis

For full details, see the **Terms of Service**.

---

## 📜 Terms of Service

Users must explicitly agree to the Terms of Service before submitting the survey.

The Terms clarify:

- Genuinely’s role as a facilitator only
- User responsibility for interactions
- Data usage and anonymization
- Safety expectations
- No affiliation with UC San Diego, it is a project of a student

Terms are available at:  
`/terms`

---

## 🚧 Project Status

- 🟢 Active development
- 👥 60+ early users, 100+ matches sent, collaborating with restaurants on campus to give users a discount for in-person meet up
- 🧪 Iterating on matching logic and UX
- 📈 Exploring better onboarding and feedback loops

This is an **early-stage, student-led project**, not a commercial product.

---

## [Video Demo](https://youtu.be/3h24wamH_04)

© 2026 Genuinely. All rights reserved.
