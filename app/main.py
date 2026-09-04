from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import models
from app.routers import auth, personnel, officer, chat, status

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(personnel.router)
app.include_router(officer.router)
app.include_router(chat.router)
app.include_router(status.router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health")
def health():
    return {"status": "healthy"}
