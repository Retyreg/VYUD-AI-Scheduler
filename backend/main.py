import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,https://publisher.vyud.tech"
    ).split(",")
    if o.strip()
]
if not ALLOWED_ORIGINS:
    logger.warning("ALLOWED_ORIGINS is empty — defaulting to localhost:3000")
    ALLOWED_ORIGINS = ["http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.scheduler import start_scheduler, stop_scheduler

    logger.info("Starting VYUD Publisher API v2.1.0")
    await start_scheduler()
    yield
    await stop_scheduler()
    logger.info("VYUD Publisher API stopped")


app = FastAPI(title="VYUD Publisher API", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import accounts, ai, analytics, auth, posts, prompts  # noqa: E402 — env must be loaded first via load_dotenv() above

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.1.0"}
