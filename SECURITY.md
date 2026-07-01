# Security Notes — AI Candidate Ranker

## Data handling

- **No PII is logged.** Candidate data submitted to `/api/rank` is processed in memory and discarded after the response. Nothing is written to disk or a database.
- **No external API calls during ranking.** All scoring (semantic, experience, skill, behavioral, disqualifier) runs entirely on-device using locally loaded models. No data leaves the server during a rank request.
- **Fully local / offline CPU processing.** The sentence-transformers model (`all-MiniLM-L6-v2`) is downloaded once from Hugging Face at first use and cached locally. Subsequent ranking runs are fully offline.

## Network exposure

- The Flask API binds to `0.0.0.0` for Replit's internal proxy. In production, place it behind a reverse proxy (nginx, Caddy) that enforces TLS and restricts origin.
- CORS is permissive (`*`) in development. Restrict `CORS_ORIGINS` to your frontend domain before public deployment.

## Secrets

- No API keys or credentials are required for ranking.
- Never commit `.env` files — use `.env.example` as a reference template.

## Reporting vulnerabilities

Open a GitHub issue marked **[SECURITY]** or email the maintainer directly. Please do not disclose security issues in public issues.
