"""Custom Prometheus metrics tracking module for AI features auditing."""
from prometheus_client import Histogram, Counter, Gauge

# Histogram tracking LLM response latencies in seconds
LMS_LLM_LATENCY = Histogram(
    "lms_llm_latency_seconds",
    "LLM query execution response latency in seconds"
)

# Counter tracking cumulative tokens used during completions
LMS_LLM_TOKENS = Counter(
    "lms_llm_tokens_total",
    "Total volume of tokens consumed by LLM requests",
    ["token_type"]  # "prompt_tokens" or "completion_tokens"
)

# Histogram tracking RAG hybrid document search/retrieval execution times
LMS_RAG_RETRIEVAL_TIME = Histogram(
    "lms_rag_retrieval_seconds",
    "RAG document hybrid retrieval search time in seconds"
)

# Gauge tracking active concurrent student sessions/connections
LMS_ACTIVE_USERS = Gauge(
    "lms_active_users",
    "Active student sessions currently registered on endpoints"
)
