#!/usr/bin/env bash
# One-shot local setup for LostLink: brings up local Supabase (Postgres+pgvector+
# Auth+Storage), applies migrations, and writes the backend/frontend env files.
#
# Prereqisites (install once):
#   - Docker Desktop (running)
#   - Supabase CLI  ->  https://supabase.com/docs/guides/local-development/cli/getting-started
#   - Python 3.11+  and  Node.js 20+
#
# Usage:  bash scripts/setup_local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "==> Project root: $ROOT"

# --- prerequisite checks -----------------------------------------------------
command -v supabase >/dev/null 2>&1 || { echo "ERROR: 'supabase' CLI not found. Install it first."; exit 1; }
command -v docker   >/dev/null 2>&1 || { echo "ERROR: 'docker' not found. Install Docker Desktop and start it."; exit 1; }
docker info >/dev/null 2>&1 || { echo "ERROR: Docker is installed but not running. Start Docker Desktop and retry."; exit 1; }

# --- init supabase project (idempotent) --------------------------------------
if [ ! -f "supabase/config.toml" ]; then
  echo "==> Initializing Supabase project..."
  supabase init || true
fi

# --- disable email confirmations so signup logs you straight in --------------
if [ -f "supabase/config.toml" ]; then
  python3 - "$ROOT/supabase/config.toml" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# Set enable_confirmations = false anywhere it appears; if absent, leave as-is
# (local default is already false on recent CLIs).
s2 = re.sub(r"enable_confirmations\s*=\s*true", "enable_confirmations = false", s)
if s2 != s:
    open(p, "w", encoding="utf-8").write(s2)
    print("   config.toml: email confirmations disabled")
PY
fi

# --- start the local stack ---------------------------------------------------
echo "==> Starting local Supabase (first run pulls Docker images, be patient)..."
supabase start

# --- apply all migrations from scratch (deterministic) -----------------------
echo "==> Applying migrations..."
supabase db reset

# --- capture local credentials and write env files ---------------------------
echo "==> Writing env files..."
eval "$(supabase status -o env)"

: "${API_URL:?could not read API_URL from supabase status}"
: "${ANON_KEY:?could not read ANON_KEY from supabase status}"
: "${SERVICE_ROLE_KEY:?could not read SERVICE_ROLE_KEY from supabase status}"
: "${JWT_SECRET:?could not read JWT_SECRET from supabase status}"

cat > backend/.env <<EOF
SUPABASE_URL=${API_URL}
SUPABASE_SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}
SUPABASE_JWT_SECRET=${JWT_SECRET}
CORS_ORIGINS=http://localhost:3000
RESEND_API_KEY=
EMAIL_FROM=LostLink <noreply@lostlink.app>
WARMUP_MODELS=false
DEBUG=true
EOF

cat > frontend/.env.local <<EOF
NEXT_PUBLIC_SUPABASE_URL=${API_URL}
NEXT_PUBLIC_SUPABASE_ANON_KEY=${ANON_KEY}
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

echo ""
echo "============================================================"
echo " Local Supabase is up. Env files written:"
echo "   backend/.env"
echo "   frontend/.env.local"
echo ""
echo " Next, in two separate terminals:"
echo ""
echo "   # Terminal 1 - backend"
echo "   cd backend && python -m venv venv && source venv/bin/activate \\"
echo "     && pip install -r requirements.txt && cd .. \\"
echo "     && uvicorn backend.app.main:app --reload --port 8000"
echo ""
echo "   # Terminal 2 - frontend"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo " Then open http://localhost:3000"
echo " Supabase Studio (view your DB): ${STUDIO_URL:-http://127.0.0.1:54323}"
echo "============================================================"
