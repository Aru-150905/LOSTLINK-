# Running LostLink 100% locally (your laptop = the server)

This runs the whole app on your machine with **no cloud**: a local Supabase stack
(Postgres + pgvector + Auth + Storage) via the Supabase CLI, the FastAPI backend,
and the Next.js frontend. The AI models (CLIP + MiniLM) download once from
Hugging Face on first use (~500 MB), then run locally.

## 0. Install prerequisites (once)

| Tool | Why | Install |
|------|-----|---------|
| **Docker Desktop** (running) | runs local Supabase | https://www.docker.com/products/docker-desktop/ |
| **Supabase CLI** | local Postgres+Auth+Storage | https://supabase.com/docs/guides/local-development/cli/getting-started |
| **Python 3.11 or 3.12** | backend + AI | https://www.python.org/downloads/ |
| **Node.js 20+** | frontend | https://nodejs.org/ |

> First launch needs internet (to pull Docker images and the AI models). After
> that it runs offline. Use `http://localhost:3000` (not `127.0.0.1`) so auth
> cookies and CORS line up.

## 1. Start local Supabase + write env files (automated)

**macOS / Linux / WSL:**
```bash
bash scripts/setup_local.sh
```
**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_local.ps1
```

This brings up local Supabase, applies all three migrations, disables email
confirmation (so sign-up logs you straight in), and writes `backend/.env` and
`frontend/.env.local` with the correct local keys.

<details>
<summary>Prefer to do step 1 by hand?</summary>

```bash
supabase init            # if supabase/config.toml doesn't exist yet
supabase start           # first run pulls images; prints local keys
supabase db reset        # applies migrations 001, 002, 003
supabase status          # copy API URL / anon key / service_role key / JWT secret
```
Then copy `backend/.env.example` → `backend/.env` and
`frontend/.env.local.example` → `frontend/.env.local`, and paste the values from
`supabase status`. In `supabase/config.toml` set `enable_confirmations = false`
under `[auth.email]` if it isn't already.
</details>

## 2. Backend (Terminal 1)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd ..                           # run from project root so the ai/ package resolves
uvicorn backend.app.main:app --reload --port 8000
```
Check: open http://localhost:8000/health → `{"status":"ok",...}`.

> **CPU-only torch (optional, avoids a large GPU download on Linux):**
> `pip install torch --index-url https://download.pytorch.org/whl/cpu` before
> `pip install -r requirements.txt`.

> **Preload models at boot** (no lag on the first upload): set `WARMUP_MODELS=true`
> in `backend/.env`. Otherwise the first upload takes ~30–60 s while models load.

## 3. Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:3000**.

## 4. Try the main flow

1. Sign up (User A) → report a **Found** item with a photo (e.g. black AirPods).
2. Sign out, sign up as User B → report a **Lost** item with a similar photo.
3. You land on the match results page and should see User A's item ranked by
   confidence. Check the **Notifications** page too.
4. View your data anytime in Supabase Studio (URL printed by `supabase status`,
   usually http://127.0.0.1:54323).

## Make yourself an admin (for the /admin dashboard)

In Supabase Studio → SQL editor:
```sql
UPDATE public.users SET is_admin = true WHERE email = 'you@college.edu';
```

## Stopping / restarting

```bash
supabase stop     # stop the local DB stack (data persists)
supabase start    # bring it back up
```
Backend and frontend restart with the same commands in steps 2 and 3.

## Note on docker-compose.yml

The included `docker-compose.yml` only containerizes the backend and frontend and
still expects a Supabase to point at. For a fully local run, use the steps above
(local Supabase on the host) rather than compose — a container's `127.0.0.1`
wouldn't reach the host's Supabase without extra networking. Compose isn't needed.

## Troubleshooting

- **`No module named 'app'` / `'ai'`** — run uvicorn from the **project root** as
  `uvicorn backend.app.main:app` (not from inside `backend/`).
- **401 on API calls** — `SUPABASE_JWT_SECRET` in `backend/.env` must equal the
  `JWT secret` from `supabase status`. Re-run the setup script if unsure.
- **Sign-up doesn't log you in** — email confirmation is on; set
  `enable_confirmations = false` in `supabase/config.toml`, then `supabase stop && supabase start`.
- **Images don't render** — make sure you're on `http://localhost:3000` and
  Supabase is running; images are served from `http://127.0.0.1:54321/storage/...`.
- **First upload is slow / times out** — that's the one-time model download.
  Set `WARMUP_MODELS=true` and restart the backend, or just retry after it loads.
- **CORS error** — visit the site at `http://localhost:3000` and keep
  `CORS_ORIGINS=http://localhost:3000` in `backend/.env`.
