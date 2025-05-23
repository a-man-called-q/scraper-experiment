from blacksheep import json, HTTPException
from blacksheep.server.routing import FromQueries

from scraper.schemas import Status, NewsRequest
from scraper.configs.openapidocs import docs
from scraper.services.news_service import get_news_list
from scraper.routes.routers import base


@docs(
    responses={200: "News fetched successfully", 500: "Internal Server Error with error message"},
    description="This endpoint will fetch news from Google News based on the keywords provided",
    tags=["News"],
)
@base.get("/get-news/")
async def get_news(request: FromQueries[NewsRequest]):
    """
    Getting news list from Google News

    @param keyword: The keywords to search
    @param use_rca: Use Root Cause Analysis
    """
    result = await get_news_list(request.value.keyword, request.value.use_rca)
    if result.status == Status.ERROR:
        raise HTTPException(500, detail=result.message)
    return json({"message": f"news-result: {result.message}"}, status=200)
