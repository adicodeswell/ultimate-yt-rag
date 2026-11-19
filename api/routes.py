import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from api.config import settings
from api.schema import (
    SearchRequest,
    SearchResponse,
    HealthResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    tags=["Health"]
)
async def health_check():
    return HealthResponse(
        status="ok",
        collection=settings.COLLECTION_NAME
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query or parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Search technical concepts",
    tags=["Search"]
)
async def search_endpoint(body: SearchRequest, request: Request):
    clean_query = body.query.strip()
    if not clean_query:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_QUERY",
                    "message": "Enter a search query."
                }
            }
        )

    search_engine = getattr(request.app.state, "search_engine", None)
    if search_engine is None:
        logger.error("SearchEngine is not initialized on app.state")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Search engine is not ready. Please try again shortly."
                }
            }
        )

    try:
        results = search_engine.search(
            query=clean_query,
            domain=body.domain,
            limit=body.limit
        )
        return SearchResponse(
            query=clean_query,
            results=results
        )
    except Exception as exc:
        logger.exception("Error executing search for query '%s': %s", clean_query, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "SEARCH_ERROR",
                    "message": "An unexpected error occurred during search. Please try again."
                }
            }
        )
