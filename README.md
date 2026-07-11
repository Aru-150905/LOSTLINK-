# LostLink — AI-Powered Lost & Found Platform

LostLink is a production-ready full-stack web application for college festivals. Users report lost and found items, and the system automatically matches them using CLIP image embeddings, Sentence Transformer text embeddings, and metadata scoring via Supabase pgvector.

## Architecture

```
├── frontend/     Next.js 16 + React + TailwindCSS + Shadcn UI
├── backend/      FastAPI Python API
├── ai/           CLIP + Sentence Transformers matching engine
└── supabase/     PostgreSQL migrations (pgvector, RLS, storage)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, TailwindCSS, Shadcn UI |
| Backend | FastAPI (Python) |
| Database | Supabase PostgreSQL + pgvector |
| Auth | Supabase Auth |
| Storage | Supabase Storage |
| AI | CLIP (image), Sentence Transformers (text) |

## Matching Engine

**Final Score = 70% image + 20% text + 10% metadata**

- **Image**: CLIP ViT-B/32 embeddings (512-dim), cosine similarity
- **Text**: all-MiniLM-L6-v2 embeddings (384-dim), cosine similarity
- **Metadata**: location proximity, time proximity, category similarity

Returns top 5 matches when a lost item is compared against found items (and vice versa).

## Quick Start

> **Running everything locally on your own machine?** Follow
> **[LOCAL_SETUP.md](LOCAL_SETUP.md)** — it uses a local Supabase stack (no cloud)
> and an automated setup script. The steps below describe the hosted-Supabase path.

### 1. Supabase Setup

1. Create a [Supabase](https://supabase.com) project
2. Enable the **pgvector** extension in Dashboard → Database → Extensions
3. Run migrations in order:
   ```bash
   # Via Supabase SQL Editor or CLI
   supabase/migrations/001_initial_schema.sql
   supabase/migrations/002_vector_search_rpc.sql
   ```
4. Copy your project URL, anon key, service role key, and JWT secret

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with Supabase credentials

# Run from project root so ai/ module resolves
cd ..
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with Supabase + API URL

npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload-item` | Upload lost/found item + auto-match |
| POST | `/api/v1/generate-embedding` | Generate embeddings only |
| POST | `/api/v1/search-matches` | Re-run match search |
| GET | `/api/v1/my-items` | User's uploaded items |
| POST | `/api/v1/claim-item` | Submit claim request |
| GET | `/api/v1/notifications` | User notifications |
| POST | `/api/v1/mark-resolved` | Mark item as returned |
| GET | `/api/v1/admin/stats` | Admin dashboard stats |
| GET | `/api/v1/admin/claims` | Pending claims |
| POST | `/api/v1/admin/claims/review` | Approve/reject claim |

## Environment Variables

### Backend (`backend/.env`)

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
CORS_ORIGINS=http://localhost:3000
RESEND_API_KEY=          # Optional: email notifications
EMAIL_FROM=LostLink <noreply@lostlink.app>
```

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Pages

- `/` — Landing page
- `/auth` — Sign in / Sign up
- `/upload/lost` — Report lost item
- `/upload/found` — Report found item
- `/my-items` — User's uploaded items
- `/matches/[id]` — Match results with confidence scores
- `/notifications` — Match and claim notifications
- `/admin` — Admin dashboard (requires `is_admin = true`)

## Admin Access

Set a user as admin in Supabase:

```sql
UPDATE public.users SET is_admin = true WHERE email = 'admin@college.edu';
```

## Deployment

- **Frontend**: Deploy to Vercel with env vars
- **Backend**: Deploy to Railway, Render, or Fly.io with Python 3.11+
- **Database**: Supabase hosted PostgreSQL
- **AI models**: Downloaded on first request (~500MB); consider pre-warming in production

## License

MIT
