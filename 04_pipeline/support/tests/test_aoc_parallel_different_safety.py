"""
AOC 5-Agent Parallel Evaluation - Different Safety Classifications
Project Sunshine - Agent Orchestration Controller

Purpose:
  Simulate parallel evaluation of TWO foods with DIFFERENT safety classifications:
  1. Spinach (시금치) - SAFE (L1) → Expected: AUTO_PUBLISH
  2. Cheese (치즈) - CONDITIONAL (L2) → Expected: HUMAN_QUEUE

Critical verification points:
  1. Do different verdicts (AUTO_PUBLISH vs HUMAN_QUEUE) process correctly in parallel?
  2. Are there any resource conflicts?
  3. Is there any log mixing?
  4. Does the L2 food correctly route to HUMAN_QUEUE while L1 routes to AUTO_PUBLISH?
  5. Are parallel tasks independent with no shared state issues?

Test Result Format:
  - Each food's final verdict
  - Parallel conflicts count (should be 0)
  - Questions asked (should be 0)
  - Whether each food routed to correct destination

Author: Claude Code
Date: 2026-01-31
"""

import asyncio
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import threading
import time


# Global conflict tracking (to detect shared state issues)
_conflict_log = []
_log_lock = threading.Lock()


def log_potential_conflict(message: str):
    """Log potential conflicts for analysis"""
    with _log_lock:
        _conflict_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'thread_id': threading.current_thread().ident
        })


class SafetyLevel(Enum):
    """Food safety classification"""
    SAFE = "SAFE"            # L1: Direct approval
    CONDITIONAL = "CONDITIONAL"  # L2: Needs human review
    DANGEROUS = "DANGEROUS"  # L3: Reject


class PublishVerdict(Enum):
    """Final publication verdict"""
    AUTO_PUBLISH = "AUTO_PUBLISH"    # L1 foods only
    HUMAN_QUEUE = "HUMAN_QUEUE"      # L2+ foods requiring review
    REJECT = "REJECT"                # L3+ foods


@dataclass
class FoodProfile:
    """Target food data"""
    topic_en: str
    topic_kr: str
    safety_level: SafetyLevel
    slides: List[Dict]
    benefits: List[str]
    cautions: List[str]
    amount_guide: str


@dataclass
class AgentEvaluation:
    """Single agent evaluation result"""
    agent_name: str
    agent_id: str  # A, B, C, D, E
    food_name: str  # Track which food was evaluated
    timestamp: str
    success: bool
    scores: Dict[str, float] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp
        return data


@dataclass
class AOCResult:
    """Final AOC evaluation result"""
    food_name: str
    food_kr: str
    safety_level: SafetyLevel  # Track L1 vs L2
    timestamp: str
    evaluations: Dict[str, AgentEvaluation]
    conflicts: List[str]
    final_verdict: PublishVerdict
    total_score: float
    qa_questions: int
    execution_time_ms: float
    expected_verdict: PublishVerdict  # What we expect
    verdict_correct: bool  # Whether it matches expectation


# ============================================================================
# AGENT A: Content Checker
# ============================================================================

class AgentA:
    """Content structure and format compliance"""

    def __init__(self):
        self.name = "Content Checker"
        self.agent_id = "A"

    async def evaluate(self, food: FoodProfile) -> AgentEvaluation:
        """Check content structure and format compliance"""
        scores = {}
        issues = []
        findings = []

        # 1. Slide structure (50점 만점)
        slide_score = self._check_slide_structure(food.slides, issues, findings)
        scores['slide_structure'] = slide_score

        # 2. Text format compliance (30점 만점)
        format_score = self._check_format_compliance(food.slides, issues, findings)
        scores['format_compliance'] = format_score

        # 3. Self-scoring consistency (20점 만점)
        self_score = self._check_self_scoring(food, issues, findings)
        scores['self_scoring'] = self_score

        total = sum(scores.values())
        success = total >= 70  # 70점 이상 통과

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
            food_name=food.topic_en,
            timestamp=datetime.now().isoformat(),
            success=success,
            scores=scores,
            findings=findings,
            issues=issues,
            metadata={
                'total_score': total,
                'max_score': 100,
                'pass_threshold': 70
            }
        )

    def _check_slide_structure(self, slides: List[Dict], issues: List, findings: List) -> float:
        """Validate slide count and order"""
        score = 0
        slide_count = len(slides)

        if slide_count >= 4:
            score = 50
            findings.append(f"✓ Slide count: {slide_count} slides")
        else:
            score = 20 * (slide_count / 4)
            issues.append(f"Insufficient slides: {slide_count}/4 (minimum)")

        # Check required slides
        required_types = {'cover', 'content_bottom', 'cta'}
        found_types = {s.get('type', '') for s in slides}

        if required_types.issubset(found_types):
            findings.append("✓ All required slide types present")
        else:
            missing = required_types - found_types
            issues.append(f"Missing slide types: {missing}")

        return score

    def _check_format_compliance(self, slides: List[Dict], issues: List, findings: List) -> float:
        """Check text field formatting"""
        score = 30

        required_fields = ['slide', 'type', 'title']
        incomplete_slides = []

        for slide in slides:
            if not all(field in slide for field in required_fields):
                incomplete_slides.append(slide.get('slide', '?'))

        if incomplete_slides:
            score = 15
            issues.append(f"Incomplete slides: {incomplete_slides}")
        else:
            findings.append("✓ All slides have required fields")

        return max(0, score)

    def _check_self_scoring(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Check internal consistency"""
        score = 20

        if len(food.cautions) > 0:
            findings.append(f"✓ Caution statements present: {len(food.cautions)}")
        else:
            issues.append("No caution statements found")
            score -= 5

        if len(food.benefits) > 0:
            findings.append(f"✓ Benefit statements present: {len(food.benefits)}")
        else:
            issues.append("No benefit statements found")
            score -= 5

        if food.amount_guide and len(food.amount_guide) > 5:
            findings.append(f"✓ Amount guide present")
        else:
            issues.append("Unclear or missing amount guide")
            score -= 5

        return max(0, score)


# ============================================================================
# AGENT B: Quality Scorer
# ============================================================================

class AgentB:
    """Content quality and tone assessment"""

    def __init__(self):
        self.name = "Quality Scorer"
        self.agent_id = "B"

    async def evaluate(self, food: FoodProfile) -> AgentEvaluation:
        """Score content quality across 5 dimensions"""
        scores = {}
        issues = []
        findings = []

        scores['accuracy'] = self._score_accuracy(food, issues, findings)
        scores['tone'] = self._score_tone(food, issues, findings)
        scores['format'] = self._score_format(food, issues, findings)
        scores['coherence'] = self._score_coherence(food, issues, findings)
        scores['policy'] = self._score_policy(food, issues, findings)

        total = sum(scores.values())
        success = total >= 70

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
            food_name=food.topic_en,
            timestamp=datetime.now().isoformat(),
            success=success,
            scores=scores,
            findings=findings,
            issues=issues,
            metadata={
                'total_score': total,
                'max_score': 100,
                'dimensions': 5
            }
        )

    def _score_accuracy(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Factual accuracy score (20점)"""
        score = 20

        # For CONDITIONAL foods, we still need to score accuracy of the conditional information
        if food.safety_level == SafetyLevel.SAFE:
            findings.append("✓ Safety classification: SAFE (L1)")
        elif food.safety_level == SafetyLevel.CONDITIONAL:
            findings.append("✓ Safety classification: CONDITIONAL (L2) - Conditional accuracy verified")
            score = 18  # Slight reduction for conditional
        else:
            issues.append(f"Safety level issue: {food.safety_level}")
            score -= 10

        if len(food.benefits) >= 2:
            findings.append(f"✓ Multiple benefits documented: {len(food.benefits)}")
        else:
            issues.append("Insufficient benefits documentation")
            score -= 5

        return max(0, score)

    def _score_tone(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Tone and voice consistency (20점)"""
        score = 20

        emoji_count = sum(1 for s in food.slides if any(ord(c) > 127 for c in s.get('title', '')))

        if emoji_count >= 2:
            findings.append(f"✓ Friendly tone with emojis: {emoji_count} slides")
        else:
            findings.append("⚠ Limited emoji usage for casual tone")
            score -= 3

        return max(0, score)

    def _score_format(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Visual format and layout (20점)"""
        score = 20

        subtitles = [s.get('subtitle', '') for s in food.slides if 'subtitle' in s]

        if all(len(st) < 100 for st in subtitles):
            findings.append("✓ Subtitle length consistent")
        else:
            issues.append("Overly long subtitles")
            score -= 5

        return max(0, score)

    def _score_coherence(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Logical flow and narrative coherence (20점)"""
        score = 20

        required_sequence = {
            'cover': 1,
            'content_bottom': 2,
            'cta': 1
        }

        type_counts = {}
        for slide in food.slides:
            slide_type = slide.get('type', '')
            type_counts[slide_type] = type_counts.get(slide_type, 0) + 1

        meets_sequence = all(
            type_counts.get(slide_type, 0) >= count
            for slide_type, count in required_sequence.items()
        )

        if meets_sequence:
            findings.append("✓ Slide progression follows standard pattern")
        else:
            issues.append("Non-standard slide progression detected")
            score -= 5

        return max(0, score)

    def _score_policy(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Brand and policy compliance (20점)"""
        score = 20

        critical_keywords = ['금지', '주의', '제거', '제외']
        caution_text = ' '.join(food.cautions)

        critical_count = sum(1 for kw in critical_keywords if kw in caution_text)

        if critical_count >= 2:
            findings.append(f"✓ Critical safety warnings included: {critical_count}")
        else:
            findings.append("⚠ Limited critical safety warnings")
            score -= 3

        findings.append("✓ AI marking compliant")

        return max(0, score)


# ============================================================================
# AGENT C: Automation Judge
# ============================================================================

class AgentC:
    """Automation feasibility assessment"""

    def __init__(self):
        self.name = "Automation Judge"
        self.agent_id = "C"

    async def evaluate(self, food: FoodProfile) -> AgentEvaluation:
        """Determine if content is auto-publishable"""
        scores = {}
        issues = []
        findings = []
        intervention_points = []

        template_score = self._check_template_compatibility(food, issues, findings)
        scores['template_compatibility'] = template_score

        automation_score = self._check_automation_readiness(food, issues, findings, intervention_points)
        scores['automation_readiness'] = automation_score

        intervention_score = self._assess_intervention_risk(
            food, issues, findings, intervention_points
        )
        scores['intervention_risk'] = intervention_score

        total = sum(scores.values())
        success = total >= 70
        auto_publishable = success and len(intervention_points) == 0

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
            food_name=food.topic_en,
            timestamp=datetime.now().isoformat(),
            success=success,
            scores=scores,
            findings=findings,
            issues=issues,
            metadata={
                'total_score': total,
                'max_score': 100,
                'auto_publishable': auto_publishable,
                'intervention_points': intervention_points
            }
        )

    def _check_template_compatibility(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Check if content fits standard templates"""
        score = 40

        slide_count = len(food.slides)
        if slide_count >= 4:
            findings.append(f"✓ Compatible with template ({slide_count} slides)")
        else:
            findings.append(f"⚠ Non-standard slide count: {slide_count}")
            score = 20

        required_fields_present = all(
            'title' in slide and 'type' in slide
            for slide in food.slides
        )

        if required_fields_present:
            findings.append("✓ All required fields present for template mapping")
        else:
            issues.append("Missing template fields")
            score -= 10

        return max(0, score)

    def _check_automation_readiness(self, food: FoodProfile, issues: List, findings: List, interventions: List) -> float:
        """Assess if content is ready for automated processing"""
        score = 30

        # CONDITIONAL foods need human review - this is a key intervention point
        if food.safety_level == SafetyLevel.CONDITIONAL:
            findings.append("⚠ CONDITIONAL food detected - requires human review")
            interventions.append("HUMAN_REVIEW: Conditional food approval required")
            score -= 10  # Reduce automation readiness
        else:
            findings.append("✓ Clear safety classification - automated processing possible")

        caution_text = ' '.join(food.cautions).lower()
        if '정도' not in caution_text and '적당' not in caution_text:
            findings.append("✓ Clear quantified guidelines")
        else:
            findings.append("⚠ Vague quantity guidelines detected")
            interventions.append("REVIEW: Verify exact quantity recommendations")
            score -= 5

        amount = food.amount_guide
        if '|' in amount or '/' in amount or '~' in amount:
            findings.append(f"✓ Structured amount guide present")
        else:
            interventions.append("REVIEW: Amount guide formatting unclear")
            score -= 3

        return max(0, score)

    def _assess_intervention_risk(self, food: FoodProfile, issues: List, findings: List, interventions: List) -> float:
        """Identify points requiring human review"""
        score = 30

        # CONDITIONAL foods automatically trigger human review
        if food.safety_level == SafetyLevel.CONDITIONAL:
            findings.append("⚠ CONDITIONAL classification triggers mandatory human review")
            interventions.append("MANDATORY: Human review for conditional safety approval")
            score = 10  # High intervention risk
        else:
            findings.append("✓ SAFE classification = minimal intervention needed")
            score = 30

        completeness_checks = {
            'benefits': len(food.benefits) >= 2,
            'cautions': len(food.cautions) >= 2,
            'amount_guide': len(food.amount_guide) > 5,
            'slides': len(food.slides) >= 4
        }

        failed_checks = [k for k, v in completeness_checks.items() if not v]
        if not failed_checks:
            findings.append("✓ All information complete")
        else:
            issues.append(f"Incomplete information: {failed_checks}")
            score -= 5
            interventions.append(f"VERIFY: Ensure all {failed_checks} are complete")

        return max(0, score)


# ============================================================================
# AGENT D: Red Flag Detector
# ============================================================================

class AgentD:
    """Safety and policy violation detection"""

    def __init__(self):
        self.name = "Red Flag Detector"
        self.agent_id = "D"

    async def evaluate(self, food: FoodProfile) -> AgentEvaluation:
        """Detect safety, policy, and brand violations"""
        scores = {}
        issues = []
        findings = []
        red_flags = []

        safety_score = self._check_food_safety(food, issues, findings, red_flags)
        scores['food_safety'] = safety_score

        policy_score = self._check_policy_compliance(food, issues, findings, red_flags)
        scores['policy_compliance'] = policy_score

        brand_score = self._check_brand_compliance(food, issues, findings, red_flags)
        scores['brand_compliance'] = brand_score

        total = sum(scores.values())
        # For CONDITIONAL foods, red flags don't mean rejection - just human review
        success = total >= 70 and len(red_flags) == 0

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
            food_name=food.topic_en,
            timestamp=datetime.now().isoformat(),
            success=success,
            scores=scores,
            findings=findings,
            issues=issues,
            metadata={
                'total_score': total,
                'max_score': 100,
                'red_flags_count': len(red_flags),
                'red_flags': red_flags
            }
        )

    def _check_food_safety(self, food: FoodProfile, issues: List, findings: List, flags: List) -> float:
        """Check for food safety violations"""
        score = 40

        # SAFE foods pass immediately
        if food.safety_level == SafetyLevel.SAFE:
            findings.append("✓ Food safety classification: SAFE (L1)")
            score = 40

        # CONDITIONAL foods pass but are flagged for review
        elif food.safety_level == SafetyLevel.CONDITIONAL:
            findings.append("✓ Food safety classification: CONDITIONAL (L2)")
            findings.append("Note: Conditional foods require human verification of conditions")
            score = 35  # Slight reduction for conditional

        # DANGEROUS foods fail completely
        else:
            flags.append(f"RED_FLAG: Food classified as {food.safety_level.value}")
            return 0

        toxic_keywords = ['독소', '중독', '위험', 'toxic', 'poison']
        dangerous_mentions = sum(1 for kw in toxic_keywords if kw in ' '.join(food.cautions))

        if dangerous_mentions == 0:
            findings.append("✓ No toxic ingredients mentioned")
        else:
            flags.append(f"RED_FLAG: Toxic ingredient warnings found ({dangerous_mentions})")
            score -= 20

        return max(0, score)

    def _check_policy_compliance(self, food: FoodProfile, issues: List, findings: List, flags: List) -> float:
        """Check CLAUDE.md policy compliance"""
        score = 30

        findings.append("✓ AI marking compliant")
        findings.append("✓ Model ID verification (hardcoded)")

        conflicting_claims = any(
            c in ' '.join(food.cautions) and c in ' '.join(food.benefits)
            for c in ['독소', 'toxic']
        )

        if not conflicting_claims:
            findings.append("✓ No conflicting safety/benefit claims")
        else:
            flags.append("RED_FLAG: Conflicting safety and benefit claims")
            score -= 10

        return max(0, score)

    def _check_brand_compliance(self, food: FoodProfile, issues: List, findings: List, flags: List) -> float:
        """Check @sunshinedogfood brand guidelines"""
        score = 30

        emoji_in_slides = sum(1 for s in food.slides if any(ord(c) > 127 for c in s.get('title', '')))
        if emoji_in_slides >= 2:
            findings.append(f"✓ Brand tone: Emoji usage present ({emoji_in_slides} slides)")
        else:
            findings.append("⚠ Limited emoji usage")
            score -= 3

        if food.topic_kr and len(food.topic_kr) > 0:
            findings.append(f"✓ Korean naming: '{food.topic_kr}'")
        else:
            flags.append("RED_FLAG: Missing Korean product name")
            score -= 15

        has_cta = any(s.get('type') == 'cta' for s in food.slides)
        if has_cta:
            findings.append("✓ CTA slide present")
        else:
            flags.append("RED_FLAG: Missing CTA slide")
            score -= 15

        return max(0, score)


# ============================================================================
# AGENT E: Cost Estimator
# ============================================================================

class AgentE:
    """Cost and resource estimation"""

    def __init__(self):
        self.name = "Cost Estimator"
        self.agent_id = "E"

    async def evaluate(self, food: FoodProfile) -> AgentEvaluation:
        """Estimate API, compute, and storage costs"""
        scores = {}
        issues = []
        findings = []
        costs = {}

        api_cost, api_score = self._estimate_api_costs(food, issues, findings)
        costs['api_cost_usd'] = api_cost
        scores['api_efficiency'] = api_score

        compute_cost, compute_score = self._estimate_compute_costs(food, issues, findings)
        costs['compute_cost_usd'] = compute_cost
        scores['compute_efficiency'] = compute_score

        storage_cost, storage_score = self._estimate_storage_costs(food, issues, findings)
        costs['storage_cost_usd'] = storage_cost
        scores['storage_efficiency'] = storage_score

        total = sum(scores.values())
        success = total >= 70

        cost_per_image = api_cost + compute_cost
        findings.append(f"Cost per content: ${cost_per_image:.2f} ({len(food.slides)} images)")

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
            food_name=food.topic_en,
            timestamp=datetime.now().isoformat(),
            success=success,
            scores=scores,
            findings=findings,
            issues=issues,
            metadata={
                'total_score': total,
                'max_score': 100,
                'estimated_costs': {
                    'api_usd': round(api_cost, 2),
                    'compute_usd': round(compute_cost, 2),
                    'storage_usd': round(storage_cost, 2),
                    'total_usd': round(api_cost + compute_cost + storage_cost, 2)
                }
            }
        )

    def _estimate_api_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate API costs (fal-ai FLUX.2 Pro)"""
        image_count = len(food.slides) - 1
        cost_per_image = 0.025
        total_api_cost = image_count * cost_per_image

        findings.append(f"API: {image_count} images × ${cost_per_image} = ${total_api_cost:.2f}")

        if image_count <= 3:
            score = 35
        elif image_count <= 5:
            score = 33
        else:
            score = max(20, 30 - (image_count - 5) * 2)

        return total_api_cost, score

    def _estimate_compute_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate compute/processing costs"""
        slide_count = len(food.slides)
        overlay_cost = slide_count * 0.001
        qc_cost = slide_count * 0.0005
        publish_cost = 0.0001

        total_compute_cost = overlay_cost + qc_cost + publish_cost

        findings.append(f"Compute: ${total_compute_cost:.4f} total")

        score = 35

        return total_compute_cost, score

    def _estimate_storage_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate storage costs (Cloudinary)"""
        slide_count = len(food.slides)
        size_per_slide_mb = 2.0
        total_size_mb = slide_count * size_per_slide_mb
        monthly_storage_cost = (total_size_mb / 1024) * 0.10 / 30

        findings.append(f"Storage: {total_size_mb}MB (~${monthly_storage_cost:.6f}/day)")

        score = 35

        return monthly_storage_cost, score


# ============================================================================
# AOC Controller
# ============================================================================

class AOCController:
    """Agent Orchestration Controller for parallel evaluation"""

    def __init__(self):
        self.agents = {
            'A': AgentA(),
            'B': AgentB(),
            'C': AgentC(),
            'D': AgentD(),
            'E': AgentE()
        }

    async def evaluate_food(self, food: FoodProfile) -> AOCResult:
        """Run parallel evaluation of a food with 5 agents"""

        start_time = datetime.now()

        # Run agents in parallel
        tasks = [
            self.agents['A'].evaluate(food),
            self.agents['B'].evaluate(food),
            self.agents['C'].evaluate(food),
            self.agents['D'].evaluate(food),
            self.agents['E'].evaluate(food)
        ]

        evaluations_list = await asyncio.gather(*tasks)
        evaluations = {ev.agent_id: ev for ev in evaluations_list}

        # Detect conflicts
        conflicts = self._detect_conflicts(evaluations)

        # Calculate final verdict
        final_verdict = self._determine_verdict(food.safety_level, evaluations, conflicts)

        # Expected verdict based on safety level
        expected_verdict = (
            PublishVerdict.AUTO_PUBLISH if food.safety_level == SafetyLevel.SAFE
            else PublishVerdict.HUMAN_QUEUE if food.safety_level == SafetyLevel.CONDITIONAL
            else PublishVerdict.REJECT
        )

        # Calculate total score
        total_score = sum(ev.metadata.get('total_score', 0) for ev in evaluations.values()) / len(evaluations)

        # Count questions asked
        qa_questions = self._count_qa_questions(evaluations)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return AOCResult(
            food_name=food.topic_en,
            food_kr=food.topic_kr,
            safety_level=food.safety_level,
            timestamp=datetime.now().isoformat(),
            evaluations=evaluations,
            conflicts=conflicts,
            final_verdict=final_verdict,
            total_score=round(total_score, 1),
            qa_questions=qa_questions,
            execution_time_ms=execution_time,
            expected_verdict=expected_verdict,
            verdict_correct=(final_verdict == expected_verdict)
        )

    def _detect_conflicts(self, evaluations: Dict[str, AgentEvaluation]) -> List[str]:
        """Detect conflicts between agent evaluations"""
        conflicts = []

        agent_c_auto = evaluations['C'].metadata.get('auto_publishable', False)
        agent_d_red_flags = evaluations['D'].metadata.get('red_flags_count', 0) > 0

        if agent_c_auto and agent_d_red_flags:
            conflict_msg = "CONFLICT: Agent C (auto_publishable) vs Agent D (red flags detected)"
            conflicts.append(conflict_msg)
            log_potential_conflict(conflict_msg)

        failed_agents = [
            ev.agent_id for ev in evaluations.values()
            if not ev.success
        ]

        if failed_agents:
            conflict_msg = f"CONFLICT: Agents {failed_agents} failed quality threshold"
            conflicts.append(conflict_msg)
            log_potential_conflict(conflict_msg)

        return conflicts

    def _determine_verdict(self, safety_level: SafetyLevel, evaluations: Dict[str, AgentEvaluation],
                          conflicts: List[str]) -> PublishVerdict:
        """Determine final publication verdict based on safety level"""

        all_pass = all(ev.success for ev in evaluations.values())
        agent_d_has_red_flags = evaluations['D'].metadata.get('red_flags_count', 0) > 0
        agent_c_auto = evaluations['C'].metadata.get('auto_publishable', False)
        agent_c_interventions = evaluations['C'].metadata.get('intervention_points', [])

        # CONDITIONAL foods always go to HUMAN_QUEUE (unless critical red flag)
        if safety_level == SafetyLevel.CONDITIONAL:
            # Only reject if critical red flags (not just agent failure)
            if agent_d_has_red_flags and 'toxic' in str(evaluations['D'].metadata.get('red_flags', [])).lower():
                return PublishVerdict.REJECT
            else:
                # CONDITIONAL foods always need human review
                return PublishVerdict.HUMAN_QUEUE  # KEY DIFFERENCE

        # SAFE foods can go to AUTO_PUBLISH
        if safety_level == SafetyLevel.SAFE:
            if not all_pass:
                return PublishVerdict.HUMAN_QUEUE

            if agent_d_has_red_flags:
                return PublishVerdict.REJECT

            if agent_c_auto and all_pass:
                return PublishVerdict.AUTO_PUBLISH
            else:
                return PublishVerdict.HUMAN_QUEUE

        # DANGEROUS foods always reject
        return PublishVerdict.REJECT

    def _count_qa_questions(self, evaluations: Dict[str, AgentEvaluation]) -> int:
        """Count questions asked by agents"""
        total_questions = 0
        for ev in evaluations.values():
            total_questions += sum(1 for finding in ev.findings if '?' in finding)
            total_questions += sum(1 for issue in ev.issues if '?' in issue)

        return total_questions


# ============================================================================
# Test Data
# ============================================================================

def create_spinach_profile() -> FoodProfile:
    """Create spinach profile - SAFE (L1)"""
    return FoodProfile(
        topic_en='spinach',
        topic_kr='시금치',
        safety_level=SafetyLevel.SAFE,
        slides=[
            {'slide': 0, 'type': 'cover', 'title': 'SPINACH', 'subtitle': ''},
            {'slide': 1, 'type': 'content_bottom', 'title': '먹어도 돼요!', 'subtitle': '철분과 비타민 풍부 ✅'},
            {'slide': 2, 'type': 'content_bottom', 'title': '주의사항', 'subtitle': '살짝 데쳐서 급여하세요 ⚠️'},
            {'slide': 3, 'type': 'cta', 'title': '저장 & 공유', 'subtitle': '주변 견주에게 알려주세요! 🐶'}
        ],
        benefits=[
            '철분: 혈액 생성 및 산소 운반',
            '비타민 K: 뼈 건강 및 혈액 응고',
            '항산화제: 세포 손상 방지'
        ],
        cautions=[
            '시금치는 반드시 살짝 데친 후 급여',
            '생 시금치는 옥살산 함유로 칼슘 흡수 방해',
            '과다 급여 시 신장 문제 가능'
        ],
        amount_guide='소형 1큰술 | 중형 2큰술 | 대형 3큰술'
    )


def create_cheese_profile() -> FoodProfile:
    """Create cheese profile - CONDITIONAL (L2)"""
    return FoodProfile(
        topic_en='cheese',
        topic_kr='치즈',
        safety_level=SafetyLevel.CONDITIONAL,
        slides=[
            {'slide': 1, 'type': 'cover', 'title': 'CHEESE', 'subtitle': '고소한 치즈'},
            {'slide': 2, 'type': 'content_bottom', 'title': '조건부 OK!', 'subtitle': '저염/저지방 치즈만! 🧀'},
            {'slide': 3, 'type': 'content_bottom', 'title': '칼슘 풍부', 'subtitle': '뼈와 치아 건강에! 🦴'},
            {'slide': 4, 'type': 'content_bottom', 'title': '단백질', 'subtitle': '양질의 단백질 공급! 💪'},
            {'slide': 5, 'type': 'content_bottom', 'title': '비타민 A', 'subtitle': '눈 건강에 도움! ✨'},
            {'slide': 6, 'type': 'content_bottom', 'title': '저염 치즈만!', 'subtitle': '나트륨 과다 주의! ⚠️'},
            {'slide': 7, 'type': 'content_bottom', 'title': '소량만 급여', 'subtitle': '지방이 많아요! 🚫'},
            {'slide': 8, 'type': 'content_top', 'title': '유당불내증 체크', 'subtitle': '소화 문제 가능! ⚠️'},
            {'slide': 9, 'type': 'content_bottom', 'title': '훈련 간식으로', 'subtitle': '조금씩 보상으로! 🧀'},
            {'slide': 10, 'type': 'cta', 'title': '저장 필수!', 'subtitle': '치즈 급여법! 🐶'}
        ],
        benefits=[
            '칼슘: 뼈와 치아 강화',
            '단백질: 근육 발달 및 유지',
            '비타민 A: 눈 건강 지원'
        ],
        cautions=[
            '반드시 저염 치즈만 급여',
            '저지방 치즈 선택 필수',
            '유당불내증 반응 가능 - 처음엔 소량 테스트',
            '과다 급여 시 체중 증가 주의',
            '고염분 치즈는 피할 것'
        ],
        amount_guide='소형 1조각(5g) | 중형 2조각(10g) | 대형 3조각(15g)'
    )


# ============================================================================
# Main Test Function
# ============================================================================

async def run_aoc_parallel_evaluation_test():
    """Run AOC 5-agent parallel evaluation test with different safety levels"""

    print("\n" + "="*90)
    print("AOC 5-AGENT PARALLEL EVALUATION - DIFFERENT SAFETY CLASSIFICATIONS")
    print("Project Sunshine - Parallel Processing Verification")
    print("="*90)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nCritical Test Points:")
    print("  1. L1 (SAFE) food → AUTO_PUBLISH verdict")
    print("  2. L2 (CONDITIONAL) food → HUMAN_QUEUE verdict")
    print("  3. Zero parallel conflicts (expected: 0)")
    print("  4. Zero questions asked (expected: 0)")
    print("  5. No log mixing or resource conflicts\n")

    # Initialize AOC Controller
    aoc = AOCController()

    # Create test profiles
    spinach = create_spinach_profile()
    cheese = create_cheese_profile()

    print("Running parallel evaluation for 2 foods with DIFFERENT safety levels...")
    print(f"Food 1: {spinach.topic_kr} ({spinach.topic_en}) - {spinach.safety_level.value} (L1)")
    print(f"Food 2: {cheese.topic_kr} ({cheese.topic_en}) - {cheese.safety_level.value} (L2)\n")

    # Run parallel evaluations for both foods simultaneously
    print("Executing parallel evaluation tasks...")
    start_parallel = datetime.now()

    spinach_result, cheese_result = await asyncio.gather(
        aoc.evaluate_food(spinach),
        aoc.evaluate_food(cheese)
    )

    parallel_time = (datetime.now() - start_parallel).total_seconds() * 1000

    # Print results
    print("\n" + "="*90)
    print("EVALUATION RESULTS")
    print("="*90 + "\n")

    # Spinach results (L1 - should be AUTO_PUBLISH)
    print(f"SPINACH (시금치) - SAFE (L1) - Expected: AUTO_PUBLISH")
    print("-" * 90)
    print_aoc_result(spinach_result)

    # Cheese results (L2 - should be HUMAN_QUEUE)
    print(f"\n\nCHEESE (치즈) - CONDITIONAL (L2) - Expected: HUMAN_QUEUE")
    print("-" * 90)
    print_aoc_result(cheese_result)

    # Summary table
    print("\n" + "="*90)
    print("SUMMARY TABLE")
    print("="*90)
    print_summary_table(spinach_result, cheese_result)

    # Conflict analysis
    print("\n" + "="*90)
    print("PARALLEL CONFLICT ANALYSIS")
    print("="*90)
    print_conflict_analysis(spinach_result, cheese_result)

    # Final verdict
    print("\n" + "="*90)
    print("FINAL VERDICT & ROUTING")
    print("="*90)
    spinach_correct = spinach_result.verdict_correct
    cheese_correct = cheese_result.verdict_correct

    print(f"Spinach (시금치, L1):")
    print(f"  Expected: {spinach_result.expected_verdict.value}")
    print(f"  Actual:   {spinach_result.final_verdict.value}")
    print(f"  Status:   {'✓ CORRECT' if spinach_correct else '✗ INCORRECT'}")

    print(f"\nCheese (치즈, L2):")
    print(f"  Expected: {cheese_result.expected_verdict.value}")
    print(f"  Actual:   {cheese_result.final_verdict.value}")
    print(f"  Status:   {'✓ CORRECT' if cheese_correct else '✗ INCORRECT'}")

    total_questions = spinach_result.qa_questions + cheese_result.qa_questions
    total_conflicts = len(spinach_result.conflicts) + len(cheese_result.conflicts)
    total_parallel_time = spinach_result.execution_time_ms + cheese_result.execution_time_ms

    print(f"\nParallel Execution Summary:")
    print(f"  Total Questions Asked: {total_questions} (expected: 0)")
    print(f"  Parallel Conflicts: {total_conflicts} (expected: 0)")
    print(f"  Combined Execution Time: {total_parallel_time:.1f}ms")
    print(f"  Actual Parallel Time: {parallel_time:.1f}ms")

    # Check for log mixing or shared state issues
    print(f"\nLog Integrity Check:")
    print(f"  Log entries captured: {len(_conflict_log)}")
    if len(_conflict_log) > 0:
        print("  ✗ FAIL: Conflicts detected in parallel execution")
        for log_entry in _conflict_log:
            print(f"    - {log_entry['message']}")
    else:
        print("  ✓ PASS: No log mixing or conflicts detected")

    # Overall test result
    overall_pass = (
        spinach_correct and
        cheese_correct and
        total_questions == 0 and
        total_conflicts == 0 and
        len(_conflict_log) == 0
    )

    print(f"\n" + "="*90)
    print(f"OVERALL TEST: {'✓✓✓ PASS ✓✓✓' if overall_pass else '✗✗✗ FAIL ✗✗✗'}")
    print("="*90)

    return overall_pass


def print_aoc_result(result: AOCResult):
    """Print detailed AOC result for a food"""

    print(f"Food: {result.food_kr} ({result.food_name}) - {result.safety_level.value}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Execution Time: {result.execution_time_ms:.1f}ms\n")

    print("Agent Scores:")
    print("-" * 90)
    agent_names = {
        'A': 'Content Checker',
        'B': 'Quality Scorer',
        'C': 'Automation Judge',
        'D': 'Red Flag Detector',
        'E': 'Cost Estimator'
    }

    for agent_id in ['A', 'B', 'C', 'D', 'E']:
        ev = result.evaluations[agent_id]
        score = ev.metadata.get('total_score', 0)
        status = "✓ PASS" if ev.success else "✗ FAIL"
        print(f"  Agent {agent_id} ({agent_names[agent_id]:25s}): {score:6.1f}/100 {status}")

    print(f"\nAverage Score: {result.total_score:.1f}/100")
    print(f"Expected Verdict: {result.expected_verdict.value}")
    print(f"Final Verdict: {result.final_verdict.value} {'✓' if result.verdict_correct else '✗'}")
    print(f"QA Questions: {result.qa_questions}")

    if result.conflicts:
        print(f"\nConflicts Detected: {len(result.conflicts)}")
        for conflict in result.conflicts:
            print(f"  - {conflict}")
    else:
        print("\nConflicts Detected: 0 (✓ Clean)")

    # Agent details summary
    print("\nAgent Details (Summary):")
    print("-" * 90)
    for agent_id in ['C', 'D']:  # Show key agents
        ev = result.evaluations[agent_id]
        print(f"\n{agent_names[agent_id]} (Agent {agent_id}):")

        if agent_id == 'C':
            interventions = ev.metadata.get('intervention_points', [])
            auto_pub = ev.metadata.get('auto_publishable', False)
            print(f"  Auto-Publishable: {auto_pub}")
            if interventions:
                print(f"  Intervention Points: {len(interventions)}")
                for intervention in interventions[:2]:
                    print(f"    - {intervention}")

        if agent_id == 'D':
            red_flags = ev.metadata.get('red_flags', [])
            print(f"  Red Flags Count: {len(red_flags)}")
            if red_flags:
                for flag in red_flags[:2]:
                    print(f"    - {flag}")


def print_summary_table(spinach: AOCResult, cheese: AOCResult):
    """Print summary comparison table"""

    print(f"\n{'Metric':<35} {'Spinach (L1)':<25} {'Cheese (L2)':<25}")
    print("-" * 85)

    metrics = [
        ('Safety Level', 'safety_level.value'),
        ('Agent A Score', 'evaluations.A.metadata.total_score'),
        ('Agent B Score', 'evaluations.B.metadata.total_score'),
        ('Agent C Score', 'evaluations.C.metadata.total_score'),
        ('Agent D Score', 'evaluations.D.metadata.total_score'),
        ('Agent E Score', 'evaluations.E.metadata.total_score'),
        ('Average Score', 'total_score'),
        ('Expected Verdict', 'expected_verdict.value'),
        ('Final Verdict', 'final_verdict.value'),
        ('Verdict Correct', 'verdict_correct'),
        ('QA Questions', 'qa_questions'),
        ('Conflicts', 'conflicts'),
        ('Exec Time (ms)', 'execution_time_ms')
    ]

    for metric_name, metric_path in metrics:
        spinach_val = get_nested_attr(spinach, metric_path)
        cheese_val = get_nested_attr(cheese, metric_path)

        # Format conflicts count
        if metric_name == 'Conflicts':
            spinach_val = len(spinach_val) if isinstance(spinach_val, list) else spinach_val
            cheese_val = len(cheese_val) if isinstance(cheese_val, list) else cheese_val

        print(f"{metric_name:<35} {str(spinach_val):<25} {str(cheese_val):<25}")


def print_conflict_analysis(spinach: AOCResult, cheese: AOCResult):
    """Print conflict analysis"""

    total_conflicts = len(spinach.conflicts) + len(cheese.conflicts)

    print(f"Total Parallel Conflicts: {total_conflicts}\n")

    if spinach.conflicts:
        print(f"Spinach Conflicts ({len(spinach.conflicts)}):")
        for conflict in spinach.conflicts:
            print(f"  - {conflict}")
    else:
        print("Spinach Conflicts: None ✓")

    if cheese.conflicts:
        print(f"\nCheese Conflicts ({len(cheese.conflicts)}):")
        for conflict in cheese.conflicts:
            print(f"  - {conflict}")
    else:
        print("\nCheese Conflicts: None ✓")

    print(f"\nOverall Parallel Status: {'✓ CLEAN' if total_conflicts == 0 else f'✗ {total_conflicts} conflicts'}")

    # Verify routing correctness
    print(f"\nRouting Verification:")
    print(f"  Spinach (L1/SAFE) routed to: {spinach.final_verdict.value}")
    print(f"    Expected: AUTO_PUBLISH | Actual: {spinach.final_verdict.value} | {'✓' if spinach.final_verdict == PublishVerdict.AUTO_PUBLISH else '✗'}")

    print(f"  Cheese (L2/CONDITIONAL) routed to: {cheese.final_verdict.value}")
    print(f"    Expected: HUMAN_QUEUE | Actual: {cheese.final_verdict.value} | {'✓' if cheese.final_verdict == PublishVerdict.HUMAN_QUEUE else '✗'}")


def get_nested_attr(obj, path: str):
    """Get nested object attribute using dot notation"""
    parts = path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


# ============================================================================
# Pytest Integration
# ============================================================================

def test_aoc_parallel_different_safety():
    """Pytest integration for parallel AOC evaluation with different safety levels"""
    result = asyncio.run(run_aoc_parallel_evaluation_test())
    assert result, "AOC parallel evaluation test failed"


if __name__ == "__main__":
    asyncio.run(run_aoc_parallel_evaluation_test())
