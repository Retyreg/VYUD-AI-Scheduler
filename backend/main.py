from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

#from services.scheduler import start_scheduler

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    #scheduler = start_scheduler()
    print("🚀 Publisher API запущен с автопостингом")
    yield
    if scheduler:
        scheduler.shutdown()
    print("👋 Publisher API остановлен")

app = FastAPI(
    title="VYUD Publisher API",
    description="API для автопостинга и AI-генерации контента",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
from routers import prompts

#app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
#app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
#app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "VYUD Publisher API", "version": "2.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "scheduler": "running" if scheduler else "stopped"}
