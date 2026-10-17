
import base64
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.tender_pipeline import run_tender_pipeline

MAX_BATCH_BYTES = 200 * 1024 * 1024
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_FILES = 50

app = FastAPI(
    title="Tender Intelligence API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "tender-intelligence-api",
        "version": app.version,
    }


@app.post("/api/tenders/analyze")
async def analyze_tender(
    files: Annotated[list[UploadFile], File(...)],
):
    """Analyze multiple PDFs and return findings plus an Excel workbook."""

    if not files:
        raise HTTPException(status_code=400, detail="Select at least one PDF.")

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum {MAX_FILES} PDF files per batch.",
        )

    documents: list[tuple[str, bytes]] = []
    total_bytes = 0

    try:
        for uploaded_file in files:
            filename = uploaded_file.filename or "unnamed.pdf"

            if not filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=415,
                    detail=f"{filename}: only PDF files are currently supported.",
                )

            content = await uploaded_file.read(MAX_FILE_BYTES + 1)

            if len(content) > MAX_FILE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{filename}: maximum file size is 50 MB.",
                )

            total_bytes += len(content)

            if total_bytes > MAX_BATCH_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="Combined upload size cannot exceed 200 MB.",
                )

            if not content.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=400,
                    detail=f"{filename}: this does not appear to be a valid PDF.",
                )

            documents.append((filename, content))

        try:
            output = run_tender_pipeline(documents)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Tender analysis failed: {type(exc).__name__}: {exc}",
            ) from exc

        return {
            "status": "completed",
            "analysis": output.result.model_dump(mode="json"),
            "boq_items": [
                item.model_dump(mode="json")
                if hasattr(item, "model_dump")
                else item.__dict__
                for item in output.boq_items
            ],
            "workbook_filename": "tender_analysis.xlsx",
            "workbook_base64": base64.b64encode(
                output.workbook_bytes
            ).decode("ascii"),
        }

    finally:
        for uploaded_file in files:
            await uploaded_file.close()
