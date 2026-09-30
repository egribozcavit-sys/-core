import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.engine.core import engine as transaction_engine
from app.middleware import rate_limit_middleware, logging_middleware
from app.api import auth, users, accounts, transactions

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("paycore")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PayCore starting up...")
    Base.metadata.create_all(bind=engine)
    await transaction_engine.connect()
    asyncio.create_task(transaction_engine.start_processing())
    logger.info("PayCore started successfully")
    yield
    logger.info("PayCore shutting down...")
    await transaction_engine.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)
app.middleware("http")(rate_limit_middleware)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
