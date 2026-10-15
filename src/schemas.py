"""Structured data models for tender analysis and evidence tracking."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FindingStatus(str, Enum):
    """Status of a parameter finding."""

    FOUND = "Found"
    NOT_FOUND = "Not found in reviewed documents"
    NEEDS_REVIEW = "Needs review"
    CONFLICTING = "Conflicting evidence"
    EXTRACTION_FAILED = "Extraction failed"


class RiskLevel(str, Enum):
    """Risk level assigned to a tender finding."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    NOT_ASSESSED = "Not assessed"


class DocumentMetadata(BaseModel):
    """Metadata for one uploaded tender document."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    document_type: str = "Unknown"
    total_pages: int = Field(ge=0)
    file_size_bytes: int = Field(ge=0)
    extraction_status: str = "Pending"


class EvidenceRecord(BaseModel):
    """A traceable piece of evidence from a tender document."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    quoted_text: str = Field(min_length=1)
    section_heading: str | None = None
    clause_reference: str | None = None


class ParameterFinding(BaseModel):
    """Analysis result for one standard tender parameter."""

    model_config = ConfigDict(extra="forbid")

    parameter_number: int = Field(ge=1, le=27)
    parameter_key: str = Field(min_length=1)
    parameter_name: str = Field(min_length=1)

    status: FindingStatus = FindingStatus.NOT_FOUND
    requirement_summary: str | None = None
    costing_impact: str | None = None
    risk_level: RiskLevel = RiskLevel.NOT_ASSESSED

    evidence: list[EvidenceRecord] = Field(default_factory=list)
    review_required: bool = False
    review_reason: str | None = None
    analyst_notes: str | None = None


class TenderAnalysisResult(BaseModel):
    """Complete analysis result for an uploaded tender package."""

    model_config = ConfigDict(extra="forbid")

    tender_reference: str | None = None
    documents: list[DocumentMetadata] = Field(default_factory=list)
    findings: list[ParameterFinding] = Field(default_factory=list)
    overall_status: str = "Not started"
    warnings: list[str] = Field(default_factory=list)
