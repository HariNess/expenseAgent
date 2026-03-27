from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from backend.models.database import create_tables, seed_employees
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.approvals import router as approvals_router

app = FastAPI(
    title="NessExpense Agent API",
    description="Intelligent expense management system with multi-agent AI",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080","https://8080-ffafdcfdafeaebcfabccbffcdeecac.premiumproject.examly.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(approvals_router)


@app.on_event("startup")
async def startup():
    create_tables()
    seed_employees()
    print("✅ NessExpense Agent API started")
    print(f"📡 Running on http://localhost:{os.getenv('APP_PORT', 8081)}")


@app.get("/")
async def root():
    return {
        "name": "NessExpense Agent",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 8081)),
        reload=True
    )
