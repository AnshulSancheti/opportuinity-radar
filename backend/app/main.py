from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Opportunity Radar",
    description="News and hackathons with private saved collections",
    version="0.1.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Opportunity Radar API", "docs": "/docs"}


@app.middleware("http")
async def protect_browser_requests(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and origin not in origins:
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        if not origin and request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site request rejected"}, status_code=403)
        if request.method in {"POST", "PUT", "PATCH"} and "application/json" not in request.headers.get("content-type", ""):
            return JSONResponse({"detail": "JSON content type required"}, status_code=415)
    response = await call_next(request)
    if request.url.path.startswith(("/api/v1/auth", "/api/v1/actions")):
        response.headers["Cache-Control"] = "no-store"
    return response
