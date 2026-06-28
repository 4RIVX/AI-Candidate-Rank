# Redrob AI Ranker

AI-powered candidate ranking system that scores resumes against a job description using semantic similarity, experience, skills, behavioral signals, and disqualifier detection.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- Flask backend: `cd artifacts/flask-ranker && python3 app.py`
- Required env: `DATABASE_URL` — Postgres connection string (not required for ranking — stateless)

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- **Frontend**: React + Vite (dark violet/indigo theme), TanStack Query
- **Backend**: Python 3.11 + Flask 3, served at `/api`
- **Scoring**: TF-IDF cosine similarity (fallback for semantic), scikit-learn, rank-bm25
- **Semantic scorer**: Auto-loads sentence-transformers/all-MiniLM-L6-v2 if available; falls back to TF-IDF
- Build: esbuild (CJS bundle)

## Where things live

- `artifacts/redrob-frontend/` — React + Vite frontend app
- `artifacts/flask-ranker/` — Python Flask backend
  - `app.py` — Flask entrypoint, serves `/api/healthz`, `/api/rank`, `/api/rank/status`, `/api/rank/download`
  - `src/config.py` — job description & scoring weights
  - `src/scoring/` — 5 scoring modules (semantic, experience, skill, behavioral, disqualifier)
  - `src/ranker/` — hybrid ranker + reasoning generator
  - `src/parsers/` — candidate JSON/JSONL parser
- `lib/api-spec/openapi.yaml` — OpenAPI spec (source of truth for API contract)
- `lib/api-client-react/` — generated TanStack Query hooks and Zod schemas

## Architecture decisions

- **Stateless API**: No database — ranking is computed on-demand, no persistence needed.
- **TF-IDF fallback**: Semantic scorer gracefully degrades to TF-IDF cosine similarity when `sentence-transformers` is unavailable (Nix install restriction).
- **Hybrid scoring**: Weighted combination of semantic (0.35), experience (0.25), skills (0.30), behavioral (0.10) with disqualifier multiplier.
- **Contract-first**: OpenAPI spec in `lib/api-spec` drives codegen for both client hooks and Zod validators.
- **Path-based routing**: Flask at `/api`, React at `/` — shared proxy routes by path prefix.

## Product

- Upload JSON or JSONL files of candidate profiles
- System ranks candidates against a configurable job description
- Each candidate gets: overall score (0-100), per-dimension scores, AI-generated reasoning
- Download ranked results as CSV
- Score distribution chart and summary statistics panel

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- `sentence-transformers` cannot be installed via Nix package manager (PEP 668 + dependency resolver). Semantic scorer auto-falls back to TF-IDF.
- Flask runs via `bash /home/runner/workspace/artifacts/flask-ranker/start.sh` (absolute path required — workflow runs from different cwd).
- Job description and scoring weights are hardcoded in `src/config.py` — change there to reconfigure.
- Model loads lazily on first `/api/rank` request (not at startup).

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
