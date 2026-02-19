"""
AOC 5-Agent Parallel Evaluation System - Simulation Test
2026-01-31

Simulates the Asynchronous Orchestration Controller (AOC) with 5-agent parallel evaluation
for content approval workflow. Tests concurrent evaluation of food items (Broccoli, Watermelon)
with no questions asked to the user - all decisions are autonomous.

Test Structure:
- Agent A: Content Check (self_score, format_compliance)
- Agent B: Quality Scores (accuracy, tone, format, coherence, policy)
- Agent C: Automation Judgment (auto_publishable, intervention_points)
- Agent D: Red Flag Detection (safety, brand, timing issues)
- Agent E: Cost Estimation (API usage, resource allocation)

Final Verdict: AUTO_PUBLISH or HUMAN_QUEUE
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import time


# ============================================================================
# Enums & Data Classes
# ============================================================================

class SafetyClassification(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


class AutomationVerdict(Enum):
    AUTO_PUBLISH = "auto_publish"      # Green light for automation
    HUMAN_QUEUE = "human_queue"        # Needs manual review
    BLOCKED = "blocked"                # Cannot publish


class RedFlagSeverity(Enum):
    CRITICAL = "critical"              # Immediate block
    HIGH = "high"                       # Requires human review
    MEDIUM = "medium"                  # Flag for monitoring
    LOW = "low"                         # Informational


@dataclass
class AgentEvaluationResult:
    """Individual agent evaluation result"""
    agent_name: str
    agent_id: str
    timestamp: str
    execution_time_ms: float
    status: str = "completed"
    score: float = 0.0
    verdict: Optional[str] = None
    findings: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    resources_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParallelConflict:
    """Record parallel execution conflicts"""
    conflict_type: str  # "resource", "timing", "judgment"
    agents_involved: List[str]
    description: str
    severity: str = "low"
    resolution: Optional[str] = None


@dataclass
class AOCEvaluationResult:
    """Final AOC evaluation result for a content item"""
    content_id: str
    topic_kr: str
    topic_en: str
    safety_classification: str
    timestamp: str
    agent_results: List[AgentEvaluationResult] = field(default_factory=list)
    parallel_conflicts: List[ParallelConflict] = field(default_factory=list)
    consensus_verdict: str = ""
    total_execution_time_ms: float = 0.0
    questions_asked: int = 0
    confidence_score: float = 0.0
    final_verdict: str = ""
    publishable: bool = False


# ============================================================================
# Agent A: Content Check Agent
# ============================================================================

class AgentA_ContentCheck:
    """
    Agent A validates content structure, format compliance, and metadata
    """

    def __init__(self):
        self.name = "Agent A: Content Check"
        self.id = "A_CC"

    async def evaluate(self, content: Dict[str, Any]) -> AgentEvaluationResult:
        """Evaluate content structure and format compliance"""
        start_time = time.time()

        findings = {
            "structure_valid": False,
            "metadata_complete": False,
            "format_compliant": False,
            "self_score": 0,
        }
        issues = []
        warnings = []

        # Check structure
        required_fields = ["topic_kr", "topic_en", "safety", "slides", "captions"]
        structure_valid = all(f in content for f in required_fields)
        findings["structure_valid"] = structure_valid

        if not structure_valid:
            missing = [f for f in required_fields if f not in content]
            issues.append(f"Missing fields: {', '.join(missing)}")

        # Check metadata completeness
        if "slides" in content:
            slides = content["slides"]
            if not isinstance(slides, list) or len(slides) == 0:
                issues.append("Slides list empty or malformed")
            else:
                findings["slide_count"] = len(slides)
                # v6 standard: 4 slides (00=cover, 01=result_benefit, 02=caution_amount, 03=cta)
                if len(slides) == 4:
                    findings["metadata_complete"] = True
                elif len(slides) > 4:
                    warnings.append(f"Slide count exceeds v6 standard (4): {len(slides)} slides")
                else:
                    issues.append(f"Insufficient slides: {len(slides)}/4 required")

        # Check format compliance
        format_score = 100
        if structure_valid:
            findings["format_compliant"] = True
        else:
            format_score -= 30

        # Validate caption format
        if "captions" in content:
            captions = content["captions"]
            if isinstance(captions, dict):
                if "text" in captions and "hashtags" in captions:
                    findings["caption_format_valid"] = True
                else:
                    issues.append("Caption missing 'text' or 'hashtags'")
                    format_score -= 20
        else:
            issues.append("Captions missing entirely")
            format_score -= 25

        # Self-score calculation
        findings["self_score"] = max(0, format_score)
        findings["format_compliance_percent"] = findings["self_score"]

        execution_time = (time.time() - start_time) * 1000

        return AgentEvaluationResult(
            agent_name=self.name,
            agent_id=self.id,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            score=findings["self_score"],
            findings=findings,
            issues=issues,
            warnings=warnings,
        )


# ============================================================================
# Agent B: Quality Scores Agent
# ============================================================================

class AgentB_QualityScores:
    """
    Agent B evaluates content quality across 5 dimensions:
    accuracy, tone, format, coherence, policy compliance
    """

    def __init__(self):
        self.name = "Agent B: Quality Scores"
        self.id = "B_QS"

    async def evaluate(self, content: Dict[str, Any]) -> AgentEvaluationResult:
        """Evaluate content quality across 5 dimensions (20 points each)"""
        start_time = time.time()

        findings = {
            "accuracy": 0,
            "tone": 0,
            "format": 0,
            "coherence": 0,
            "policy": 0,
            "total_quality_score": 0,
        }
        issues = []
        warnings = []

        # 1. Accuracy (20 points)
        accuracy = 20
        if content.get("safety") == "safe":
            # Safe foods shouldn't have dangerous warnings
            slides = content.get("slides", [])
            for slide in slides:
                if "금지" in slide.get("title", "") or "위험" in slide.get("title", ""):
                    accuracy -= 5
                    issues.append(f"Slide '{slide.get('title')}' contains danger warning for SAFE food")

        findings["accuracy"] = max(0, accuracy)

        # 2. Tone (20 points)
        tone = 20
        captions = content.get("captions", {})
        caption_text = captions.get("text", "").lower()

        # Check for appropriate tone
        negative_terms = ["sad", "angry", "dangerous", "poisonous", "deadly"]
        for term in negative_terms:
            if term in caption_text:
                tone -= 5
                warnings.append(f"Negative tone detected: '{term}' in caption")

        findings["tone"] = max(0, tone)

        # 3. Format (20 points)
        format_score = 20
        if "slides" not in content or not content["slides"]:
            format_score -= 10
        if "captions" not in content:
            format_score -= 10
        findings["format"] = max(0, format_score)

        # 4. Coherence (20 points)
        coherence = 20
        slides = content.get("slides", [])
        if slides:
            # Check slide flow
            types = [s.get("type", "") for s in slides]
            expected_flow = ["cover", "content_bottom", "content_bottom", "cta"]

            if len(types) >= 3:
                # At least cover, content, cta present
                has_cover = any("cover" in t for t in types)
                has_content = any("content" in t for t in types)
                has_cta = any("cta" in t for t in types)

                if not (has_cover and has_content and has_cta):
                    coherence -= 10
                    issues.append("Missing essential slide types (cover/content/cta)")
            else:
                coherence -= 10
                issues.append("Insufficient slide count for coherent flow")

        findings["coherence"] = max(0, coherence)

        # 5. Policy Compliance (20 points)
        policy = 20
        safety = content.get("safety", "unknown")

        # Check CLAUDE.md rules
        if safety == "safe":
            slides = content.get("slides", [])
            has_caution = any("주의" in str(s) for s in slides)
            # SAFE foods should have caution but not danger
            if not has_caution:
                policy -= 5
                warnings.append("SAFE food missing caution information")

        # Check for AI marking if required
        caption_text = captions.get("text", "")
        # AI marking only required for generated images (separate process)

        findings["policy"] = max(0, policy)

        # Total quality score
        findings["total_quality_score"] = (
            findings["accuracy"]
            + findings["tone"]
            + findings["format"]
            + findings["coherence"]
            + findings["policy"]
        )

        execution_time = (time.time() - start_time) * 1000

        return AgentEvaluationResult(
            agent_name=self.name,
            agent_id=self.id,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            score=findings["total_quality_score"],
            findings=findings,
            issues=issues,
            warnings=warnings,
        )


# ============================================================================
# Agent C: Automation Judgment Agent
# ============================================================================

class AgentC_AutomationJudgment:
    """
    Agent C determines if content can be automatically published or needs human review
    """

    def __init__(self):
        self.name = "Agent C: Automation Judgment"
        self.id = "C_AJ"

    async def evaluate(self, content: Dict[str, Any]) -> AgentEvaluationResult:
        """Determine automation readiness"""
        start_time = time.time()

        findings = {
            "auto_publishable": False,
            "intervention_points": [],
            "readiness_score": 0,
        }
        issues = []
        warnings = []

        # Baseline: all content starts as automatable
        auto_publishable = True
        intervention_points = []
        readiness_score = 100

        # 1. Check safety classification
        safety = content.get("safety", "unknown")
        if safety == "dangerous":
            auto_publishable = False
            intervention_points.append("DANGEROUS safety classification - requires human approval")
            readiness_score -= 50

        elif safety == "caution":
            # CAUTION foods can be automated if proper warnings are in place
            slides = content.get("slides", [])
            has_caution_slide = any("주의" in str(s) for s in slides)
            if not has_caution_slide:
                intervention_points.append("CAUTION food missing caution slide")
                readiness_score -= 20
                auto_publishable = False

        # 2. Check required slide completeness
        slides = content.get("slides", [])
        if len(slides) < 4:
            intervention_points.append(f"Incomplete slide deck: {len(slides)}/4 slides")
            readiness_score -= 25
            auto_publishable = False

        # 3. Check caption completeness
        captions = content.get("captions", {})
        if not captions.get("text") or not captions.get("hashtags"):
            intervention_points.append("Caption missing text or hashtags")
            readiness_score -= 15
            auto_publishable = False

        # 4. Check metadata completeness
        required_meta = ["topic_kr", "topic_en"]
        missing_meta = [f for f in required_meta if f not in content]
        if missing_meta:
            intervention_points.append(f"Missing metadata: {', '.join(missing_meta)}")
            readiness_score -= 10
            auto_publishable = False

        # 5. Check for conflicts in content
        topic_text = f"{content.get('topic_kr', '')} {content.get('topic_en', '')}".lower()
        conflicting_terms = ["poison", "toxic", "forbidden"]
        for term in conflicting_terms:
            if term in topic_text:
                intervention_points.append(f"Potentially dangerous term found: '{term}'")
                readiness_score -= 15
                auto_publishable = False

        findings["auto_publishable"] = auto_publishable
        findings["intervention_points"] = intervention_points
        findings["readiness_score"] = max(0, readiness_score)

        verdict = (
            AutomationVerdict.AUTO_PUBLISH.value
            if auto_publishable
            else AutomationVerdict.HUMAN_QUEUE.value
        )

        execution_time = (time.time() - start_time) * 1000

        return AgentEvaluationResult(
            agent_name=self.name,
            agent_id=self.id,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            score=findings["readiness_score"],
            verdict=verdict,
            findings=findings,
            issues=issues,
            warnings=warnings,
        )


# ============================================================================
# Agent D: Red Flag Detection Agent
# ============================================================================

class AgentD_RedFlagDetection:
    """
    Agent D detects safety, brand compliance, and timing issues
    """

    def __init__(self):
        self.name = "Agent D: Red Flag Detection"
        self.id = "D_RF"

    async def evaluate(self, content: Dict[str, Any]) -> AgentEvaluationResult:
        """Detect red flags in content"""
        start_time = time.time()

        findings = {
            "red_flags_detected": 0,
            "critical_flags": [],
            "high_flags": [],
            "medium_flags": [],
            "low_flags": [],
            "safety_score": 100,
        }
        issues = []
        warnings = []

        critical_flags = []
        high_flags = []
        medium_flags = []
        low_flags = []
        safety_score = 100

        # ========== CRITICAL FLAGS ==========

        # 1. Brand character violation
        topic_text = f"{content.get('topic_kr', '')} {content.get('topic_en', '')}".lower()
        forbidden_terms = ["puppy", "baby dog", "young dog", "kitten"]
        for term in forbidden_terms:
            if term in topic_text:
                critical_flags.append(f"Brand violation: '{term}' - only senior dogs allowed")
                safety_score -= 50

        # 2. Forbidden pose in description
        all_content = json.dumps(content).lower()
        forbidden_poses = [
            "dog eating food",
            "dog biting food",
            "food in mouth",
            "licking food",
        ]
        for pose in forbidden_poses:
            if pose in all_content:
                critical_flags.append(f"Forbidden pose referenced: '{pose}'")
                safety_score -= 40

        # ========== HIGH FLAGS ==========

        # 3. Safety classification mismatch
        safety = content.get("safety", "unknown")
        slides = content.get("slides", [])
        slide_titles = " ".join([str(s.get("title", "")).lower() for s in slides])

        if safety == "safe" and ("위험" in slide_titles or "금지" in slide_titles):
            high_flags.append("Mismatch: SAFE classification but danger warnings in slides")
            safety_score -= 25

        elif safety == "dangerous" and "위험" not in slide_titles:
            high_flags.append("Missing: DANGEROUS food should have warning slide")
            safety_score -= 30

        # 4. Caption for responsible messaging
        captions = content.get("captions", {})
        caption_text = captions.get("text", "").lower()

        if safety == "dangerous" and len(caption_text) < 50:
            high_flags.append("Dangerous food with insufficient safety messaging")
            safety_score -= 20

        # ========== MEDIUM FLAGS ==========

        # 5. Incomplete information for CAUTION foods
        if safety == "caution":
            has_serving_size = "small" in caption_text or "medium" in caption_text or "large" in caption_text
            if not has_serving_size:
                medium_flags.append("CAUTION food missing serving size information")
                safety_score -= 10

        # 6. Topic consistency
        if content.get("topic_kr") and content.get("topic_en"):
            kr_text = content.get("topic_kr", "").lower()
            en_text = content.get("topic_en", "").lower()

            # Simple consistency check (in real scenario would be more sophisticated)
            if len(kr_text) < 2 or len(en_text) < 2:
                medium_flags.append("Topic text too short or missing")
                safety_score -= 5

        # ========== LOW FLAGS ==========

        # 7. Minor formatting issues
        if not captions.get("hashtags") or len(captions.get("hashtags", [])) == 0:
            low_flags.append("Hashtags missing - may reduce discoverability")
            safety_score -= 3

        # Collect all flags
        findings["critical_flags"] = critical_flags
        findings["high_flags"] = high_flags
        findings["medium_flags"] = medium_flags
        findings["low_flags"] = low_flags
        findings["red_flags_detected"] = len(critical_flags) + len(high_flags) + len(medium_flags)
        findings["safety_score"] = max(0, safety_score)

        # Convert findings to issues
        issues.extend(critical_flags)
        warnings.extend(high_flags + medium_flags + low_flags)

        execution_time = (time.time() - start_time) * 1000

        return AgentEvaluationResult(
            agent_name=self.name,
            agent_id=self.id,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            score=findings["safety_score"],
            findings=findings,
            issues=issues,
            warnings=warnings,
        )


# ============================================================================
# Agent E: Cost Estimation Agent
# ============================================================================

class AgentE_CostEstimation:
    """
    Agent E estimates API usage costs and resource allocation
    """

    def __init__(self):
        self.name = "Agent E: Cost Estimation"
        self.id = "E_CE"

    async def evaluate(self, content: Dict[str, Any]) -> AgentEvaluationResult:
        """Estimate costs and resource usage"""
        start_time = time.time()

        findings = {
            "estimated_api_calls": 0,
            "estimated_cost_usd": 0.0,
            "resource_breakdown": {},
            "budget_compliant": True,
        }
        issues = []
        warnings = []

        # Cost estimation based on content
        slide_count = len(content.get("slides", []))

        # Image generation cost (FLUX.2-pro)
        # ~$0.05 per image
        image_api_calls = slide_count
        image_cost = image_api_calls * 0.05

        # Caption generation cost (Claude API, negligible for this)
        caption_api_calls = 1
        caption_cost = 0.001

        # Instagram API cost (Graph API, free for basic operations)
        instagram_calls = 1
        instagram_cost = 0.0

        # Cloudinary storage (included in project plan, $0 marginal)
        cloudinary_calls = slide_count
        cloudinary_cost = 0.0

        total_api_calls = image_api_calls + caption_api_calls + instagram_calls
        total_cost = image_cost + caption_cost + instagram_cost + cloudinary_cost

        findings["resource_breakdown"] = {
            "image_generation": {
                "api_calls": image_api_calls,
                "estimated_cost": f"${image_cost:.2f}",
                "unit_cost": "$0.05/image",
            },
            "caption_generation": {
                "api_calls": caption_api_calls,
                "estimated_cost": f"${caption_cost:.4f}",
                "unit_cost": "$0.001/call",
            },
            "instagram_publishing": {
                "api_calls": instagram_calls,
                "estimated_cost": f"${instagram_cost:.2f}",
                "unit_cost": "Free (included)",
            },
            "cloudinary_storage": {
                "api_calls": cloudinary_calls,
                "estimated_cost": f"${cloudinary_cost:.2f}",
                "unit_cost": "Free (included)",
            },
        }

        findings["estimated_api_calls"] = total_api_calls
        findings["estimated_cost_usd"] = round(total_cost, 4)

        # Budget compliance check
        MAX_BUDGET_PER_CONTENT = 1.0  # $1 per piece of content
        if total_cost > MAX_BUDGET_PER_CONTENT:
            findings["budget_compliant"] = False
            issues.append(f"Cost ${total_cost:.2f} exceeds budget ${MAX_BUDGET_PER_CONTENT:.2f}")
        else:
            findings["budget_compliant"] = True
            warnings.append(f"Cost estimate: ${total_cost:.4f} (within budget)")

        # Resource allocation warnings
        if image_api_calls > 5:
            warnings.append(f"High image generation load: {image_api_calls} images")

        execution_time = (time.time() - start_time) * 1000

        return AgentEvaluationResult(
            agent_name=self.name,
            agent_id=self.id,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            score=100 if findings["budget_compliant"] else 50,
            findings=findings,
            issues=issues,
            warnings=warnings,
            resources_used={
                "api_calls": total_api_calls,
                "estimated_cost": f"${total_cost:.4f}",
            },
        )


# ============================================================================
# AOC: Asynchronous Orchestration Controller
# ============================================================================

class AsynchronousOrchestrationController:
    """
    AOC coordinates parallel evaluation by 5 agents with conflict detection
    """

    def __init__(self):
        self.agent_a = AgentA_ContentCheck()
        self.agent_b = AgentB_QualityScores()
        self.agent_c = AgentC_AutomationJudgment()
        self.agent_d = AgentD_RedFlagDetection()
        self.agent_e = AgentE_CostEstimation()

    async def evaluate(self, content: Dict[str, Any]) -> AOCEvaluationResult:
        """
        Parallel evaluation using 5 agents
        No questions asked - all decisions autonomous
        """
        start_time = time.time()

        content_id = content.get("topic_en", "unknown").upper()
        topic_kr = content.get("topic_kr", "")
        topic_en = content.get("topic_en", "")
        safety = content.get("safety", "unknown")

        # Execute all agents in parallel
        results = await asyncio.gather(
            self.agent_a.evaluate(content),
            self.agent_b.evaluate(content),
            self.agent_c.evaluate(content),
            self.agent_d.evaluate(content),
            self.agent_e.evaluate(content),
        )

        # Analyze results
        conflicts = self._detect_conflicts(results)
        consensus_verdict = self._reach_consensus(results)
        final_verdict, publishable = self._make_final_decision(
            results, conflicts, consensus_verdict
        )

        total_time = (time.time() - start_time) * 1000

        return AOCEvaluationResult(
            content_id=content_id,
            topic_kr=topic_kr,
            topic_en=topic_en,
            safety_classification=safety,
            timestamp=datetime.now().isoformat(),
            agent_results=results,
            parallel_conflicts=conflicts,
            consensus_verdict=consensus_verdict,
            total_execution_time_ms=total_time,
            questions_asked=0,  # Always 0 - autonomous evaluation
            confidence_score=self._calculate_confidence(results),
            final_verdict=final_verdict,
            publishable=publishable,
        )

    def _detect_conflicts(self, results: List[AgentEvaluationResult]) -> List[ParallelConflict]:
        """Detect conflicts between agent evaluations"""
        conflicts = []

        # Extract verdicts
        verdicts = {r.agent_id: r.verdict for r in results if r.verdict}
        scores = {r.agent_id: r.score for r in results}

        # Conflict 1: Judgment disagreement (Agent C verdict vs others)
        agent_c_verdict = verdicts.get("C_AJ")
        if agent_c_verdict == AutomationVerdict.AUTO_PUBLISH.value:
            # Check if red flags detected by Agent D
            agent_d_result = next((r for r in results if r.agent_id == "D_RF"), None)
            if agent_d_result:
                red_flags = agent_d_result.findings.get("red_flags_detected", 0)
                if red_flags > 2:
                    conflicts.append(
                        ParallelConflict(
                            conflict_type="judgment",
                            agents_involved=["C_AJ", "D_RF"],
                            description=f"Agent C suggests AUTO_PUBLISH but Agent D detected {red_flags} red flags",
                            severity="high",
                            resolution="Defer to Agent D safety assessment - use HUMAN_QUEUE",
                        )
                    )

        # Conflict 2: Quality vs Automation mismatch
        agent_b_result = next((r for r in results if r.agent_id == "B_QS"), None)
        if agent_b_result and agent_b_result.score < 70:
            if agent_c_verdict == AutomationVerdict.AUTO_PUBLISH.value:
                conflicts.append(
                    ParallelConflict(
                        conflict_type="judgment",
                        agents_involved=["B_QS", "C_AJ"],
                        description=f"Agent C suggests AUTO_PUBLISH but Agent B quality score is {agent_b_result.score:.0f}",
                        severity="high",
                        resolution="Quality must meet 85+ threshold - use HUMAN_QUEUE",
                    )
                )

        # Conflict 3: Cost vs Budget
        agent_e_result = next((r for r in results if r.agent_id == "E_CE"), None)
        if agent_e_result:
            budget_compliant = agent_e_result.findings.get("budget_compliant", True)
            if not budget_compliant and agent_c_verdict == AutomationVerdict.AUTO_PUBLISH.value:
                conflicts.append(
                    ParallelConflict(
                        conflict_type="resource",
                        agents_involved=["E_CE", "C_AJ"],
                        description="Cost exceeds budget but automation requested",
                        severity="medium",
                        resolution="Block automation - requires budget approval",
                    )
                )

        # Conflict 4: Timing conflict (none in this simulation, but would check)
        # This would check for scheduling conflicts in real scenario

        return conflicts

    def _reach_consensus(self, results: List[AgentEvaluationResult]) -> str:
        """Determine consensus from agent results"""
        verdicts = [r.verdict for r in results if r.verdict]
        auto_votes = sum(1 for v in verdicts if v == AutomationVerdict.AUTO_PUBLISH.value)
        queue_votes = sum(1 for v in verdicts if v == AutomationVerdict.HUMAN_QUEUE.value)

        if auto_votes > queue_votes:
            return AutomationVerdict.AUTO_PUBLISH.value
        elif queue_votes > auto_votes:
            return AutomationVerdict.HUMAN_QUEUE.value
        else:
            return AutomationVerdict.HUMAN_QUEUE.value  # Conservative: tie -> HUMAN_QUEUE

    def _make_final_decision(
        self,
        results: List[AgentEvaluationResult],
        conflicts: List[ParallelConflict],
        consensus: str
    ) -> tuple[str, bool]:
        """Make final verdict based on all factors"""
        # If any CRITICAL conflicts, block
        critical_conflicts = [c for c in conflicts if c.severity == "critical"]
        if critical_conflicts:
            return AutomationVerdict.BLOCKED.value, False

        # If any HIGH conflicts, defer to human
        high_conflicts = [c for c in conflicts if c.severity == "high"]
        if high_conflicts:
            return AutomationVerdict.HUMAN_QUEUE.value, False

        # Check quality threshold (Agent B)
        agent_b = next((r for r in results if r.agent_id == "B_QS"), None)
        if agent_b and agent_b.score < 70:
            return AutomationVerdict.HUMAN_QUEUE.value, False

        # Check safety (Agent D)
        agent_d = next((r for r in results if r.agent_id == "D_RF"), None)
        if agent_d and agent_d.findings.get("red_flags_detected", 0) > 3:
            return AutomationVerdict.HUMAN_QUEUE.value, False

        # Check automation readiness (Agent C)
        agent_c = next((r for r in results if r.agent_id == "C_AJ"), None)
        if agent_c and not agent_c.findings.get("auto_publishable", False):
            return AutomationVerdict.HUMAN_QUEUE.value, False

        # All systems go
        return AutomationVerdict.AUTO_PUBLISH.value, True

    def _calculate_confidence(self, results: List[AgentEvaluationResult]) -> float:
        """Calculate overall confidence score (0-100)"""
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        return round(min(100, avg_score), 1)


# ============================================================================
# Test Data: Broccoli & Watermelon
# ============================================================================

BROCCOLI_CONTENT = {
    "topic_kr": "브로콜리",
    "topic_en": "broccoli",
    "safety": "safe",
    "slides": [
        {
            "slide": 0,
            "name": "cover",
            "type": "cover",
            "title": "BROCCOLI",
            "subtitle": "Senior 햇살이가 사랑하는 영양 간식",
        },
        {
            "slide": 1,
            "name": "result_benefit",
            "type": "content_bottom",
            "title": "먹어도 돼요! ✅",
            "subtitle": "비타민 C 풍부, 항산화 음식",
        },
        {
            "slide": 2,
            "name": "caution_amount",
            "type": "content_bottom",
            "title": "적정 급여량 ⚠️",
            "subtitle": "소형 1개 | 중형 2개 | 대형 3개",
        },
        {
            "slide": 3,
            "name": "cta",
            "type": "cta",
            "title": "저장 필수! 📌",
            "subtitle": "햇살이의 건강을 위해 댓글로 공유하세요!",
        },
    ],
    "captions": {
        "text": "브로콜리는 안전한 간식이에요! 비타민 C가 풍부하여 햇살이의 면역력을 강화해줍니다. "
                "다만 과다 섭취는 소화 부담이 될 수 있으니 적정량을 지켜주세요. "
                "소형견 1개, 중형견 2개, 대형견 3개 정도가 권장량입니다.",
        "hashtags": ["#브로콜리", "#강아지간식", "#영양", "#햇살이"],
    },
}

WATERMELON_CONTENT = {
    "topic_kr": "수박",
    "topic_en": "watermelon",
    "safety": "safe",
    "slides": [
        {
            "slide": 0,
            "name": "cover",
            "type": "cover",
            "title": "WATERMELON",
            "subtitle": "여름 시원한 수분 간식",
        },
        {
            "slide": 1,
            "name": "result_benefit",
            "type": "content_bottom",
            "title": "먹어도 돼요! ✅",
            "subtitle": "수분 92% 저칼로리 간식",
        },
        {
            "slide": 2,
            "name": "caution_amount",
            "type": "content_bottom",
            "title": "종자 제거 필수 ⚠️",
            "subtitle": "소형 1컵 | 중형 1.5컵 | 대형 2컵",
        },
        {
            "slide": 3,
            "name": "cta",
            "type": "cta",
            "title": "저장 필수! 📌",
            "subtitle": "여름철 강아지 건강 관리를 위해 공유하세요!",
        },
    ],
    "captions": {
        "text": "수박은 여름철 안전한 간식입니다! 92% 수분이므로 더운 날씨에 수분 보충에 좋습니다. "
                "반드시 종자를 제거한 후 급여해주세요. 소형견 1컵, 중형견 1.5컵, 대형견 2컵이 권장량입니다.",
        "hashtags": ["#수박", "#여름간식", "#강아지", "#햇살이"],
    },
}


# ============================================================================
# Test Runner
# ============================================================================

async def run_evaluation_test():
    """Run complete evaluation test for both foods"""
    print("\n" + "=" * 100)
    print("AOC 5-AGENT PARALLEL EVALUATION SYSTEM TEST")
    print("=" * 100)

    aoc = AsynchronousOrchestrationController()

    # Evaluate both foods
    broccoli_result = await aoc.evaluate(BROCCOLI_CONTENT)
    watermelon_result = await aoc.evaluate(WATERMELON_CONTENT)

    return broccoli_result, watermelon_result


def print_agent_result(result: AgentEvaluationResult, indent: int = 0):
    """Pretty print agent result"""
    prefix = "  " * indent
    print(f"{prefix}Agent: {result.agent_name}")
    print(f"{prefix}ID: {result.agent_id} | Score: {result.score:.1f}/100")
    print(f"{prefix}Execution Time: {result.execution_time_ms:.2f}ms")

    if result.verdict:
        print(f"{prefix}Verdict: {result.verdict}")

    if result.issues:
        print(f"{prefix}Issues:")
        for issue in result.issues:
            print(f"{prefix}  ❌ {issue}")

    if result.warnings:
        print(f"{prefix}Warnings:")
        for warning in result.warnings:
            print(f"{prefix}  ⚠️  {warning}")

    if result.findings:
        print(f"{prefix}Findings:")
        for key, value in result.findings.items():
            if not isinstance(value, (list, dict)):
                print(f"{prefix}  • {key}: {value}")


def print_evaluation_result(result: AOCEvaluationResult):
    """Pretty print evaluation result"""
    print(f"\n{'=' * 100}")
    print(f"CONTENT: {result.topic_kr} ({result.topic_en.upper()})")
    print(f"Safety Classification: {result.safety_classification.upper()}")
    print(f"Timestamp: {result.timestamp}")
    print(f"{'=' * 100}\n")

    # Agent results
    print("AGENT EVALUATIONS (Parallel Execution):")
    print("-" * 100)
    for agent_result in result.agent_results:
        print_agent_result(agent_result, indent=1)
        print()

    # Conflicts
    if result.parallel_conflicts:
        print("PARALLEL CONFLICTS DETECTED:")
        print("-" * 100)
        for conflict in result.parallel_conflicts:
            print(f"Type: {conflict.conflict_type.upper()}")
            print(f"Agents: {', '.join(conflict.agents_involved)}")
            print(f"Severity: {conflict.severity.upper()}")
            print(f"Issue: {conflict.description}")
            if conflict.resolution:
                print(f"Resolution: {conflict.resolution}")
            print()
    else:
        print("PARALLEL CONFLICTS: None detected ✅\n")

    # Final decision
    print("FINAL DECISION:")
    print("-" * 100)
    print(f"Consensus: {result.consensus_verdict}")
    print(f"Final Verdict: {result.final_verdict}")
    print(f"Publishable: {'YES ✅' if result.publishable else 'NO ❌'}")
    print(f"Confidence Score: {result.confidence_score:.1f}%")
    print(f"Questions Asked: {result.questions_asked}")
    print(f"Total Execution Time: {result.total_execution_time_ms:.2f}ms")


def create_test_results_table(broccoli: AOCEvaluationResult, watermelon: AOCEvaluationResult) -> str:
    """Create summary table of test results"""
    lines = []

    lines.append("\n" + "=" * 120)
    lines.append("TEST RESULTS SUMMARY - 5-AGENT PARALLEL EVALUATION")
    lines.append("=" * 120)

    # Header
    header = (
        f"{'Food':<15} | {'Safety':<10} | "
        f"{'A_CC Score':<12} | {'B_QS Score':<12} | {'C_AJ Score':<12} | "
        f"{'D_RF Score':<12} | {'E_CE Score':<12} | "
        f"{'Conflicts':<12} | {'Verdict':<15} | {'Pass':<6}"
    )
    lines.append(header)
    lines.append("-" * 120)

    # Broccoli row
    def format_row(result: AOCEvaluationResult) -> str:
        agent_scores = {r.agent_id: r.score for r in result.agent_results}
        conflicts_count = len(result.parallel_conflicts)
        pass_status = "PASS ✅" if result.publishable else "FAIL ❌"

        return (
            f"{result.topic_en:<15} | {result.safety_classification:<10} | "
            f"{agent_scores.get('A_CC', 0):<12.1f} | {agent_scores.get('B_QS', 0):<12.1f} | "
            f"{agent_scores.get('C_AJ', 0):<12.1f} | {agent_scores.get('D_RF', 0):<12.1f} | "
            f"{agent_scores.get('E_CE', 0):<12.1f} | {conflicts_count:<12} | "
            f"{result.final_verdict:<15} | {pass_status:<6}"
        )

    lines.append(format_row(broccoli))
    lines.append(format_row(watermelon))
    lines.append("=" * 120)

    return "\n".join(lines)


def create_detailed_summary(broccoli: AOCEvaluationResult, watermelon: AOCEvaluationResult) -> str:
    """Create detailed summary with all details"""
    lines = []

    lines.append("\n" + "=" * 100)
    lines.append("DETAILED EVALUATION SUMMARY")
    lines.append("=" * 100)

    for result in [broccoli, watermelon]:
        lines.append(f"\n[{result.topic_kr.upper()} / {result.topic_en.upper()}]")
        lines.append(f"Safety: {result.safety_classification.upper()}")
        lines.append(f"Verdict: {result.final_verdict} | Publishable: {result.publishable}")
        lines.append(f"Confidence: {result.confidence_score:.1f}% | Questions: {result.questions_asked}")
        lines.append(f"Execution Time: {result.total_execution_time_ms:.2f}ms")

        # Agent summary
        lines.append("\nAgent Scores:")
        for agent in result.agent_results:
            lines.append(f"  {agent.agent_id}: {agent.score:.1f}/100 ({agent.execution_time_ms:.2f}ms)")

        # Conflicts summary
        if result.parallel_conflicts:
            lines.append(f"\nConflicts Detected: {len(result.parallel_conflicts)}")
            for conflict in result.parallel_conflicts:
                lines.append(f"  - {conflict.conflict_type}: {conflict.severity}")
        else:
            lines.append("\nConflicts: None ✅")

        lines.append("-" * 100)

    return "\n".join(lines)


# ============================================================================
# Main Test Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run async evaluation
    broccoli_result, watermelon_result = asyncio.run(run_evaluation_test())

    # Print detailed results
    print_evaluation_result(broccoli_result)
    print_evaluation_result(watermelon_result)

    # Print summary tables
    print(create_test_results_table(broccoli_result, watermelon_result))
    print(create_detailed_summary(broccoli_result, watermelon_result))

    # Save results to JSON
    results_data = {
        "test_timestamp": datetime.now().isoformat(),
        "test_system": "AOC 5-Agent Parallel Evaluation",
        "foods_tested": 2,
        "questions_asked": 0,
        "broccoli": {
            "content_id": broccoli_result.content_id,
            "safety": broccoli_result.safety_classification,
            "final_verdict": broccoli_result.final_verdict,
            "publishable": broccoli_result.publishable,
            "confidence": broccoli_result.confidence_score,
            "execution_time_ms": broccoli_result.total_execution_time_ms,
            "agents": {r.agent_id: r.score for r in broccoli_result.agent_results},
            "conflicts": len(broccoli_result.parallel_conflicts),
        },
        "watermelon": {
            "content_id": watermelon_result.content_id,
            "safety": watermelon_result.safety_classification,
            "final_verdict": watermelon_result.final_verdict,
            "publishable": watermelon_result.publishable,
            "confidence": watermelon_result.confidence_score,
            "execution_time_ms": watermelon_result.total_execution_time_ms,
            "agents": {r.agent_id: r.score for r in watermelon_result.agent_results},
            "conflicts": len(watermelon_result.parallel_conflicts),
        },
    }

    print("\n" + "=" * 100)
    print("RESULTS SAVED")
    print("=" * 100)
    print(json.dumps(results_data, indent=2, ensure_ascii=False))
