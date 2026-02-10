# AOC 5-Agent Parallel Evaluation System - User Guide

**Version:** 1.0
**Last Updated:** 2026-01-31
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Quick Start](#quick-start)
4. [Running Tests](#running-tests)
5. [Understanding Results](#understanding-results)
6. [Agent Descriptions](#agent-descriptions)
7. [Conflict Resolution](#conflict-resolution)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Overview

The **Asynchronous Orchestration Controller (AOC) 5-Agent Parallel Evaluation System** is an autonomous content approval system that evaluates food content for the Project Sunshine Instagram account using 5 specialized agents running in parallel.

### Key Features

✅ **Fully Autonomous** - Zero questions asked to users
✅ **Parallel Execution** - All 5 agents evaluate simultaneously (~2ms total)
✅ **Conflict Detection** - Automatic detection of agent disagreement
✅ **Consensus-Based** - Final decision requires 75%+ agent agreement
✅ **Safety-First** - Multiple safety checks across all agents
✅ **Cost-Aware** - Budget tracking and optimization
✅ **Production-Ready** - Tested with real food items (Broccoli, Watermelon)

### What Gets Evaluated?

```
Input:  Food Content Item (Korean name, English name, safety level, slides, captions)
                ↓
        ┌─────────────────────────────────────┐
        │  5-Agent Parallel Evaluation        │
        ├─────────────────────────────────────┤
        │  A: Content Check                   │
        │  B: Quality Scores (5 dimensions)   │
        │  C: Automation Judgment             │
        │  D: Red Flag Detection              │
        │  E: Cost Estimation                 │
        └─────────────────────────────────────┘
                ↓
Output: AUTO_PUBLISH, HUMAN_QUEUE, or BLOCKED
        + Confidence Score
        + Detailed Reasoning
```

---

## System Architecture

### The 5 Agents

```
┌──────────────────────────────────────────────────────────────┐
│ AOC (Asynchronous Orchestration Controller)                  │
└──────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┬───────────┬───────────┬────────────┐
                    │                   │           │           │            │
              [Agent A]          [Agent B]     [Agent C]    [Agent D]   [Agent E]
            Content Check     Quality Scores  Automation  Red Flags    Cost Est.
                (A_CC)           (B_QS)       (C_AJ)      (D_RF)       (E_CE)
                │                 │            │           │            │
         ┌──────┴──────┐   ┌──────┴────────┬──┴───────┐ ┌─┴──────┐  ┌──┴────────┐
         │              │   │               │  Policy   │ │Safety  │  │ Budget    │
         │ Format       │   │ Accuracy      │ Compliance│ │Checks  │  │ Compliance│
         │ Metadata     │   │ Tone          │           │ │Brand   │  │ API Calls │
         │ Structure    │   │ Format        │           │ │Flags   │  │ Resource  │
         │ Captions     │   │ Coherence     │           │ │Timing  │  │ Alloc.    │
         │              │   │               │           │ │        │  │           │
         └──────┬───────┘   └───────┬───────┴───────────┘ └────────┘  └───────────┘
                │                   │
                └───────────────────┼─────────────────────────────────┐
                                    │                               │
                        ┌───────────▼──────────────┐      ┌─────────▼────────┐
                        │  Conflict Detection      │      │  Final Decision   │
                        │  (resource, timing,      │──────│  - Auto consensus │
                        │   judgment)              │      │  - Quality check  │
                        └──────────┬───────────────┘      │  - Safety check   │
                                   │                      │  - Cost check     │
                                   └──────────────────────┴──────────────────┘
                                                          │
                                              ┌───────────▼──────────┐
                                              │  Final Verdict       │
                                              │  ✅ AUTO_PUBLISH     │
                                              │  ⏳ HUMAN_QUEUE      │
                                              │  ❌ BLOCKED          │
                                              └──────────────────────┘
```

### Parallel Execution Timeline

```
Time (ms)  Agent A   Agent B     Agent C   Agent D   Agent E
─────────────────────────────────────────────────────────────
0.00       ├────┤   ├──────────┤
0.01       │    │   │  1.45ms  │  ├──┤   ├───┤    ├───┤
0.02       │    │   │          │  │  │   │   │    │   │
0.04       │    │   │          │  │  │   │   │    │   │
1.45       ├────┘   ├──────────┤  ├──┤   ├───┤    ├───┤
1.66       │        │          │  │  │   │   │    │   │
                    └──────────┘  └──┘   └───┘    └───┘

Total Parallel Time: 1.66ms (vs ~10ms if sequential)
Speedup: 6x faster
```

---

## Quick Start

### Installation

```bash
# The AOC system is included in the project
# No additional dependencies needed beyond standard Python 3.8+

cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine

# The test file is at:
# support/tests/test_aoc_5agent_evaluation.py
```

### Running the Test

```bash
# Run the complete evaluation test
python3 support/tests/test_aoc_5agent_evaluation.py

# Expected output:
# ✅ Evaluates both Broccoli and Watermelon
# ✅ Shows detailed agent results
# ✅ Reports any conflicts (should be 0)
# ✅ Provides final verdicts and confidence scores
# ✅ Generates summary table
# ✅ Saves results to JSON
```

### Expected Output

```
====================================================================================================
AOC 5-AGENT PARALLEL EVALUATION SYSTEM TEST
====================================================================================================

====================================================================================================
CONTENT: 브로콜리 (BROCCOLI)
Safety Classification: SAFE
...
[detailed results]

FINAL DECISION:
────────────────────────────────────────────────────────────────
Consensus: auto_publish
Final Verdict: auto_publish
Publishable: YES ✅
Confidence Score: 99.0%
Questions Asked: 0
Total Execution Time: 1.66ms
```

---

## Running Tests

### Option 1: Run Complete Test Suite

```bash
python3 support/tests/test_aoc_5agent_evaluation.py
```

**What it does:**
- Evaluates Broccoli (SAFE food)
- Evaluates Watermelon (SAFE food)
- Runs all 5 agents in parallel for each food
- Detects conflicts (if any)
- Produces final verdicts
- Generates summary tables
- Saves JSON results

**Output files:**
- Console output (detailed)
- JSON results (in memory, printed to stdout)

### Option 2: Test Individual Components

```python
# In Python REPL or script:
import asyncio
from support.tests.test_aoc_5agent_evaluation import (
    AsynchronousOrchestrationController,
    BROCCOLI_CONTENT
)

async def test_single():
    aoc = AsynchronousOrchestrationController()
    result = await aoc.evaluate(BROCCOLI_CONTENT)
    print(f"Verdict: {result.final_verdict}")
    print(f"Confidence: {result.confidence_score}%")

asyncio.run(test_single())
```

### Option 3: Custom Food Evaluation

```python
import asyncio
from support.tests.test_aoc_5agent_evaluation import (
    AsynchronousOrchestrationController
)

async def test_custom():
    custom_food = {
        "topic_kr": "당근",
        "topic_en": "carrot",
        "safety": "safe",
        "slides": [
            {"type": "cover", "title": "CARROT", "subtitle": "..."},
            {"type": "content_bottom", "title": "먹어도 돼요!", "subtitle": "..."},
            {"type": "content_bottom", "title": "주의사항", "subtitle": "..."},
            {"type": "cta", "title": "저장필수!", "subtitle": "..."},
        ],
        "captions": {
            "text": "당근은 안전한 간식입니다...",
            "hashtags": ["#당근", "#강아지"]
        }
    }

    aoc = AsynchronousOrchestrationController()
    result = await aoc.evaluate(custom_food)

    print(f"Status: {result.final_verdict}")
    print(f"Confidence: {result.confidence_score}%")
    for agent in result.agent_results:
        print(f"{agent.agent_id}: {agent.score}/100")

asyncio.run(test_custom())
```

---

## Understanding Results

### Final Verdict Types

#### 1. AUTO_PUBLISH ✅

**Meaning:** Content is approved for immediate publication

**Requirements Met:**
- Quality Score ≥ 85
- Safety Score ≥ 90
- Automation Ready = YES
- Red Flags ≤ 2
- Budget Compliant
- No conflicts

**Example:**
```
Broccoli: ✅ AUTO_PUBLISH (99% confidence)
Watermelon: ✅ AUTO_PUBLISH (99% confidence)
```

#### 2. HUMAN_QUEUE ⏳

**Meaning:** Content needs human review before publishing

**Reasons:**
- Quality Score < 85
- Safety Score < 90
- Automation Ready = NO
- Red Flags > 2
- Budget Exceeded
- Unresolved conflicts
- Edge case detected

**Example:**
```
MysteryMeat: ⏳ HUMAN_QUEUE
  Reason: Automation score 65 (requires manual approval)
  Conflicts: 1 (Agent C vs Agent D safety concern)
```

#### 3. BLOCKED ❌

**Meaning:** Content cannot be published - critical issues

**Reasons:**
- Dangerous food with no warning
- Forbidden character terms found
- Forbidden pose detected
- Multiple critical red flags
- Brand guideline violation
- Unsafe for dogs

**Example:**
```
ChocolateCake: ❌ BLOCKED
  Reason: Critical - Toxic food without warning
  Red Flags: 3 (critical)
```

### Confidence Score

**Range:** 0-100%
**Calculation:** Average of all 5 agent scores

```
High Confidence (90-100%):
  • All agents in agreement
  • No conflicts detected
  • Quality meets all standards
  → Highly reliable verdict

Medium Confidence (70-90%):
  • Most agents in agreement
  • Minor conflicts resolved
  • One or two items slightly below threshold
  → Generally reliable, minor review recommended

Low Confidence (<70%):
  • Significant agent disagreement
  • Multiple conflicts detected
  • Several items below threshold
  → Requires human review
```

### Questions Asked

**Expected Value:** 0 (for properly formatted content)

**If > 0:** System encountered ambiguity
```
Questions Asked: 0  → Fully autonomous decision
Questions Asked: 1+ → Human input needed for clarification
```

---

## Agent Descriptions

### Agent A: Content Check (A_CC)

**Purpose:** Validates content structure and format compliance

**Checks:**
- ✅ Required fields present (topic_kr, topic_en, safety, slides, captions)
- ✅ Metadata complete
- ✅ Slides properly formatted (4-slide v6 standard)
- ✅ Captions have both text and hashtags
- ✅ No format errors

**Scoring:**
- 100 points possible
- Deductions: -30 (missing fields), -25 (invalid format), -20 (caption issues)

**Output:**
```
Agent A: Content Check
Score: 100/100
Status: APPROVED

Findings:
  - structure_valid: True
  - metadata_complete: True
  - format_compliant: True
  - slide_count: 4
  - caption_format_valid: True
```

### Agent B: Quality Scores (B_QS)

**Purpose:** Evaluates content quality across 5 dimensions

**5 Dimensions (20 points each):**

1. **Accuracy (20 pts)** - Information correctness
   - No contradictions between safety classification and content
   - Serving sizes match pet size categories
   - Safety information accurate

2. **Tone (20 pts)** - Emotional quality
   - Positive and encouraging
   - No negative language
   - Appropriate for audience

3. **Format (20 pts)** - Structure quality
   - Proper slide structure
   - Caption completeness
   - Visual organization

4. **Coherence (20 pts)** - Logical flow
   - Slides follow logical progression
   - Messages reinforce each other
   - Clear narrative arc

5. **Policy Compliance (20 pts)** - Rule adherence
   - CLAUDE.md guidelines met
   - Safety messaging appropriate
   - Brand guidelines followed

**Total Score:** 100 points max

**Output:**
```
Agent B: Quality Scores
Score: 95/100

Breakdown:
  - Accuracy: 20/20
  - Tone: 20/20
  - Format: 20/20
  - Coherence: 20/20
  - Policy: 15/20 (minor: caution message)
```

### Agent C: Automation Judgment (C_AJ)

**Purpose:** Determines if content is ready for automated publishing

**Criteria:**
- ✅ Safety classification is valid (SAFE/CAUTION/DANGEROUS)
- ✅ All required slides present
- ✅ Captions complete
- ✅ Metadata filled in
- ✅ No dangerous terms
- ✅ Appropriate warnings for CAUTION/DANGEROUS foods

**Output:**
```
Agent C: Automation Judgment
Score: 100/100
Verdict: AUTO_PUBLISH

Findings:
  - auto_publishable: True
  - intervention_points: 0
  - readiness_score: 100
```

### Agent D: Red Flag Detection (D_RF)

**Purpose:** Detects safety, brand, and timing issues

**Red Flag Categories:**

**CRITICAL (Immediate Block):**
- Forbidden character terms (puppy, baby dog, young)
- Forbidden poses in description (eating, licking, biting)
- No warning for dangerous food

**HIGH (Requires Review):**
- Safety classification mismatch (SAFE with danger warnings)
- Insufficient safety messaging
- Incomplete information for CAUTION foods

**MEDIUM (Monitor):**
- Missing serving size info
- Topic consistency issues
- Minor formatting issues

**LOW (Informational):**
- Hashtag suggestions
- Optimization recommendations

**Output:**
```
Agent D: Red Flag Detection
Score: 100/100

Findings:
  - red_flags_detected: 0
  - safety_score: 100
  - critical_flags: 0
  - high_flags: 0
  - medium_flags: 0
  - low_flags: 0
```

### Agent E: Cost Estimation (E_CE)

**Purpose:** Tracks API usage and budget compliance

**Cost Categories:**

1. **Image Generation** ($0.05/image via FLUX.2-pro)
2. **Caption Generation** ($0.001/call via Claude API)
3. **Instagram Publishing** (Free via Graph API)
4. **Cloudinary Storage** (Free in project plan)

**Budget Check:**
- Per-item budget: $1.00
- Typical cost: $0.20-0.30
- Compliance check: $ ≤ $1.00

**Output:**
```
Agent E: Cost Estimation
Score: 100/100

Findings:
  - estimated_api_calls: 10
  - estimated_cost_usd: 0.2010
  - budget_compliant: True

Breakdown:
  - Image Generation: 4 × $0.05 = $0.20
  - Caption: 1 × $0.001 = $0.001
  - Instagram: Free
  - Storage: Free
  Total: $0.2010 (Budget: 20% utilization)
```

---

## Conflict Resolution

### What Are Conflicts?

**Conflicts** occur when agents disagree on a verdict or when one agent's finding contradicts another.

### Conflict Types

#### 1. Judgment Conflict (Severity: HIGH)

**Scenario:** Agent C says AUTO_PUBLISH but Agent D found red flags

```
Example:
  Agent C: Auto publishable ✅
  Agent D: 3 critical red flags ❌

Resolution:
  → HUMAN_QUEUE (defer to safety)
  → Human review required
```

**When It Happens:**
- Automation ready but safety concerns
- Policy compliance conflict
- Brand guideline questions

#### 2. Quality Conflict (Severity: HIGH)

**Scenario:** Agent B quality score < 85 but Agent C says AUTO_PUBLISH

```
Example:
  Agent B: 65/100 (Below threshold)
  Agent C: Auto publishable ✅

Resolution:
  → HUMAN_QUEUE (quality must be 85+)
  → Quality issues must be addressed first
```

**When It Happens:**
- Poor information accuracy
- Tone issues
- Incoherent messaging

#### 3. Budget Conflict (Severity: MEDIUM)

**Scenario:** Cost exceeds budget but automation requested

```
Example:
  Agent E: $1.50 cost (exceeds $1.00 budget)
  Agent C: Auto publishable ✅

Resolution:
  → BLOCKED (requires approval)
  → Budget approval needed before publishing
```

**When It Happens:**
- Unexpectedly high image generation costs
- Additional API calls needed
- Premium processing required

#### 4. Timing Conflict (Severity: LOW)

**Scenario:** Requested publish time conflicts with existing schedule

```
Example:
  Existing: Broccoli scheduled for 6:00 PM
  Request: Watermelon also scheduled for 6:00 PM

Resolution:
  → Defer second item to next available slot (6:30 PM)
  → Or move to next day if preferred
```

**When It Happens:**
- Multiple items publishing simultaneously
- Resource contention on servers
- Bandwidth limits reached

### Conflict Detection Example

```python
# The system automatically detects:
if agent_c_verdict == "AUTO_PUBLISH" and agent_d_red_flags > 2:
    conflict = ParallelConflict(
        conflict_type="judgment",
        agents_involved=["C_AJ", "D_RF"],
        description="Safety concern vs Automation",
        severity="high",
        resolution="Use HUMAN_QUEUE due to red flags"
    )
    # System resolves to HUMAN_QUEUE automatically
```

### How Conflicts Are Resolved

```
Conflict Detected?
  │
  ├─ CRITICAL Severity → BLOCKED (stop immediately)
  │
  ├─ HIGH Severity → HUMAN_QUEUE (human review)
  │                    (override Agent C if safety issue)
  │
  ├─ MEDIUM Severity → HUMAN_QUEUE (flag for review)
  │                     (can be overridden with caution)
  │
  └─ LOW Severity → AUTO_PUBLISH (informational only)
                    (proceed with warning)
```

---

## Troubleshooting

### Issue: "All agents returned 0 scores"

**Cause:** Empty or malformed content dictionary

**Solution:**
```python
# Ensure content has all required fields:
content = {
    "topic_kr": "음식명",           # Required
    "topic_en": "food_name",        # Required
    "safety": "safe",               # Required: safe/caution/dangerous
    "slides": [                      # Required: list of slides
        {"type": "cover", "title": "...", "subtitle": "..."},
        {"type": "content_bottom", "title": "...", "subtitle": "..."},
        {"type": "content_bottom", "title": "...", "subtitle": "..."},
        {"type": "cta", "title": "...", "subtitle": "..."},
    ],
    "captions": {                    # Required
        "text": "Caption text here",
        "hashtags": ["#tag1", "#tag2"]
    }
}
```

### Issue: "HUMAN_QUEUE verdict but no conflicts detected"

**Cause:** One or more agents below threshold (e.g., quality < 85)

**Solution:**
Check individual agent scores:
```python
for agent in result.agent_results:
    if agent.score < 70:
        print(f"{agent.agent_id} below threshold: {agent.score}/100")
        for issue in agent.issues:
            print(f"  Issue: {issue}")
```

### Issue: "Budget Exceeded"

**Cause:** Too many slides or high API usage

**Solution:**
```
# Standard: 4 slides × $0.05 = $0.20
# But if you need more images:
  - 7 slides × $0.05 = $0.35 ✓ (still under $1)
  - 10 slides × $0.05 = $0.50 ✓ (still under $1)
  - 20 slides × $0.05 = $1.00 ✓ (at limit)
  - 25 slides × $0.05 = $1.25 ✗ (exceeds budget)

# Solution: Reduce slides or request budget increase
```

### Issue: "Confidence score unusually low (< 50%)"

**Cause:** Significant agent disagreement or multiple issues

**Solution:**
```python
# Analyze each agent's findings:
for agent in result.agent_results:
    print(f"{agent.agent_id}: {agent.score}/100")
    if agent.issues:
        print("Issues:")
        for issue in agent.issues:
            print(f"  - {issue}")
    if agent.warnings:
        print("Warnings:")
        for warning in agent.warnings:
            print(f"  - {warning}")

# Address the lowest-scoring agent first
```

### Issue: "TypeError: 'NoneType' object is not subscriptable"

**Cause:** Missing field in content dictionary

**Solution:**
```python
# Verify all required fields:
required = ["topic_kr", "topic_en", "safety", "slides", "captions"]
for field in required:
    if field not in content:
        print(f"Missing required field: {field}")
        # Add the missing field before evaluation
```

---

## API Reference

### Main Class: AsynchronousOrchestrationController

```python
class AsynchronousOrchestrationController:
    """
    Coordinates parallel evaluation by 5 agents with conflict detection
    """

    async def evaluate(content: Dict[str, Any]) -> AOCEvaluationResult:
        """
        Parallel evaluation using 5 agents

        Args:
            content (Dict): Food content to evaluate
                Required keys:
                  - topic_kr (str): Korean food name
                  - topic_en (str): English food name
                  - safety (str): "safe", "caution", or "dangerous"
                  - slides (List[Dict]): List of slide objects
                  - captions (Dict): Caption with text and hashtags

        Returns:
            AOCEvaluationResult: Comprehensive evaluation result
                - content_id: Content identifier
                - safety_classification: Safety level
                - agent_results: List of agent evaluations
                - parallel_conflicts: List of detected conflicts
                - final_verdict: AUTO_PUBLISH, HUMAN_QUEUE, or BLOCKED
                - publishable: Boolean ready status
                - confidence_score: 0-100% confidence
                - questions_asked: Number of user questions (0 = autonomous)
                - total_execution_time_ms: Parallel execution time
```

### Data Classes

#### AOCEvaluationResult

```python
@dataclass
class AOCEvaluationResult:
    content_id: str                          # Content identifier
    topic_kr: str                            # Korean topic name
    topic_en: str                            # English topic name
    safety_classification: str               # "safe", "caution", "dangerous"
    timestamp: str                           # ISO format timestamp
    agent_results: List[AgentEvaluationResult]  # 5 agent results
    parallel_conflicts: List[ParallelConflict]  # Detected conflicts
    consensus_verdict: str                   # Agent consensus
    total_execution_time_ms: float           # Parallel execution time
    questions_asked: int                     # Questions to user (0 = autonomous)
    confidence_score: float                  # 0-100% confidence
    final_verdict: str                       # AUTO_PUBLISH, HUMAN_QUEUE, BLOCKED
    publishable: bool                        # Ready status
```

#### AgentEvaluationResult

```python
@dataclass
class AgentEvaluationResult:
    agent_name: str                          # Full agent name
    agent_id: str                            # Short ID (A_CC, B_QS, etc.)
    timestamp: str                           # ISO timestamp
    execution_time_ms: float                 # Execution time in milliseconds
    status: str                              # "completed", "error", etc.
    score: float                             # 0-100 score
    verdict: Optional[str]                   # AUTO_PUBLISH, HUMAN_QUEUE, etc.
    findings: Dict[str, Any]                 # Agent-specific findings
    issues: List[str]                        # Critical issues found
    warnings: List[str]                      # Non-critical warnings
    resources_used: Dict[str, Any]           # API calls, memory, etc.
```

### Usage Examples

#### Basic Evaluation

```python
import asyncio
from support.tests.test_aoc_5agent_evaluation import (
    AsynchronousOrchestrationController
)

async def evaluate_food():
    content = {
        "topic_kr": "당근",
        "topic_en": "carrot",
        "safety": "safe",
        "slides": [...],  # 4 slides required
        "captions": {
            "text": "...",
            "hashtags": [...]
        }
    }

    aoc = AsynchronousOrchestrationController()
    result = await aoc.evaluate(content)

    print(f"Status: {result.final_verdict}")
    print(f"Confidence: {result.confidence_score}%")
    print(f"Ready to publish: {result.publishable}")

asyncio.run(evaluate_food())
```

#### Detailed Analysis

```python
result = await aoc.evaluate(content)

# Check each agent
for agent in result.agent_results:
    print(f"\n{agent.agent_id}: {agent.score}/100")
    print(f"  Verdict: {agent.verdict}")
    if agent.issues:
        print(f"  Issues:")
        for issue in agent.issues:
            print(f"    - {issue}")

# Check conflicts
if result.parallel_conflicts:
    print(f"\n⚠️  {len(result.parallel_conflicts)} conflicts detected")
    for conflict in result.parallel_conflicts:
        print(f"  {conflict.conflict_type}: {conflict.description}")
else:
    print("\n✅ No conflicts detected")
```

---

## Success Criteria

Your AOC system is working correctly if:

✅ **Parallel Execution**
- 5 agents run simultaneously (not sequentially)
- Total execution time < 5ms

✅ **Correct Verdicts**
- SAFE foods with proper warnings → AUTO_PUBLISH
- Dangerous foods without warnings → HUMAN_QUEUE or BLOCKED
- CAUTION foods with caveats → AUTO_PUBLISH
- Incomplete content → HUMAN_QUEUE

✅ **Zero Questions**
- questions_asked = 0 (for well-formed content)
- All decisions made autonomously

✅ **High Confidence**
- Typical confidence 90-99%
- Low confidence (<70%) only for edge cases

✅ **No False Positives**
- SAFE foods not incorrectly blocked
- No unnecessary HUMAN_QUEUE verdicts

---

## Support & Questions

For issues or questions about the AOC system:

1. Check the Troubleshooting section above
2. Review the Agent Descriptions for specific behavior
3. Check test results in `/docs/AOC_5AGENT_TEST_REPORT.md`
4. Run test suite to verify system health

---

**AOC 5-Agent Parallel Evaluation System**
**Version 1.0 - Production Ready ✅**
**Last Updated: 2026-01-31**
