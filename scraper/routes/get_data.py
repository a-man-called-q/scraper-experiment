from blacksheep import HTTPException, ok

from scraper.configs.models import Site
from scraper.schemas import SiteResponse
from scraper.configs.openapidocs import docs
from scraper.routes.routers import base


@docs(
    responses={
        200: "Data fetched successfully",
        404: "No items found",
        500: "Internal Server Error with error message",
    },
    description="Fetch all data from the database.",
    tags=["Data"],
)
@base.get("/get-data/")
async def get_data():
    """
    Get All Data from the database
    """
    items_query = Site.all()
    items_models = await items_query # Execute query to get models
    if not items_models:
        raise HTTPException(status=404, message="No items found")

    site_responses = []
    for site_model in items_models:
        site_responses.append(SiteResponse(
            id=site_model.id,
            title=site_model.title,
            published_date=site_model.published_date,
            keyword=site_model.keyword,
            content=site_model.content,
            masked_url=site_model.masked_url,
            url=site_model.url,
            is_extracted=site_model.is_extracted,
            has_rc_analysis=site_model.has_rc_analysis,
            rc_analysis=site_model.rc_analysis,
            has_sentiment_analysis=site_model.has_sentiment_analysis,
            sentiment_analysis=site_model.sentiment_analysis,
            has_prominent_analysis=site_model.has_prominent_analysis,
            prominent_analysis=site_model.prominent_analysis,
            created_at=site_model.created_at,
            updated_at=site_model.updated_at
        ))
    return ok(site_responses)
