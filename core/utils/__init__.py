"""
SunFlow Core Utilities
"""

# Trace Manager (P0)
from .trace_manager import (
    TraceManager,
    traced,
    get_trace_id,
    log_trace_event,
)

# Health Check (P1)
from .health_check import (
    HealthChecker,
    HealthStatus,
    get_health_status,
)

# Backup Manager (P1)
from .backup_manager import (
    BackupManager,
    BackupInfo,
)

# Token Monitor (P1)
from .token_monitor import (
    TokenMonitor,
    TokenStatus,
)

# Content Queue
try:
    from .content_queue import ContentQueue
except ImportError:
    ContentQueue = None

# Retry Manager
try:
    from .retry_manager import RetryManager
except ImportError:
    RetryManager = None

# A/B Test Manager
try:
    from .ab_test_manager import ABTestManager
except ImportError:
    ABTestManager = None

# Comment Responder
try:
    from .comment_responder import CommentResponder
except ImportError:
    CommentResponder = None

# Rollback Manager (P2)
from .rollback_manager import (
    RollbackManager,
    RollbackType,
    create_checkpoint,
    quick_rollback,
)

# Circuit Breaker (P2)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    circuit_protected,
    get_all_circuit_status,
)

# Error Aggregator (P2)
from .error_aggregator import (
    ErrorAggregator,
    ErrorSeverity,
    ErrorCategory,
    log_error,
    get_error_summary,
)


__all__ = [
    # Trace
    "TraceManager",
    "traced",
    "get_trace_id",
    "log_trace_event",
    # Health
    "HealthChecker",
    "HealthStatus",
    "get_health_status",
    # Backup
    "BackupManager",
    "BackupInfo",
    # Token
    "TokenMonitor",
    "TokenStatus",
    # Rollback
    "RollbackManager",
    "RollbackType",
    "create_checkpoint",
    "quick_rollback",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "circuit_protected",
    "get_all_circuit_status",
    # Error Aggregator
    "ErrorAggregator",
    "ErrorSeverity",
    "ErrorCategory",
    "log_error",
    "get_error_summary",
    # Optional
    "ContentQueue",
    "RetryManager",
    "ABTestManager",
    "CommentResponder",
]
