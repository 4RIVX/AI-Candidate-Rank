"""Global constants for the Redrob AI Ranker.

All magic strings, numbers, and lists live here.
No other module should define these constants.
"""

# ── Scorer weights ────────────────────────────────────────────────────────────
WEIGHT_SEMANTIC: float = 0.30
WEIGHT_EXPERIENCE: float = 0.25
WEIGHT_SKILL: float = 0.25
WEIGHT_BEHAVIORAL: float = 0.20

# ── Semantic scorer ────────────────────────────────────────────────────────────
SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"

JOB_DESCRIPTION: str = """
Senior AI Engineer role requiring deep expertise in embeddings, vector databases,
retrieval systems, and production ML deployment. The ideal candidate has 5-9 years of
experience, has deployed production ML systems including semantic search, ranking
pipelines (NDCG/MRR), and inference services with low latency. Strong Python skills
and hands-on experience with FAISS, Pinecone, Weaviate, Qdrant, or similar vector stores.
Experience with sentence-transformers, fine-tuning LLMs (LoRA, QLoRA, PEFT), and
learning-to-rank frameworks is highly valued. Must have worked at product companies
building systems used by real users.
"""

# ── Experience scorer ─────────────────────────────────────────────────────────
YOE_IDEAL_MIN: int = 5
YOE_IDEAL_MAX: int = 9
YOE_MID_MIN: int = 3
YOE_MID_MAX: int = 12

YOE_IDEAL_SCORE: float = 1.0
YOE_MID_SCORE: float = 0.7
YOE_LOW_SCORE: float = 0.3

COMPANY_ALL_CONSULTING_SCORE: float = 0.2
COMPANY_SOME_PRODUCT_SCORE: float = 0.7
COMPANY_PRIMARILY_PRODUCT_SCORE: float = 1.0

PRODUCTION_ML_KEYWORDS: list[str] = [
    "deployed",
    "production",
    "shipped",
    "a/b test",
    "inference",
    "latency",
    "pipeline",
    "serving",
]

EXPERIENCE_WEIGHT_YOE: float = 0.40
EXPERIENCE_WEIGHT_COMPANY: float = 0.35
EXPERIENCE_WEIGHT_PRODUCTION: float = 0.25

# ── Consulting firms list ─────────────────────────────────────────────────────
CONSULTING_FIRMS: list[str] = [
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
]

# ── Skill scorer ──────────────────────────────────────────────────────────────
HARD_REQUIRED_SKILLS: list[str] = [
    "embeddings",
    "vector database",
    "sentence-transformers",
    "faiss",
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "opensearch",
    "elasticsearch",
    "retrieval",
    "ranking",
    "ndcg",
    "mrr",
    "evaluation framework",
    "python",
]

NICE_TO_HAVE_SKILLS: list[str] = [
    "lora",
    "qlora",
    "peft",
    "fine-tuning",
    "llm",
    "xgboost",
    "learning-to-rank",
    "nlp",
    "open source",
    "distributed systems",
]

PENALTY_ONLY_DOMAINS: list[str] = [
    "computer vision",
    "speech recognition",
    "robotics",
    "tts",
    "image classification",
]

HARD_SKILL_VALUE: float = 0.15
NICE_SKILL_VALUE: float = 0.05
HARD_SKILL_CAP: float = 1.0
NICE_SKILL_CAP: float = 0.3
DOMAIN_PENALTY: float = 0.3

# ── Behavioral scorer ─────────────────────────────────────────────────────────
RECENCY_TIER_1_DAYS: int = 30
RECENCY_TIER_2_DAYS: int = 60
RECENCY_TIER_3_DAYS: int = 90
RECENCY_TIER_4_DAYS: int = 180

RECENCY_TIER_1_SCORE: float = 1.0
RECENCY_TIER_2_SCORE: float = 0.8
RECENCY_TIER_3_SCORE: float = 0.6
RECENCY_TIER_4_SCORE: float = 0.3
RECENCY_TIER_5_SCORE: float = 0.0

OPEN_TO_WORK_TRUE_SCORE: float = 1.0
OPEN_TO_WORK_FALSE_SCORE: float = 0.3
AVAILABILITY_OPEN_TO_WORK_WEIGHT: float = 0.5
AVAILABILITY_NOTICE_PERIOD_WEIGHT: float = 0.5
NOTICE_PERIOD_MAX_DAYS: int = 180

ENGAGEMENT_RESPONSE_RATE_WEIGHT: float = 0.4
ENGAGEMENT_INTERVIEW_RATE_WEIGHT: float = 0.3
ENGAGEMENT_GITHUB_WEIGHT: float = 0.3
GITHUB_ACTIVITY_MAX: int = 100
GITHUB_ACTIVITY_MISSING: int = -1

RELIABILITY_EMAIL_SCORE: float = 0.1
RELIABILITY_PHONE_SCORE: float = 0.1
RELIABILITY_LINKEDIN_SCORE: float = 0.1
RELIABILITY_COMPLETENESS_WEIGHT: float = 0.7

BEHAVIORAL_RECENCY_WEIGHT: float = 0.30
BEHAVIORAL_AVAILABILITY_WEIGHT: float = 0.25
BEHAVIORAL_ENGAGEMENT_WEIGHT: float = 0.25
BEHAVIORAL_RELIABILITY_WEIGHT: float = 0.20

# ── Disqualifier ──────────────────────────────────────────────────────────────
NON_AI_JOB_TITLES: list[str] = [
    "marketing manager",
    "hr manager",
    "content writer",
    "graphic designer",
    "accountant",
    "sales executive",
    "civil engineer",
    "mechanical engineer",
]

KEYWORD_STUFFER_AI_SKILL_THRESHOLD: int = 5
KEYWORD_STUFFER_MULTIPLIER: float = 0.05

CONSULTING_ONLY_MULTIPLIER: float = 0.5

RESEARCH_KEYWORDS: list[str] = ["phd", "research lab", "paper", "published", "academic"]
PRODUCTION_KEYWORDS: list[str] = ["deployed", "production", "users", "shipped"]
RESEARCH_ONLY_MULTIPLIER: float = 0.4

HONEYPOT_MAX_YOE: int = 40
HONEYPOT_MAX_UNRELATED_EXPERT_SKILLS: int = 12
HONEYPOT_MAX_ROLE_MONTHS: int = 600
HONEYPOT_MULTIPLIER: float = 0.0

LOCATION_PENALTY_MULTIPLIER: float = 0.7
INDIA_COUNTRY_VALUES: list[str] = ["india", "in"]

CLEAN_MULTIPLIER: float = 1.0
