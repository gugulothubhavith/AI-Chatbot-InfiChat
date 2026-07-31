"""Pydantic models for the Deep Research pipeline state."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class DepthLevel(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    EXHAUSTIVE = "exhaustive"


class SourceType(str, Enum):
    WEB = "web"
    ACADEMIC = "academic"
    NEWS = "news"
    FORUM = "forum"
    WIKIPEDIA = "wikipedia"
    GOVERNMENT = "government"
    PDF = "pdf"


class Stance(str, Enum):
    CONFIRMS = "confirms"
    CONTRADICTS = "contradicts"
    PARTIAL = "partial"
    NOISE = "noise"


class CriticVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    NEEDS_MORE = "NEEDS_MORE"
    DIFFERENT_ANGLE = "DIFFERENT_ANGLE"


# ── Agent 1 Output ──────────────────────────────────────

class ResearchBrief(BaseModel):
    topic: str = ""
    domain: str = ""
    depth_level: DepthLevel = DepthLevel.STANDARD
    time_sensitive: bool = False
    audience: str = "general"
    key_aspects: List[str] = Field(default_factory=list)


# ── Agent 2 Output ──────────────────────────────────────

class ResearchSubtopic(BaseModel):
    title: str
    priority: str = "medium"  # high, medium, low
    source_types_needed: List[str] = Field(default_factory=list)
    queries: List[str] = Field(default_factory=list)
    status: str = "active"  # active, pruned, completed
    score: float = 0.0


class ResearchPlan(BaseModel):
    main_topic: str = ""
    subtopics: List[ResearchSubtopic] = Field(default_factory=list)


# ── Agent 3 Output ──────────────────────────────────────

class SearchQuery(BaseModel):
    query: str
    category: str = "general"  # supporting, debunking, academic, news, data, temporal, regional
    priority: int = 5  # 1-10
    target_engines: str = "google,bing,duckduckgo"
    time_range: str = ""  # "", "day", "week", "month", "year"


# ── Agents 4-6 Output ──────────────────────────────────

class SourceDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    title: str = ""
    snippet: str = ""
    full_text: str = ""
    source_type: SourceType = SourceType.WEB
    authority_score: float = 0.5  # 0.0 - 1.0
    published_date: Optional[str] = None
    domain: str = ""
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Agent 7 Output ──────────────────────────────────────

class Entity(BaseModel):
    name: str
    entity_type: str  # PERSON, ORG, GPE, DATE, etc.
    mentions: int = 1
    sources: List[str] = Field(default_factory=list)  # source doc IDs


class Relationship(BaseModel):
    source_entity: str
    target_entity: str
    relation_type: str  # "works_at", "located_in", "caused_by", etc.
    confidence: float = 0.5


class KnowledgeGraphData(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)


# ── Agent 8 Output ──────────────────────────────────────

class TimelineEvent(BaseModel):
    date: str
    description: str
    source_id: str = ""
    recency_weight: float = 1.0


class TemporalData(BaseModel):
    events: List[TimelineEvent] = Field(default_factory=list)
    outdated_claims: List[str] = Field(default_factory=list)


# ── Agent 9 Output ──────────────────────────────────────

class FactClaim(BaseModel):
    claim: str
    supporting_sources: List[str] = Field(default_factory=list)
    contradicting_sources: List[str] = Field(default_factory=list)
    stance: Stance = Stance.NOISE
    confidence: float = 0.0
    source_count: int = 0


# ── Agent 10 Output ─────────────────────────────────────

class QualityCheck(BaseModel):
    name: str
    passed: bool = False
    detail: str = ""


class QualityGateResult(BaseModel):
    iteration: int = 1
    checks: List[QualityCheck] = Field(default_factory=list)
    verdict: CriticVerdict = CriticVerdict.NEEDS_MORE
    feedback: str = ""
    overall_confidence: float = 0.0
    targeted_queries: List[str] = Field(default_factory=list)


# ── Agent 11 Output ─────────────────────────────────────

class Citation(BaseModel):
    index: int
    title: str
    url: str
    authority: float = 0.5


class ResearchReport(BaseModel):
    executive_summary: str = ""
    key_findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_for: List[str] = Field(default_factory=list)
    evidence_against: List[str] = Field(default_factory=list)
    timeline: List[Dict[str, str]] = Field(default_factory=list)
    knowledge_graph_json: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Citation] = Field(default_factory=list)
    full_markdown: str = ""
    confidence_score: float = 0.0


# ── Pipeline State ──────────────────────────────────────

class ResearchState(BaseModel):
    """Mutable state object passed through the entire pipeline."""
    research_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    brief: Optional[ResearchBrief] = None
    plan: Optional[ResearchPlan] = None
    queries: List[SearchQuery] = Field(default_factory=list)
    sources: List[SourceDocument] = Field(default_factory=list)
    knowledge_graph: Optional[KnowledgeGraphData] = None
    temporal: Optional[TemporalData] = None
    facts: List[FactClaim] = Field(default_factory=list)
    quality_results: List[QualityGateResult] = Field(default_factory=list)
    report: Optional[ResearchReport] = None
    iteration: int = 0
    max_iterations: int = 2
    # --- New fields for enhanced pipeline ---
    research_stage: str = ""  # Current readable stage name (e.g. "Intent Analysis", "Web Search")
    partial_findings: List[Dict[str, Any]] = Field(default_factory=list)  # Stream intermediate results
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict)  # For resume capability
    stage_timestamps: Dict[str, str] = Field(default_factory=dict)  # Track timing per stage
    critic_feedback: str = ""  # Feedback from critic for adversarial query refinement
