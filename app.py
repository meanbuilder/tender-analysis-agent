"""Streamlit dashboard for Tender Intelligence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

from src.parameter_catalog import get_all_parameters
from src.pdf_preview import render_highlighted_pdf_page
from src.tender_pipeline import run_tender_pipeline
from src.tender_qa import answer_tender_question

APP_TITLE = "Tender Intelligence"
APP_SUBTITLE = "Industrial Tender Analysis & Estimation Automation"


# ---------------------------------------------------------------------
# Application theme
# ---------------------------------------------------------------------


def _load_xp_sap_theme() -> None:
    """Load the local Windows XP / SAP R/3-inspired stylesheet."""

    css_path = Path(__file__).parent / "assets" / "xp_sap.css"

    if not css_path.is_file():
        st.warning("XP/SAP theme stylesheet was not found; using default styling.")
        return

    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _render_xp_sap_chrome() -> None:
    """Render the application title bar and transaction toolbar."""

    st.markdown(
        """
        <div class="xp-titlebar">
            Tender Intelligence
            <small>TPP Boilers | Industrial Tender Analysis &amp; Estimation</small>
        </div>
        <div class="sap-toolbar">
            <span class="sap-transaction">ZTENDER01</span>
            <span> Tender Workspace </span>
            <span>|</span>
            <span> Technical Analysis </span>
            <span>|</span>
            <span> Commercial Review </span>
            <span>|</span>
            <span> AI Tender Analyst </span>
            <span>|</span>
            <span> Reports </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------


def _status_value(value: object) -> str:
    """Convert enum-like values into readable text."""

    return str(getattr(value, "value", value))


def _make_widget_key(*parts: object) -> str:
    """Create a deterministic Streamlit widget key from identifying parts."""

    source = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]
    return f"source_preview_{digest}"


def _source_preview_button(
    filename: str,
    page_number: int,
    quoted_text: str,
    *,
    key_prefix: str,
) -> None:
    """Show the original PDF page with a highlight when available."""

    source_pdfs = st.session_state.get("tender_source_pdfs", {})
    pdf_bytes = source_pdfs.get(filename)

    button_key = _make_widget_key(
        key_prefix,
        filename,
        page_number,
        quoted_text,
    )

    if not st.button(
        f"View original page {page_number} with highlight",
        key=button_key,
    ):
        return

    if not pdf_bytes:
        st.warning(
            "The original PDF is not available in this session. "
            "Upload the document again and rerun the analysis."
        )
        return

    image_bytes, highlighted, message = render_highlighted_pdf_page(
        pdf_bytes,
        page_number,
        quoted_text,
    )

    if image_bytes is None:
        st.error(message)
        return

    st.image(
        image_bytes,
        caption=f"{filename} — original PDF page {page_number}",
        width="stretch",
    )

    if highlighted:
        st.success(message)
    else:
        st.warning(message)


def _upload_signature(uploaded_files) -> tuple[tuple[str, int], ...]:
    """Identify the current upload selection."""

    return tuple((file.name, file.size) for file in uploaded_files)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------


def render_sidebar() -> None:
    """Render navigation and workspace information."""

    with st.sidebar:
        st.title("Tender Intelligence")
        st.caption("Industrial procurement analysis")
        st.divider()

        st.subheader("Workspace")
        st.markdown("""
            - Tender Overview
            - Document Upload
            - Parameter Analysis
            - BOQ & Technical Items
            - Risk Register
            - Excel Export
            - AI Tender Analyst
            """)

        st.divider()
        st.caption("Analysis is evidence-based.")
        st.caption("Human verification remains mandatory.")


# ---------------------------------------------------------------------
# Document upload and analysis execution
# ---------------------------------------------------------------------


def render_document_upload() -> None:
    """Handle PDF uploads and run the tender analysis pipeline."""

    st.header("Tender Documents")
    st.write(
        "Upload the GeM bid, ATC, technical specifications, BOQ, "
        "eligibility documents, amendments and related tender PDFs."
    )

    tender_reference = st.text_input(
        "Tender / Bid Reference (optional)",
        placeholder="Enter the NIT or GeM Bid Number",
    )

    uploaded_files = st.file_uploader(
        "Select tender PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select multiple PDFs belonging to the same tender.",
    )

    if not uploaded_files:
        st.info("Upload one or more PDF documents to begin.")
        return

    signature = _upload_signature(uploaded_files)

    st.success(f"{len(uploaded_files)} PDF file(s) selected.")

    st.dataframe(
        [
            {
                "Filename": file.name,
                "Size (KB)": round(file.size / 1024, 2),
                "Type": file.type or "Unknown",
            }
            for file in uploaded_files
        ],
        width="stretch",
        hide_index=True,
    )

    if st.button(
        "Run Tender Analysis",
        type="primary",
        width="stretch",
    ):
        try:
            documents = [(file.name, file.getvalue()) for file in uploaded_files]

            # Store original PDFs for source-page previews.
            # Duplicate filenames are rejected to prevent ambiguity.
            filenames = [filename for filename, _ in documents]

            if len(filenames) != len(set(filenames)):
                st.error(
                    "Two or more uploaded files have the same filename. "
                    "Rename the files and upload them again so source "
                    "citations can identify the correct PDF."
                )
                return

            with st.spinner(
                "Extracting documents and analysing tender requirements..."
            ):
                output = run_tender_pipeline(
                    documents,
                    tender_reference=tender_reference.strip() or None,
                )

            st.session_state["tender_source_pdfs"] = {
                filename: pdf_bytes for filename, pdf_bytes in documents
            }

            st.session_state["tender_pipeline_output"] = output
            st.session_state["tender_upload_signature"] = signature

            # Clear Q&A results when a new analysis is run.
            st.session_state.pop("tender_qa_result", None)
            st.session_state.pop("tender_qa_answered_question", None)

            st.success("Analysis workflow finished.")

        except Exception as exc:
            st.error(
                "The analysis could not be completed. "
                "Check the application terminal for diagnostic details."
            )
            st.exception(exc)
            return

    saved_signature = st.session_state.get("tender_upload_signature")

    if saved_signature != signature:
        st.info(
            "Run the analysis for the currently selected documents "
            "to display their results."
        )
        return

    output = st.session_state.get("tender_pipeline_output")

    if output is not None:
        render_analysis_results(output)


# ---------------------------------------------------------------------
# Analysis results
# ---------------------------------------------------------------------


def render_analysis_results(output) -> None:
    """Render findings, evidence, BOQ candidates and Q&A."""

    result = output.result
    findings = result.findings

    st.divider()
    st.header("Analysis Results")
    st.write(f"**Status:** {result.overall_status}")

    status_values = [_status_value(f.status) for f in findings]
    risk_values = [_status_value(f.risk_level) for f in findings]

    high_risk_count = sum(risk in {"HIGH", "CRITICAL"} for risk in risk_values)
    review_count = sum(bool(f.review_required) for f in findings)
    found_count = sum(status == "FOUND" for status in status_values)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Parameters", len(findings))
    col2.metric("Requirements Found", found_count)
    col3.metric("High / Critical Risk", high_risk_count)
    col4.metric("Requiring Review", review_count)

    # Documents processed
    st.subheader("Documents Processed")

    st.dataframe(
        [
            {
                "Document": document.filename,
                "Type": document.document_type,
                "Pages": document.total_pages,
                "Extraction Status": document.extraction_status,
                "Size (KB)": round(document.file_size_bytes / 1024, 2),
            }
            for document in result.documents
        ],
        width="stretch",
        hide_index=True,
    )

    if result.warnings:
        with st.expander(
            f"Warnings and exceptions ({len(result.warnings)})",
            expanded=True,
        ):
            for warning in result.warnings:
                st.warning(warning)

    # Parameter summary
    st.subheader("27-Parameter Tender Analysis")

    parameter_rows = []

    for finding in findings:
        source_documents = sorted({e.filename for e in finding.evidence})
        source_pages = sorted({e.page_number for e in finding.evidence})

        parameter_rows.append(
            {
                "No.": finding.parameter_number,
                "Parameter": finding.parameter_name,
                "Status": _status_value(finding.status),
                "Requirement": finding.requirement_summary,
                "Costing Impact": finding.costing_impact,
                "Risk": _status_value(finding.risk_level),
                "Source Documents": ", ".join(source_documents),
                "Pages": ", ".join(map(str, source_pages)),
                "Review Required": finding.review_required,
                "Review Reason": finding.review_reason or "",
            }
        )

    st.dataframe(
        parameter_rows,
        width="stretch",
        hide_index=True,
        height=600,
    )

    st.caption(
        "A keyword match is a candidate finding, not a final legal or "
        "commercial interpretation. Verify each important clause in "
        "the original tender document."
    )

    # Evidence review
    st.subheader("Evidence Review")

    for finding_index, finding in enumerate(findings):
        label = (
            f"{finding.parameter_number}. {finding.parameter_name} — "
            f"{_status_value(finding.status)}"
        )

        with st.expander(label):
            st.write("**Requirement summary**")
            st.write(finding.requirement_summary or "No summary available.")

            st.write("**Risk level**")
            st.write(_status_value(finding.risk_level))

            if finding.review_reason:
                st.warning(finding.review_reason)

            if finding.analyst_notes:
                st.write("**Analyst notes**")
                st.write(finding.analyst_notes)

            if not finding.evidence:
                st.info(
                    "No supporting text was captured for this finding. "
                    "Review the original documents before concluding "
                    "that the clause is absent."
                )

            for evidence_index, evidence in enumerate(finding.evidence):
                st.markdown(
                    f"**{evidence.filename} — " f"page {evidence.page_number}**"
                )

                if evidence.clause_reference:
                    st.caption(f"Clause: {evidence.clause_reference}")

                if evidence.section_heading:
                    st.caption(f"Section: {evidence.section_heading}")

                st.code(evidence.quoted_text, language=None)

                _source_preview_button(
                    evidence.filename,
                    evidence.page_number,
                    evidence.quoted_text,
                    key_prefix=(f"evidence-{finding_index}-{evidence_index}"),
                )

    # BOQ and technical item candidates
    st.subheader("BOQ & Technical Item Candidates")

    if output.boq_items:
        st.dataframe(
            [
                {
                    "Item No.": item.item_number,
                    "Description": item.description,
                    "Quantity": (
                        str(item.quantity) if item.quantity is not None else None
                    ),
                    "Unit": item.unit,
                    "Unit Price": (
                        str(item.unit_price) if item.unit_price is not None else None
                    ),
                    "Total Price": (
                        str(item.total_price) if item.total_price is not None else None
                    ),
                    "Source Document": item.source_filename,
                    "Page": item.source_page,
                    "Review Required": item.review_required,
                    "Review Reason": item.review_reason,
                }
                for item in output.boq_items
            ],
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "BOQ results are candidates extracted from text. "
            "Verify item descriptions, quantities, units and prices "
            "against the original BOQ table."
        )
    else:
        st.info(
            "No BOQ candidates were extracted. A manual review of "
            "the tender BOQ is recommended."
        )

    # Prepare unique evidence for Q&A.
    st.subheader("AI Tender Analyst")

    st.caption(
        "Ask questions about the extracted tender evidence. "
        "Answers require source verification; missing text may affect results."
    )

    all_evidence = []
    seen_evidence = set()

    for finding in findings:
        for evidence in finding.evidence:
            evidence_key = (
                evidence.filename,
                evidence.page_number,
                evidence.quoted_text,
                evidence.section_heading,
                evidence.clause_reference,
            )

            if evidence_key not in seen_evidence:
                seen_evidence.add(evidence_key)
                all_evidence.append(evidence)

    with st.form("tender_qa_form", clear_on_submit=False):
        question = st.text_input(
            "Question about this tender",
            placeholder="e.g. What are the payment terms?",
            key="tender_qa_question",
        )

        submitted = st.form_submit_button(
            "Ask Tender Analyst",
            type="primary",
        )

    if submitted:
        if not question.strip():
            st.warning("Enter a question before submitting.")

        elif not all_evidence:
            st.warning(
                "No extracted evidence is available for Q&A. "
                "Review the source PDFs and extraction warnings."
            )

        else:
            with st.spinner("Reviewing relevant tender evidence..."):
                qa_result = answer_tender_question(
                    question,
                    all_evidence,
                )

            st.session_state["tender_qa_result"] = qa_result
            st.session_state["tender_qa_answered_question"] = question.strip()

    qa_result = st.session_state.get("tender_qa_result")
    answered_question = st.session_state.get("tender_qa_answered_question")

    if qa_result is not None:
        if answered_question:
            st.caption(f"Question: {answered_question}")

        st.markdown(qa_result.answer)

        if qa_result.warning:
            st.warning(qa_result.warning)

        if qa_result.insufficient_evidence:
            st.info(
                "This response is not a verified conclusion. "
                "Check the cited passages and original tender documents."
            )

        if qa_result.ai_used:
            st.caption(
                "AI-assisted answer. Verify the interpretation against "
                "the cited source text."
            )
        else:
            st.caption("No AI-generated answer was produced for this response.")

        if qa_result.sources:
            st.markdown("**Source passages**")

            for source_index, source in enumerate(qa_result.sources):
                st.markdown(f"**{source.filename} — page {source.page_number}**")
                st.code(source.quoted_text, language=None)

                # Keep the preview button inside the source loop.
                _source_preview_button(
                    source.filename,
                    source.page_number,
                    source.quoted_text,
                    key_prefix=f"qa-{source_index}",
                )

    # Excel report
    st.subheader("Excel Report")

    st.download_button(
        label="Download Tender Analysis Workbook (.xlsx)",
        data=output.workbook_bytes,
        file_name="tender_analysis_report.xlsx",
        mime=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        type="primary",
        width="stretch",
    )

    st.caption(
        "The workbook contains Tender Summary, BOQ and Technical Items, "
        "Compliance and Risk Register, Evidence and Exceptions, and "
        "Make in India Annexure 8 preparation worksheet."
    )


# ---------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------


def main() -> None:
    """Run the Tender Intelligence dashboard."""

    _load_xp_sap_theme()
    render_sidebar()
    _render_xp_sap_chrome()

    parameters = get_all_parameters()

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Standard Parameters", len(parameters))
    metric2.metric("Supported Input", "PDF")
    metric3.metric("Output", "Excel Workbook")

    st.divider()

    st.write(
        "Extract tender requirements, review commercial and technical "
        "risks, inspect supporting evidence, and prepare a structured "
        "workbook for human verification."
    )

    render_document_upload()

    st.divider()

    st.caption(
        "Local document processing | Gemini AI-assisted Q&A | "
        "Verify extracted requirements against original tender documents."
    )


if __name__ == "__main__":
    main()
