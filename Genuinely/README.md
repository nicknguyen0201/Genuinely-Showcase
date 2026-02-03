# Matching.ipynb — Documentation (Genuinely)

This notebook implements the **batch matching pipeline** for the Genuinely friend‑match project:

- pulls active user profiles from Supabase
- computes pairwise similarity / distance using survey vectors
- produces a **stable roommate** matching using **Irving’s algorithm**
- writes match pairs back to Supabase
- sends match notification emails (via Resend) and marks rows as emailed

> Intended usage: run manually (e.g., every few days / weekly) to generate a new “round” of matches.

---

## 1) Prerequisites

### Python environment

Python 3.10+.


### Environment variables

The notebook expects these variables (typically from a `.env` file loaded via `load_dotenv()`):

- `SUPABASE_URL` — your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — **service role key** (server/admin; never ship to client)
- `RESEND_API_KEY` — Resend API key used to send emails
- `RESEND_FROM` — verified sender, e.g. `Genuinely <team@genuinely.life>`

Example `.env`:

```env
SUPABASE_URL="https://<project>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="..."
RESEND_API_KEY="..."
RESEND_FROM="Genuinely <team@genuinely.life>"
```

---

## 2) Data model assumptions

### `profiles` table

The notebook reads:

- `id` (uuid; should equal `auth.users.id`)
- `name`
- `email`
- `survey_vec` (array / list of numbers)
- `active` (boolean)

Only users with `active = true` are included.

### `matches` table

The notebook inserts pairs for a given `round_id` (ISO date string).
It also updates `emailed_at` after successful sends.

This notebook assumes the matches table supports:

- a normalized pair key (e.g., `user_low`, `user_high`) **or**
- equivalent columns that uniquely identify a pair per round

(See `insert_matches()` / `send_matches_and_mark()` for the exact columns being written.)

### Past-pair “ban list”

To reduce repeats, the notebook queries previous matches and applies a strong penalty to the distance matrix so the algorithm avoids matching the same pair again.

---

## 3) High-level pipeline

The entrypoint is `main()`:

1. **Fetch + validate profiles**  
   `get_rows_supabase()` filters for active users and validates vector length.

2. **Build feature matrix + distance matrix**  
   `get_X_ids_and_namemap()` stacks survey vectors into `F` (n×d) and computes `X` (n×n):
   \[
   X[i,j] = \sum_k w_k (F[i,k] - F[j,k])^2
   \]
   where `w` is the weight vector (called `unlearned_weight` in the notebook).

3. **Make n even (dummy user if needed)**  
   If there is an odd number of users, a dummy profile is appended so Irving’s algorithm can produce complete pairings.

4. **Apply “do not rematch” penalty**  
   `fetch_past_pairs()` gets historical pairs  
   `apply_ban_penalty_inplace()` adds a large constant to `X[i,j]` for banned pairs

5. **Convert distances to preferences**  
   `get_preference_matrix(X)` produces each user’s preference list sorted by **ascending** distance (closest first).

6. **Run Irving’s Stable Roommates algorithm**  
   `Find_all_Irving_partner(pref)` returns a stable pairing if one exists (or reports failure states depending on implementation).

7. **Convert pair indices to user IDs**  
   `all_matchings_to_ids()` maps from matrix indices to Supabase UUIDs.

8. **Write matches + send emails**  
   `insert_matches(pairs, round_id)` inserts match rows  
   `send_matches_and_mark(pairs, ids_to_info, round_id)` sends 2 emails per pair and sets `emailed_at` only after both sends succeed.

---

## 4) Core functions

### 4.1 `get_rows_supabase()`

Pulls active profiles and validates each `survey_vec` length.

Returns:

- list of clean profile rows (dicts)

Notes:

- If vectors are missing or wrong length, rows are skipped with a warning.
- If nothing is valid, it raises an error.

---

### 4.2 `get_X_ids_and_namemap()`

Builds:

- `F`: stacked `survey_vec` matrix (n×d)
- `X`: weighted squared-distance matrix (n×n)
- `ids`: index→user_id list
- `id_to_info`: user_id → (name, email, index)

Key behavior:

- Adds a dummy user if `n` is odd to make the algorithm feasible.
- Uses broadcasting to compute all pairwise distances efficiently.

---

### 4.3 `fetch_past_pairs(supabase)`

Queries the `matches` table (or equivalent) for prior pairings and returns a list/set of banned pairs.

A “pair” is treated as unordered:

- store as `(min(user_a, user_b), max(user_a, user_b))`

---

### 4.4 `apply_ban_penalty_inplace(X, id_to_info, banned_pairs)`

For every banned pair (u,v), finds their indices in `X` and adds a **large** penalty to both `X[i,j]` and `X[j,i]`.

Purpose:

- Keep the preference ranking from choosing repeated pairings unless absolutely necessary.

---

### 4.5 `get_preference_matrix(X)`

Converts distances to a preference matrix:

- for each user i: sort all j by increasing `X[i,j]`
- place i itself at the end (self-match disallowed)

Output:

- `pref_matrix` shape (n×n), each row is a permutation of indices.

---

### 4.6 Irving’s algorithm (Stable Roommates)

Implemented as a collection of helper functions (ported from an MIT-licensed reference implementation):

- `get_ranking(preference)`
- `phaseI_reduction(...)`
- `phaseII_reduction2(...)`
- `seek_cycle2(...)`, `update_second2(...)`
- `Find_all_Irving_partner(preference)`
- plus debug printers

Purpose:

- Find a stable pairing in the **roommates** setting (not bipartite).

Important:

- Stable roommates does not always have a solution; the code returns the found solution(s) or indicates failure states.

---

### 4.7 `insert_matches(pairs, round_id)`

Writes match pairs into Supabase.

Expected behavior:

- normalize each pair `(a,b)` into `(user_low, user_high)`
- set `round_id`
- avoid duplicates (ideally via `onConflict` or a unique constraint)

---

### 4.8 Email sending

Two layers exist:

#### `send_email_resend(to_email, subject, html)`

Sends a single email via Resend HTTP API.

Inputs:

- `to_email`
- `subject`
- `html` string

Raises:

- RuntimeError if Resend returns non-2xx

#### `send_matches_and_mark(res_pairs, ids_to_info, round_id)`

For each pair (a,b):

1. Loads both users’ `profiles` (to fetch `survey_vec`)
2. Decodes vectors into human-readable fields (gender/year/interests)
3. Computes “things in common”
4. Sends 2 emails (A→B details, B→A details)
5. Updates matches row `emailed_at` only if both sends succeed

This function is intentionally **transaction-like** per pair:

- if any send fails: do not mark emailed_at

---

## 5) Decoding survey vectors (human-friendly emails)

The notebook includes helpers that:

- map a numeric `survey_vec` back into:
  - gender
  - year
  - selected vibe attributes
  - selected interests
- compute overlap between two decoded results

Used to generate the email content so users see:

- who they matched with (name/year)
- what they have in common

