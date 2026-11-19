import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import settings
from api.engine import SearchEngine
from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("yt-rag-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up YouTube Knowledge Explorer API...")
    app.state.search_engine = SearchEngine()
    logger.info("Search engine ready to accept requests.")
    yield
    logger.info("Shutting down YouTube Knowledge Explorer API...")


app = FastAPI(
    title="YouTube Knowledge Explorer API",
    description="FastAPI service for querying YouTube transcript chunks using hybrid search and cross-encoder reranking.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request parameters.")
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    detailed_message = f"{field}: {msg}" if field else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": detailed_message
            }
        }
    )


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
