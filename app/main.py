from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .routers import invoices


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Demo-friendly bootstrap; swap for Alembic migrations in real deployments.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Invoice Engine",
    description=(
        "A small invoicing service with the rules that matter in the real world: "
        "concurrency-safe sequential numbering, immutable issued documents, "
        "auditable cancellations, and PDF output."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(invoices.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
