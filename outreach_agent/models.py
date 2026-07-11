from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SignalType(str, Enum):
    JOB_POSTING = "job_posting"
    BLOG_POST = "blog_post"
    NEWS = "news"
    PRESS = "press"
    PRODUCT_PAGE = "product_page"
    REVIEW = "review"
    OTHER = "other"

class Prospect(BaseModel):
    name: str = Field(description="Name of the prospect")
    company: str = Field(description="Company of the prospect")
    title: str = Field(description="Job title of the prospect")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn URL (informational only)")

class GapSignal(BaseModel):
    description: str = Field(description="Description of the gap, problem, or pain point")
    source_snippet: str = Field(description="Verbatim quote from the source as evidence")
    source_url: str = Field(description="URL of the source where the signal was found")
    source_query: str = Field(description="The search query that led to this source")
    signal_type: SignalType = Field(description="Type of the source")
    confidence: float = Field(ge=0, le=1, description="Confidence score (0-1) based on recency, specificity, and relevance")
    reasoning: str = Field(description="Brief explanation of why this confidence score was assigned")

class Draft(BaseModel):
    subject: str = Field(description="Subject line of the email draft")
    body: str = Field(description="Body of the email draft")
    gap_used: GapSignal = Field(description="The specific GapSignal used to draft this message")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
