# AI Candidate Ranking System

**India Runs Hackathon — Redrob AI Challenge**
Built by **Arivumathi S**, SNS College of Technology, Coimbatore

---

## What This Is

Most candidate-ranking systems reward keyword density. A profile stuffed with "AI Engineer | ML | LLM | Transformer | RAG | FAISS" ranks higher than a genuine senior engineer who built production retrieval systems but wrote their resume like a human.

This system fixes that. It ranks 100,000 candidates the way a great recruiter actually thinks — by understanding career trajectory, real production experience, behavioral availability, and genuine skill fit — then actively penalizes keyword-stuffed and off-target profiles before they can reach the top of the list.

**100,000 candidates ranked in 296 seconds on CPU. Zero external API calls. Zero GPU.**

---

## Results

| Metric | Value |
|---|---|
| Dataset size | 100,000 candidates |
| Ranking runtime | 296 seconds (CPU only) |
| Top candidate score | 0.7491 |
| Submission rows | 100 |
| Validator result | ✅ Submission is valid |
| Test coverage | 82% (24/24 tests passing) |

---

## How It Works

### Five-Signal Hybrid Scoring

Every candidate is scored across five independent dimensions, then combined into one final score:

```
Final Score = (
    0.30 × Semantic Score
  + 0.25 × Experience Score
  + 0.25 × Skill Score
  + 0.20 × Behavioral Score
) × Disqualifier Multiplier
```

**1. Semantic Score (30%)**
Uses `all-MiniLM-L6-v2` sentence-transformers to compute cosine similarity between the job description and a candidate's full profile text (headline + summary + career descriptions + skills). This catches conceptual relevance that keyword matching misses — "built retrieval systems" maps correctly to a vector search role even without the exact phrase "vector database."

**2. Experience Score (25%)**
Scores three things independently:
- Years of experience (ideal band: 5–9 years → 1.0, outside that scales down)
- Company type (product companies → 1.0, mixed → 0.7, consulting-only → 0.1)
- Production ML evidence (scans career descriptions for: `deployed`, `production`, `shipped`, `A/B test`, `inference`, `latency`, `serving`, `pipeline`)

**3. Skill Score (25%)**
Hard required skills (FAISS, Pinecone, Weaviate, Milvus, sentence-transformers, NDCG, MRR, retrieval, ranking) each contribute 0.12 toward a score capped at 1.0. Nice-to-have skills (LoRA, fine-tuning, RAG, LLM, HuggingFace) contribute 0.04 each, capped at 0.3. Off-domain skill dominance (Figma, Selenium, OpenCV only) triggers a penalty.

**4. Behavioral Score (20%)**
Processes all 23 Redrob platform signals:
- **Recency**: days since last active (0–30 days → 1.0, 180+ days → 0.0)
- **Availability**: `open_to_work_flag` + notice period length
- **Engagement**: recruiter response rate + interview completion rate + GitHub activity
- **Reliability**: verified email/phone, LinkedIn connected, profile completeness

**5. Disqualifier Multiplier**
Applied after the weighted sum. The key differentiator — most systems ignore this entirely.

| Pattern | Multiplier |
|---|---|
| Honeypot (impossible YoE, duration > 480 months, 15+ unrelated advanced skills) | 0.0× |
| Wrong title (HR, Sales, Marketing, Designer, Accountant, Recruiter, etc.) | 0.08× |
| Off-domain specialist (OpenCV/Figma/Angular only, no NLP/retrieval skills) | 0.35× |
| Consulting-only career (TCS, Infosys, Wipro, Accenture, etc. — every role) | 0.5× |
| Research-only (papers/academic, no production deployment) | 0.4× |
| India-only candidate not willing to relocate to Pune/Noida | ×0.7 on top |
| Clean profile | 1.0× |

### Reasoning Generator

Every ranked candidate gets a one-line, fact-based reasoning string — built only from real fields in their profile. The generator scores every sentence in a candidate's career history against JD keywords and picks the highest-scoring real sentence. If no relevant sentence exists, it explicitly says so instead of fabricating one.

```
"ML Engineer (6yrs) at product company; built vector search pipeline 
serving 50M+ queries/month; open to work, 30-day notice."
```

---

## Project Structure

```
redrob-ranker/
├── src/
│   ├── config.py                    # All weights, skill lists, company lists, constants
│   ├── parsers/
│   │   └── candidate_parser.py      # JSON/JSONL ingestion + schema validation
│   ├── scoring/
│   │   ├── semantic_scorer.py       # sentence-transformers, cosine similarity
│   │   ├── experience_scorer.py     # YoE + company type + production ML
│   │   ├── skill_scorer.py          # Hard/nice/penalty skill scoring
│   │   ├── behavioral_scorer.py     # 23 Redrob platform signals
│   │   └── disqualifier.py          # Multiplier logic + honeypot detection
│   ├── ranker/
│   │   ├── hybrid_ranker.py         # Weighted combination + deterministic sort
│   │   └── reasoning_generator.py   # Fact-based candidate reasoning
│   └── utils/
│       ├── logger.py                # Python logging, zero print() statements
│       └── validators.py            # Input validation
├── tests/
│   ├── conftest.py                  # pytest fixtures
│   ├── test_parsers.py
│   ├── test_scorers.py
│   ├── test_disqualifier.py
│   ├── test_ranker.py
│   └── test_integration.py          # Full pipeline: input → valid CSV
├── rank.py                          # CLI: python rank.py --candidates file --out out.csv
├── app.py                           # Flask API
├── frontend/                        # React + Tailwind UI
├── requirements.txt
├── submission_metadata.yaml
├── SECURITY.md
└── README.md
```

---

## Setup

**Prerequisites:** Python 3.10+, Node.js 18+

```bash
# Clone the repo
git clone https://github.com/4RIVX/redrob-ranker.git
cd redrob-ranker/artifacts/flask-ranker

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

The sentence-transformers model (`all-MiniLM-L6-v2`, ~80MB) downloads automatically on first run and caches locally. No internet connection needed after that.

---

## Usage

### Run the full ranking pipeline

```bash
python rank.py --candidates /path/to/candidates.jsonl --out submission.csv --top-n 100
```

### Validate your submission

```bash
python validate_submission.py submission.csv
# Expected output: Submission is valid.
```

### Run the web sandbox

```bash
# Terminal 1 — Flask backend
python app.py

# Terminal 2 — React frontend
cd frontend && npm run dev
```

Open `http://localhost:5173`, upload a JSON/JSONL candidate file (up to 500 for demo), click **Rank Candidates**, download the CSV.

### Run tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
# 24/24 passing, 82% coverage
```

---

## Environment Variables

Copy `.env.example` to `.env` before running:

```bash
cp .env.example .env
```

```env
FLASK_PORT=5000
FLASK_ENV=development
```

No API keys required. No external services called during ranking.

---

## Technical Decisions

| Choice | Why |
|---|---|
| `all-MiniLM-L6-v2` | 80MB, CPU-only, strong semantic quality for the domain, no GPU needed |
| Rule-based scorers for experience/skill/behavioral | Explainable, deterministic, debuggable — judges and recruiters can verify every score |
| Disqualifier as multiplier not filter | Suppresses bad profiles without removing them — maintains full ranked list while keeping genuinely wrong profiles at the bottom |
| Deterministic tie-break by `candidate_id` | Reproducible results across every run with identical inputs |
| Flask + React separation | Clean API contract between scoring engine and UI; engine is independently runnable via CLI |
| pytest with fixtures | Scoring modules are pure functions — easy to unit test in isolation |

---

## Security

- No PII is logged at any level
- No external API calls are made during ranking — fully offline
- Candidate data never leaves the local environment
- `.env` excluded from version control via `.gitignore`
- File upload endpoint validates file type before processing

See [SECURITY.md](SECURITY.md) for full details.

---

## Submission

| Deliverable | Location |
|---|---|
| GitHub repository | This repo |
| Ranked output CSV | `submission.csv` (root of repo) |
| Approach deck (PDF) | `submission_deck.pdf` |
| Submission metadata | `submission_metadata.yaml` |

---

## Built With

- Python 3.11
- [sentence-transformers](https://www.sbert.net/) — semantic embeddings
- scikit-learn / NumPy / Pandas — vectorized scoring
- Flask — REST API
- React + Tailwind CSS — recruiter-facing interface
- pytest — test suite

---

## Author

**Arivumathi S**
 B.E. — Electronics and Communication Engineering
SNS College of Technology, Coimbatore

---

*India Runs Hackathon — Redrob AI Challenge | 2026*
