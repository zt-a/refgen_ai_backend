import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database import init_db
from src.auth.router import router as auth_router
from src.routes.profile import router as profile_router
from src.routes.essay import router as essay_router
from src.routes.refprint import router as refprint_router
from src.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(prefix=settings.api_v1_prefix, router=auth_router)
app.include_router(prefix=settings.api_v1_prefix, router=profile_router)
app.include_router(prefix=settings.api_v1_prefix, router=essay_router)
app.include_router(prefix=settings.api_v1_prefix, router=refprint_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
