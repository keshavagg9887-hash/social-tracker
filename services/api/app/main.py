from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .ai_detections import router as ai_detections_router

app = FastAPI(
    title="Social Empowerment Platform API",
    description="Backend API for device management, AI detections, incidents, and streaming.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register AI Detections router [M2]
app.include_router(ai_detections_router, prefix="/api")

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "social-empowerment-api"}

