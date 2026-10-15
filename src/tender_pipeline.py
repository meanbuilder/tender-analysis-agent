"""Orchestrate PDF extraction, tender analysis, risk assessment and export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.boq_extractor import BOQItem, extract_boq_items
from src.excel_exporter import workbook_to_bytes
from src.pdf_extractor import extract_pdf_bytes
from src.risk_engine import assess_risks
from src.schemas import (
    DocumentMetadata,
    EvidenceRecord,
    FindingStatus,
    RiskLevel,
    TenderAnalysisResult,
)
from src.tender_analyzer import analyze_tender_evidence


@dataclass
class TenderPipelineOutput:
    """Complete output produced by one tender-analysis run."""

    result: TenderAnalysisResult
    boq_items: list[BOQItem]
    workbook_bytes: bytes


def _failed_document_metadata(
    filename: str,
    file_size_bytes: int,
) -> DocumentMetadata:
    """Represent a document that could not be extracted."""

    return DocumentMetadata(
        filename=filename,
        document_type="PDF",
        total_pages=0,
        file_size_bytes=file_size_bytes,
        extraction_status="failed",
    )


def run_tender_pipeline(
    uploaded_documents: Iterable[tuple[str, bytes]],
    *,
    tender_reference: str | None = None,
) -> TenderPipelineOutput:
    """
    Process uploaded PDFs and generate an evidence-backed workbook.

    Each uploaded document is a (filename, PDF bytes) tuple.
    A failed document does not prevent other PDFs from being processed.
    """

    documents_input = list(uploaded_documents)

    if not documents_input:
        raise ValueError("Upload at least one PDF document.")

    document_metadata: list[DocumentMetadata] = []
    all_evidence: list[EvidenceRecord] = []
    warnings: list[str] = []
    failed_count = 0

    for filename, pdf_bytes in documents_input:
        if not isinstance(pdf_bytes, bytes) or not pdf_bytes:
            failed_count += 1
            document_metadata.append(
                _failed_document_metadata(filename, len(pdf_bytes or b""))
            )
            warnings.append(f"{filename}: the uploaded file is empty or invalid.")
            continue

        try:
            metadata, evidence = extract_pdf_bytes(
                pdf_bytes,
                display_filename=filename,
            )

            document_metadata.append(metadata)
            all_evidence.extend(evidence)

            if not evidence:
                warnings.append(
                    f"{filename}: no extractable text was found. "
                    "The PDF may be scanned or image-based."
                )

        except Exception as exc:
            failed_count += 1
            document_metadata.append(
                _failed_document_metadata(filename, len(pdf_bytes))
            )
            warnings.append(
                f"{filename}: extraction failed " f"({type(exc).__name__}: {exc})."
            )

    findings = analyze_tender_evidence(all_evidence)

    # If every document failed and no evidence exists, do not misrepresent
    # the parameters as simply absent from the tender.
    if not all_evidence and failed_count == len(documents_input):
        findings = [
            finding.model_copy(
                update={
                    "status": FindingStatus.EXTRACTION_FAILED,
                    "review_required": True,
                    "review_reason": (
                        "No tender evidence could be extracted. "
                        "Review the PDF files and retry before making "
                        "any compliance or costing decision."
                    ),
                }
            )
            for finding in findings
        ]

    findings = assess_risks(findings)

    boq_items = extract_boq_items(all_evidence)

    if not boq_items:
        warnings.append(
            "No BOQ item candidates were identified. "
            "Review the BOQ manually; table extraction may require "
            "additional handling."
        )

    if failed_count:
        warnings.append(
            f"{failed_count} of {len(documents_input)} document(s) "
            "could not be extracted successfully."
        )

    if all_evidence:
        overall_status = "Analysis completed — human review required"
    elif failed_count == len(documents_input):
        overall_status = "Extraction failed — review required"
    else:
        overall_status = "No extractable tender text — review required"

    result = TenderAnalysisResult(
        tender_reference=tender_reference or None,
        documents=document_metadata,
        findings=findings,
        overall_status=overall_status,
        warnings=warnings,
    )

    workbook = workbook_to_bytes(result, boq_items)

    return TenderPipelineOutput(
        result=result,
        boq_items=boq_items,
        workbook_bytes=workbook,
    )
