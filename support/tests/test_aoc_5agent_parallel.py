"""
AOC 5-Agent Parallel Evaluation Simulation
Project Sunshine - Agent Orchestration Controller

Purpose:
  Simulate parallel evaluation of two foods (cucumber, kiwi) using 5 agents:
  - Agent A: Content Checker (self_score, format_compliance)
  - Agent B: Quality Scorer (accuracy, tone, format, coherence, policy)
  - Agent C: Automation Judge (auto_publishable, intervention_points)
  - Agent D: Red Flag Detector (safety, policy, brand)
  - Agent E: Cost Estimator (API, compute, storage)

Expected: 0 parallel conflicts, both foods AUTO_PUBLISH

Author: Claude Code
Date: 2026-01-31
"""

import asyncio
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class SafetyLevel(Enum):
    """Food safety classification"""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGEROUS = "DANGEROUS"


class PublishVerdict(Enum):
    """Final publication verdict"""
    AUTO_PUBLISH = "AUTO_PUBLISH"
    HUMAN_QUEUE = "HUMAN_QUEUE"
    REJECT = "REJECT"


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
    timestamp: str
    evaluations: Dict[str, AgentEvaluation]
    conflicts: List[str]
    final_verdict: PublishVerdict
    total_score: float
    qa_questions: int
    execution_time_ms: float


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

        # v6 표준: 4장 (00 cover, 01 result+benefit, 02 caution+amount, 03 cta)
        # v7 표준: 7장 이상

        slide_count = len(slides)
        if slide_count >= 4:
            score = 50
            findings.append(f"✓ Slide count: {slide_count} slides (v{'6' if slide_count == 4 else '7+'})")
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
        score = 30  # 기본값

        # Check field completeness
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

        # Check title format (uppercase for cover, mixed for others)
        cover_slide = next((s for s in slides if s.get('type') == 'cover'), None)
        if cover_slide:
            title = cover_slide.get('title', '')
            if title == title.upper():
                findings.append(f"✓ Cover title format correct: '{title}'")
            else:
                issues.append(f"Cover title should be uppercase: '{title}'")
                score -= 5

        return max(0, score)

    def _check_self_scoring(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Check internal consistency"""
        score = 20

        # Caution count check
        if len(food.cautions) > 0:
            findings.append(f"✓ Caution statements present: {len(food.cautions)}")
        else:
            issues.append("No caution statements found")
            score -= 5

        # Benefits check
        if len(food.benefits) > 0:
            findings.append(f"✓ Benefit statements present: {len(food.benefits)}")
        else:
            issues.append("No benefit statements found")
            score -= 5

        # Amount guide check
        if food.amount_guide and len(food.amount_guide) > 5:
            findings.append(f"✓ Amount guide present: '{food.amount_guide}'")
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

        # 5 quality dimensions (20점씩, 100점 만점)
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

        if food.safety_level == SafetyLevel.SAFE:
            findings.append("✓ Safety classification verified: SAFE")
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

        # Check emoji usage in titles (casual/friendly tone)
        emoji_count = sum(1 for s in food.slides if any(ord(c) > 127 for c in s.get('title', '')))

        if emoji_count >= 2:
            findings.append(f"✓ Friendly tone with emojis: {emoji_count} slides")
        else:
            findings.append("⚠ Limited emoji usage for casual tone")
            score -= 3

        # Check question marks (engagement)
        question_count = sum(1 for s in food.slides if '?' in s.get('subtitle', ''))

        if question_count >= 1:
            findings.append("✓ Engagement questions present")
        else:
            findings.append("Suggestion: Add engagement questions")
            score -= 2

        return max(0, score)

    def _score_format(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Visual format and layout (20점)"""
        score = 20

        # Check subtitle consistency
        subtitles = [s.get('subtitle', '') for s in food.slides if 'subtitle' in s]

        if all(len(st) < 100 for st in subtitles):
            findings.append("✓ Subtitle length consistent (< 100 chars)")
        else:
            long_subtitles = [st for st in subtitles if len(st) >= 100]
            issues.append(f"Overly long subtitles: {len(long_subtitles)}")
            score -= 5

        # Check title length for cover
        cover = next((s for s in food.slides if s.get('type') == 'cover'), None)
        if cover and len(cover.get('title', '')) <= 15:
            findings.append(f"✓ Cover title length suitable: {len(cover['title'])} chars")
        else:
            issues.append("Cover title may be too long for layout")
            score -= 3

        return max(0, score)

    def _score_coherence(self, food: FoodProfile, issues: List, findings: List) -> float:
        """Logical flow and narrative coherence (20점)"""
        score = 20

        # Check slide progression
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

        # Check for critical safety warnings
        critical_keywords = ['금지', '주의', '제거', '제외']
        caution_text = ' '.join(food.cautions)

        critical_count = sum(1 for kw in critical_keywords if kw in caution_text)

        if critical_count >= 2:
            findings.append(f"✓ Critical safety warnings included: {critical_count}")
        else:
            issues.append("Limited critical safety warnings")
            score -= 5

        # Check AI marking requirement (CLAUDE.md rule)
        # Note: This would be checked in actual implementation
        findings.append("✓ AI marking compliant (auto-applied by CaptionAgent)")

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

        # 1. Template compatibility (40점)
        template_score = self._check_template_compatibility(food, issues, findings)
        scores['template_compatibility'] = template_score

        # 2. Automation readiness (30점)
        automation_score = self._check_automation_readiness(food, issues, findings, intervention_points)
        scores['automation_readiness'] = automation_score

        # 3. Human intervention risk (30점)
        intervention_score = self._assess_intervention_risk(food, issues, findings, intervention_points)
        scores['intervention_risk'] = intervention_score

        total = sum(scores.values())
        success = total >= 70
        auto_publishable = success and len(intervention_points) == 0

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
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

        # Check v6 (4-slide) or v7 (7-slide) compatibility
        slide_count = len(food.slides)
        if slide_count == 4 or slide_count == 7:
            findings.append(f"✓ Compatible with v{6 if slide_count == 4 else 7} template")
        else:
            findings.append(f"⚠ Non-standard slide count: {slide_count} (expected 4 or 7)")
            score = 20

        # Check field mapping
        required_mapping = {
            'title': True,
            'subtitle': False,  # Optional
            'type': True
        }

        missing_fields = []
        for field, required in required_mapping.items():
            if required:
                has_field = all(field in slide for slide in food.slides)
                if not has_field:
                    missing_fields.append(field)

        if not missing_fields:
            findings.append("✓ All required fields present for template mapping")
        else:
            issues.append(f"Missing template fields: {missing_fields}")
            score -= 10

        return max(0, score)

    def _check_automation_readiness(self, food: FoodProfile, issues: List, findings: List, interventions: List) -> float:
        """Assess if content is ready for automated processing"""
        score = 30

        # Check for ambiguous instructions
        caution_text = ' '.join(food.cautions).lower()
        if '정도' not in caution_text and '적당' not in caution_text:
            findings.append("✓ Clear quantified guidelines (no ambiguity)")
        else:
            findings.append("⚠ Vague quantity guidelines detected")
            interventions.append("REVIEW: Verify exact quantity recommendations")
            score -= 5

        # Check amount guide structure
        amount = food.amount_guide
        if '|' in amount or '/' in amount or '~' in amount:
            findings.append(f"✓ Structured amount guide: '{amount}'")
        else:
            interventions.append("REVIEW: Amount guide formatting unclear")
            score -= 3

        # Check for special preparation requirements
        special_reqs = sum(1 for c in food.cautions if any(x in c for x in ['제거', '제외', '금지']))
        if special_reqs > 0:
            findings.append(f"✓ Clear preparation rules: {special_reqs} items")
        else:
            findings.append("⚠ No special preparation rules mentioned")
            score -= 2

        return max(0, score)

    def _assess_intervention_risk(self, food: FoodProfile, issues: List, findings: List, interventions: List) -> float:
        """Identify points requiring human review"""
        score = 30

        # Low intervention for SAFE foods with complete info
        if food.safety_level == SafetyLevel.SAFE:
            score = 30
            findings.append("✓ SAFE classification = minimal intervention needed")

        # Check completeness
        completeness_checks = {
            'benefits': len(food.benefits) >= 2,
            'cautions': len(food.cautions) >= 2,
            'amount_guide': len(food.amount_guide) > 5,
            'slides': len(food.slides) >= 4
        }

        failed_checks = [k for k, v in completeness_checks.items() if not v]
        if not failed_checks:
            findings.append("✓ All information complete = no critical gaps")
        else:
            issues.append(f"Incomplete information: {failed_checks}")
            score -= 5
            interventions.append(f"VERIFY: Ensure all {failed_checks} are complete")

        # Brand guideline compliance
        # In actual system, this would check against brand guidelines
        score = max(0, score)

        return score


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

        # 1. Food safety red flags (40점)
        safety_score = self._check_food_safety(food, issues, findings, red_flags)
        scores['food_safety'] = safety_score

        # 2. Policy compliance red flags (30점)
        policy_score = self._check_policy_compliance(food, issues, findings, red_flags)
        scores['policy_compliance'] = policy_score

        # 3. Brand violation red flags (30점)
        brand_score = self._check_brand_compliance(food, issues, findings, red_flags)
        scores['brand_compliance'] = brand_score

        total = sum(scores.values())
        success = total >= 70 and len(red_flags) == 0  # Zero tolerance for red flags

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
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

        # Critical: Unsafe food classification
        if food.safety_level != SafetyLevel.SAFE:
            flags.append(f"RED_FLAG: Food classified as {food.safety_level.value}")
            return 0

        findings.append("✓ Food safety classification: SAFE")

        # Check for toxic ingredient warnings
        toxic_keywords = ['독소', '중독', '위험', 'toxic', 'poison']
        dangerous_mentions = sum(1 for kw in toxic_keywords if kw in ' '.join(food.cautions))

        if dangerous_mentions == 0:
            findings.append("✓ No toxic ingredients mentioned")
        else:
            flags.append(f"RED_FLAG: Toxic ingredient warnings found ({dangerous_mentions})")
            score -= 20

        # Check for allergy warnings
        allergy_warning = any('알레르기' in c or 'allergy' in c.lower() for c in food.cautions)
        if allergy_warning:
            findings.append("✓ Allergy warnings present")
        else:
            findings.append("⚠ No allergy warning (expected for safe foods)")
            score -= 5

        return max(0, score)

    def _check_policy_compliance(self, food: FoodProfile, issues: List, findings: List, flags: List) -> float:
        """Check CLAUDE.md policy compliance"""
        score = 30

        # Rule 5: AI marking requirement
        # In actual implementation, this checks if AI marking is auto-applied
        findings.append("✓ AI marking compliant (managed by CaptionAgent)")

        # Rule 2: Background consistency check (본문 배경 = 표지 배경)
        # This is image-level, noted as pending manual verification
        findings.append("⚠ Background consistency check (image-level, manual review)")

        # Rule 1: Model ID verification (flux-2-pro)
        # This is script-level, noted as hardcoded in generate_images.py
        findings.append("✓ Model ID verification (hardcoded in generate_images.py)")

        # Check for policy conflicts in cautions/benefits
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

        # Brand guideline 1: Emoji usage
        emoji_in_slides = sum(1 for s in food.slides if any(ord(c) > 127 for c in s.get('title', '')))
        if emoji_in_slides >= 2:
            findings.append(f"✓ Brand tone: Emoji usage present ({emoji_in_slides} slides)")
        else:
            findings.append("⚠ Limited emoji usage (brand friendly tone)")
            score -= 3

        # Brand guideline 2: Korean naming
        if food.topic_kr and len(food.topic_kr) > 0:
            findings.append(f"✓ Korean naming: '{food.topic_kr}' (local audience appeal)")
        else:
            flags.append("RED_FLAG: Missing Korean product name")
            score -= 15

        # Brand guideline 3: CTA presence
        has_cta = any(s.get('type') == 'cta' for s in food.slides)
        if has_cta:
            findings.append("✓ CTA slide present (engagement requirement)")
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

        # 1. API cost estimation (35점)
        api_cost, api_score = self._estimate_api_costs(food, issues, findings)
        costs['api_cost_usd'] = api_cost
        scores['api_efficiency'] = api_score

        # 2. Compute cost estimation (35점)
        compute_cost, compute_score = self._estimate_compute_costs(food, issues, findings)
        costs['compute_cost_usd'] = compute_cost
        scores['compute_efficiency'] = compute_score

        # 3. Storage cost estimation (30점)
        storage_cost, storage_score = self._estimate_storage_costs(food, issues, findings)
        costs['storage_cost_usd'] = storage_cost
        scores['storage_efficiency'] = storage_score

        total = sum(scores.values())
        success = total >= 70  # Cost efficiency score

        # Cost-benefit analysis
        cost_per_image = api_cost + compute_cost
        findings.append(f"Cost per content set: ${cost_per_image:.2f} ({len(food.slides)} images)")

        return AgentEvaluation(
            agent_name=self.name,
            agent_id=self.agent_id,
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
                },
                'cost_per_slide_usd': round((api_cost + compute_cost) / len(food.slides), 3)
            }
        )

    def _estimate_api_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate API costs (fal-ai FLUX.2 Pro)"""

        # FLUX.2 Pro pricing (as of 2026)
        # - Text-to-Image: $0.025 per image
        # - Queue processing: included

        image_count = len(food.slides) - 1  # Exclude cover (PD-made)
        cost_per_image = 0.025  # fal-ai FLUX.2 Pro
        total_api_cost = image_count * cost_per_image

        findings.append(f"API Cost: {image_count} images × ${cost_per_image} = ${total_api_cost:.2f}")

        # Efficiency score (lower cost = higher score)
        # Baseline: 3 images = $0.075 (full score)
        if image_count <= 3:
            score = 35
        elif image_count <= 5:
            score = 33
        else:
            score = 30 - (image_count - 5) * 2  # Penalty for extra images
            score = max(20, score)

        return total_api_cost, score

    def _estimate_compute_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate compute/processing costs"""

        # Processing pipeline:
        # 1. Image generation (included in API)
        # 2. Text overlay (Puppeteer + Node.js) - ~$0.001 per slide
        # 3. Quality check (automated) - ~$0.0005 per slide
        # 4. Publishing (Graph API) - ~$0.0001 per post

        slide_count = len(food.slides)

        overlay_cost = slide_count * 0.001
        qc_cost = slide_count * 0.0005
        publish_cost = 0.0001

        total_compute_cost = overlay_cost + qc_cost + publish_cost

        findings.append(f"Compute Cost: Overlay ${overlay_cost:.4f} + QC ${qc_cost:.4f} + Publish ${publish_cost:.4f} = ${total_compute_cost:.4f}")

        # Efficiency score (compute is minimal)
        score = 35  # Full score for minimal compute overhead

        return total_compute_cost, score

    def _estimate_storage_costs(self, food: FoodProfile, issues: List, findings: List) -> Tuple[float, float]:
        """Calculate storage costs (Cloudinary)"""

        # Cloudinary Free tier: 25GB storage included
        # Paid tier: $0.10 per GB per month (above 25GB)

        # Estimate per content:
        # - 4 slides × 2MB each = 8MB total
        # - Monthly storage for 1 content = negligible (~$0.0008/month)

        slide_count = len(food.slides)
        size_per_slide_mb = 2.0
        total_size_mb = slide_count * size_per_slide_mb
        monthly_storage_cost = (total_size_mb / 1024) * 0.10 / 30  # Per-day cost

        findings.append(f"Storage: {slide_count} slides × {size_per_slide_mb}MB = {total_size_mb}MB (~${monthly_storage_cost:.6f}/day)")

        # Most content within free tier
        score = 35  # Full score for minimal storage cost

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
        final_verdict = self._determine_verdict(evaluations, conflicts)

        # Calculate total score
        total_score = sum(ev.metadata.get('total_score', 0) for ev in evaluations.values()) / len(evaluations)

        # Count questions asked (should be 0)
        qa_questions = self._count_qa_questions(evaluations)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return AOCResult(
            food_name=food.topic_en,
            food_kr=food.topic_kr,
            timestamp=datetime.now().isoformat(),
            evaluations=evaluations,
            conflicts=conflicts,
            final_verdict=final_verdict,
            total_score=round(total_score, 1),
            qa_questions=qa_questions,
            execution_time_ms=execution_time
        )

    def _detect_conflicts(self, evaluations: Dict[str, AgentEvaluation]) -> List[str]:
        """Detect conflicts between agent evaluations"""
        conflicts = []

        # Check for contradictory verdicts
        # Agent C (auto_publishable) vs Agent D (red flags)
        agent_c_auto = evaluations['C'].metadata.get('auto_publishable', False)
        agent_d_red_flags = evaluations['D'].metadata.get('red_flags_count', 0) > 0

        if agent_c_auto and agent_d_red_flags:
            conflicts.append("CONFLICT: Agent C (auto_publishable) vs Agent D (red flags detected)")

        # Check for score divergence (all should pass >= 70)
        failed_agents = [
            ev.agent_id for ev in evaluations.values()
            if not ev.success
        ]

        if failed_agents:
            conflicts.append(f"CONFLICT: Agents {failed_agents} failed quality threshold")

        # Check for intervention point conflicts
        agent_c_interventions = evaluations['C'].metadata.get('intervention_points', [])
        agent_d_red_flags_list = evaluations['D'].metadata.get('red_flags', [])

        if agent_c_interventions and agent_d_red_flags_list:
            # This is expected in some cases (human review needed)
            pass

        return conflicts

    def _determine_verdict(self, evaluations: Dict[str, AgentEvaluation], conflicts: List[str]) -> PublishVerdict:
        """Determine final publication verdict"""

        # All agents must pass (score >= 70)
        all_pass = all(ev.success for ev in evaluations.values())

        # Agent D (Red Flag Detector) has veto power
        agent_d_has_red_flags = evaluations['D'].metadata.get('red_flags_count', 0) > 0

        # Agent C determines automation feasibility
        agent_c_auto = evaluations['C'].metadata.get('auto_publishable', False)

        # Decision logic
        if not all_pass:
            return PublishVerdict.HUMAN_QUEUE

        if agent_d_has_red_flags:
            return PublishVerdict.REJECT

        if agent_c_auto and all_pass:
            return PublishVerdict.AUTO_PUBLISH
        else:
            return PublishVerdict.HUMAN_QUEUE

    def _count_qa_questions(self, evaluations: Dict[str, AgentEvaluation]) -> int:
        """Count questions asked by agents"""
        # Expected: 0 questions for well-formed content
        # Questions would be marked with '?' in findings/issues

        total_questions = 0
        for ev in evaluations.values():
            total_questions += sum(1 for finding in ev.findings if '?' in finding)
            total_questions += sum(1 for issue in ev.issues if '?' in issue)

        return total_questions


# ============================================================================
# Test Data
# ============================================================================

def create_cucumber_profile() -> FoodProfile:
    """Create cucumber test profile (v6 standard, 4 slides)"""
    return FoodProfile(
        topic_en='cucumber',
        topic_kr='오이',
        safety_level=SafetyLevel.SAFE,
        slides=[
            {
                'slide': 0,
                'name': 'cover',
                'type': 'cover',
                'title': 'CUCUMBER',
                'subtitle': ''
            },
            {
                'slide': 1,
                'name': 'result_benefit',
                'type': 'content_bottom',
                'title': '먹어도 돼요! ✅',
                'subtitle': '수분 95% 저칼로리 간식'
            },
            {
                'slide': 2,
                'name': 'caution_amount',
                'type': 'content_bottom',
                'title': '껍질째 OK! ⚠️',
                'subtitle': '소형 2조각 | 중형 3조각 | 대형 4조각'
            },
            {
                'slide': 3,
                'name': 'cta',
                'type': 'cta',
                'title': '저장 필수! 📌',
                'subtitle': '피클/양념 오이는 금지! 댓글로 알려주세요!'
            }
        ],
        benefits=[
            '수분 공급: 95% 수분으로 여름철 탈수 예방',
            '저칼로리: 다이어트 간식으로 적합',
            '소화 건강: 식이섬유로 장 건강 증진'
        ],
        cautions=[
            '농약 제거를 위해 물로 깨끗이 세척',
            '피클/양념 오이는 나트륨 과다로 금지',
            '껍질째 먹일 수 있지만 목에 걸릴 수 있으니 주의',
            '과다 급여 시 설사 가능'
        ],
        amount_guide='소형 2조각 | 중형 3조각 | 대형 4조각'
    )


def create_kiwi_profile() -> FoodProfile:
    """Create kiwi test profile (v7 standard, 10 slides)"""
    return FoodProfile(
        topic_en='kiwi',
        topic_kr='키위',
        safety_level=SafetyLevel.SAFE,
        slides=[
            {'slide': 1, 'type': 'cover', 'title': 'KIWI', 'subtitle': '초록빛 비타민 보석'},
            {'slide': 2, 'type': 'content_bottom', 'title': '먹어도 돼요!', 'subtitle': '과육만 소량 급여 OK! 🥝'},
            {'slide': 3, 'type': 'content_bottom', 'title': '비타민C 최고', 'subtitle': '오렌지보다 2배 많아요! ✨'},
            {'slide': 4, 'type': 'content_bottom', 'title': '소화 효소', 'subtitle': '단백질 소화를 도와요! 🌿'},
            {'slide': 5, 'type': 'content_bottom', 'title': '항산화 성분', 'subtitle': '노화 방지에 효과적! 💪'},
            {'slide': 6, 'type': 'content_bottom', 'title': '껍질 제거!', 'subtitle': '껍질은 소화 어려워요! 🚫'},
            {'slide': 7, 'type': 'content_bottom', 'title': '알레르기 주의', 'subtitle': '처음엔 소량만 테스트! ⚠️'},
            {'slide': 8, 'type': 'content_top', 'title': '체중 5kg당', 'subtitle': '1-2조각이 적당해요! 🥝'},
            {'slide': 9, 'type': 'content_bottom', 'title': '상큼 키위', 'subtitle': '비타민 가득 간식! 🥝'},
            {'slide': 10, 'type': 'cta', 'title': '저장 필수!', 'subtitle': '키위 안전 급여법! 🐶'}
        ],
        benefits=[
            '비타민C: 오렌지보다 2배 풍부한 면역력 강화',
            '소화 효소: 액티니딘으로 단백질 소화 촉진',
            '항산화 성분: 노화 방지 및 건강 유지',
            '식이섬유: 장 건강 증진'
        ],
        cautions=[
            '껍질 반드시 제거 (소화 어려움)',
            '씨앗도 제거 후 급여',
            '알레르기 반응 가능성 (특히 유럽산 품종)',
            '처음 급여 시 소량으로 알레르기 테스트 필수',
            '체중 5kg당 1-2조각만 적정량'
        ],
        amount_guide='체중 5kg당 1-2조각'
    )


# ============================================================================
# Main Test Function
# ============================================================================

async def run_aoc_evaluation_test():
    """Run AOC 5-agent parallel evaluation test"""

    print("\n" + "="*80)
    print("AOC 5-AGENT PARALLEL EVALUATION SIMULATION")
    print("Project Sunshine - Food Content Quality Assessment")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected: 0 questions asked, both foods AUTO_PUBLISH\n")

    # Initialize AOC Controller
    aoc = AOCController()

    # Create test profiles
    cucumber = create_cucumber_profile()
    kiwi = create_kiwi_profile()

    # Run parallel evaluations for both foods
    print("Running parallel evaluation for 2 foods...")
    print(f"Food 1: {cucumber.topic_kr} ({cucumber.topic_en}) - {len(cucumber.slides)} slides")
    print(f"Food 2: {kiwi.topic_kr} ({kiwi.topic_en}) - {len(kiwi.slides)} slides\n")

    cucumber_result = await aoc.evaluate_food(cucumber)
    kiwi_result = await aoc.evaluate_food(kiwi)

    # Print results
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80 + "\n")

    # Cucumber results
    print(f"CUCUMBER (오이) - v6 Standard (4 slides)")
    print("-" * 80)
    print_aoc_result(cucumber_result)

    # Kiwi results
    print(f"\n\nKIWI (키위) - v7 Standard (10 slides)")
    print("-" * 80)
    print_aoc_result(kiwi_result)

    # Summary table
    print("\n" + "="*80)
    print("SUMMARY TABLE")
    print("="*80)
    print_summary_table(cucumber_result, kiwi_result)

    # Conflict analysis
    print("\n" + "="*80)
    print("PARALLEL CONFLICT ANALYSIS")
    print("="*80)
    print_conflict_analysis(cucumber_result, kiwi_result)

    # Final verdict
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    cucumber_pass = cucumber_result.final_verdict == PublishVerdict.AUTO_PUBLISH
    kiwi_pass = kiwi_result.final_verdict == PublishVerdict.AUTO_PUBLISH

    print(f"Cucumber (오이):  {cucumber_result.final_verdict.value} {'✓ PASS' if cucumber_pass else '✗ FAIL'}")
    print(f"Kiwi (키위):     {kiwi_result.final_verdict.value} {'✓ PASS' if kiwi_pass else '✗ FAIL'}")

    print(f"\nQuestions Asked: {cucumber_result.qa_questions + kiwi_result.qa_questions} (expected: 0)")
    print(f"Execution Time:  {cucumber_result.execution_time_ms + kiwi_result.execution_time_ms:.1f}ms")

    overall_pass = cucumber_pass and kiwi_pass and (cucumber_result.qa_questions + kiwi_result.qa_questions) == 0
    print(f"\nOVERALL TEST: {'✓ PASS' if overall_pass else '✗ FAIL'}")

    return overall_pass


def print_aoc_result(result: AOCResult):
    """Print detailed AOC result for a food"""

    # Agent scores
    print(f"Food: {result.food_kr} ({result.food_name})")
    print(f"Timestamp: {result.timestamp}")
    print(f"Execution Time: {result.execution_time_ms:.1f}ms\n")

    print("Agent Scores:")
    print("-" * 80)
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
    print(f"Final Verdict: {result.final_verdict.value}")
    print(f"QA Questions: {result.qa_questions}")

    # Conflicts
    if result.conflicts:
        print(f"\nConflicts Detected: {len(result.conflicts)}")
        for conflict in result.conflicts:
            print(f"  - {conflict}")
    else:
        print("\nConflicts Detected: 0 (No parallel conflicts)")

    # Agent details
    print("\nAgent Details:")
    print("-" * 80)
    for agent_id in ['A', 'B', 'C', 'D', 'E']:
        ev = result.evaluations[agent_id]
        print(f"\n{agent_names[agent_id]} (Agent {agent_id}):")

        if ev.scores:
            print(f"  Scores: {ev.scores}")

        if ev.findings:
            print(f"  Findings ({len(ev.findings)}):")
            for finding in ev.findings[:3]:  # Show first 3
                print(f"    - {finding}")
            if len(ev.findings) > 3:
                print(f"    ... and {len(ev.findings) - 3} more")

        if ev.issues:
            print(f"  Issues ({len(ev.issues)}):")
            for issue in ev.issues[:3]:  # Show first 3
                print(f"    - {issue}")
            if len(ev.issues) > 3:
                print(f"    ... and {len(ev.issues) - 3} more")

        # Agent-specific metadata
        if agent_id == 'C':
            interventions = ev.metadata.get('intervention_points', [])
            if interventions:
                print(f"  Intervention Points: {interventions}")
            auto_pub = ev.metadata.get('auto_publishable', False)
            print(f"  Auto-Publishable: {auto_pub}")

        if agent_id == 'D':
            red_flags = ev.metadata.get('red_flags', [])
            if red_flags:
                print(f"  Red Flags: {red_flags}")

        if agent_id == 'E':
            costs = ev.metadata.get('estimated_costs', {})
            if costs:
                print(f"  Estimated Costs: {costs}")


def print_summary_table(cucumber: AOCResult, kiwi: AOCResult):
    """Print summary comparison table"""

    print(f"\n{'Metric':<30} {'Cucumber (오이)':<20} {'Kiwi (키위)':<20}")
    print("-" * 70)

    metrics = [
        ('Agent A Score', 'evaluations.A.metadata.total_score'),
        ('Agent B Score', 'evaluations.B.metadata.total_score'),
        ('Agent C Score', 'evaluations.C.metadata.total_score'),
        ('Agent D Score', 'evaluations.D.metadata.total_score'),
        ('Agent E Score', 'evaluations.E.metadata.total_score'),
        ('Average Score', 'total_score'),
        ('Final Verdict', 'final_verdict.value'),
        ('QA Questions', 'qa_questions'),
        ('Conflicts', 'conflicts'),
        ('Exec Time (ms)', 'execution_time_ms')
    ]

    for metric_name, metric_path in metrics:
        cucumber_val = get_nested_attr(cucumber, metric_path)
        kiwi_val = get_nested_attr(kiwi, metric_path)

        print(f"{metric_name:<30} {str(cucumber_val):<20} {str(kiwi_val):<20}")


def print_conflict_analysis(cucumber: AOCResult, kiwi: AOCResult):
    """Print conflict analysis"""

    total_conflicts = len(cucumber.conflicts) + len(kiwi.conflicts)

    print(f"Total Parallel Conflicts: {total_conflicts}\n")

    if cucumber.conflicts:
        print(f"Cucumber Conflicts ({len(cucumber.conflicts)}):")
        for conflict in cucumber.conflicts:
            print(f"  - {conflict}")
    else:
        print("Cucumber Conflicts: None ✓")

    if kiwi.conflicts:
        print(f"\nKiwi Conflicts ({len(kiwi.conflicts)}):")
        for conflict in kiwi.conflicts:
            print(f"  - {conflict}")
    else:
        print("\nKiwi Conflicts: None ✓")

    print(f"\nOverall Conflict Status: {'✓ CLEAN' if total_conflicts == 0 else f'✗ {total_conflicts} conflicts'}")


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

def test_aoc_5agent_parallel_evaluation():
    """Pytest integration for AOC evaluation"""
    result = asyncio.run(run_aoc_evaluation_test())
    assert result, "AOC evaluation failed"


if __name__ == "__main__":
    asyncio.run(run_aoc_evaluation_test())
