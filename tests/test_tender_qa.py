import pytest

from src.llm_provider import GeminiNotConfiguredError, GeminiRequestError
from src.schemas import EvidenceRecord
from src.tender_qa import (
    answer_tender_question,
)


def evidence(text, filename="Tender.pdf", page=3):
    return EvidenceRecord(
        filename=filename,
        page_number=page,
        quoted_text=text,
    )


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def generate_structured(self, prompt, response_model):
        if self.error:
            raise self.error
        return response_model.model_validate(self.result)


def test_empty_question_is_rejected():
    with pytest.raises(ValueError):
        answer_tender_question("  ", [evidence("Payment within 30 days")])


def test_no_relevant_evidence_returns_insufficient_evidence():
    result = answer_tender_question(
        "What is the warranty period?",
        [evidence("Payment will be made within 30 days.")],
    )

    assert result.insufficient_evidence is True
    assert result.ai_used is False
    assert result.sources == []


def test_missing_gemini_key_returns_relevant_passages(monkeypatch):
    def missing_key_provider():
        return FakeProvider(
            error=GeminiNotConfiguredError("Gemini is not configured.")
        )

    monkeypatch.setattr(
        "src.tender_qa.GeminiProvider",
        missing_key_provider,
    )

    result = answer_tender_question(
        "What are the payment terms?",
        [evidence("Payment will be made within 30 days.")],
    )

    assert result.insufficient_evidence is True
    assert result.ai_used is False
    assert result.sources[0].filename == "Tender.pdf"
    assert result.sources[0].page_number == 3
    assert "not configured" in result.warning.lower()
    assert "Payment will be made within 30 days." in result.answer


def test_valid_answer_uses_original_evidence_citation():
    provider = FakeProvider(
        result={
            "answer": "Payment is due within 30 days.",
            "evidence_indices": [0],
            "insufficient_evidence": False,
        }
    )

    result = answer_tender_question(
        "What are the payment terms?",
        [evidence("Payment will be made within 30 days.", page=8)],
        provider=provider,
    )

    assert result.ai_used is True
    assert result.insufficient_evidence is False
    assert result.sources[0].page_number == 8
    assert result.sources[0].quoted_text == (
        "Payment will be made within 30 days."
    )


def test_invalid_evidence_index_rejects_answer():
    provider = FakeProvider(
        result={
            "answer": "Payment is due in 30 days.",
            "evidence_indices": [99],
            "insufficient_evidence": False,
        }
    )

    result = answer_tender_question(
        "What are the payment terms?",
        [evidence("Payment will be made within 30 days.")],
        provider=provider,
    )

    assert result.ai_used is False
    assert result.insufficient_evidence is True
    assert result.sources == []
    assert "rejected" in result.answer.lower()


def test_answer_without_citations_is_not_trusted():
    provider = FakeProvider(
        result={
            "answer": "Payment is due within 30 days.",
            "evidence_indices": [],
            "insufficient_evidence": False,
        }
    )

    result = answer_tender_question(
        "What are the payment terms?",
        [evidence("Payment will be made within 30 days.")],
        provider=provider,
    )

    assert result.ai_used is False
    assert result.insufficient_evidence is True
    assert result.sources == []


def test_provider_failure_preserves_source_passages():
    provider = FakeProvider(error=GeminiRequestError("simulated failure"))

    result = answer_tender_question(
        "What are the payment terms?",
        [evidence("Payment will be made within 30 days.")],
        provider=provider,
    )

    assert result.ai_used is False
    assert result.sources[0].filename == "Tender.pdf"
    assert result.warning is not None
