from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tender Intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    # Vite may choose 5174, 5175, etc. if its default port is already occupied.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
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
