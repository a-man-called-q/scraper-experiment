import asyncio
from blacksheep.server.routing import FromQueries

from scraper.configs.openapidocs import docs
from scraper.services.analysis_service import prominent_analysis, rc_analysis, sentiment_analysis
from scraper.libs.utils import get_current_data
from scraper.routes.routers import base
from scraper.schemas import URLRequest


@docs(
    responses={200: "Analysis Done Successfully", 500: "Internal Server Error with error message"},
    description="This endpoint will perform Root Cause Analysis (5W1H), Sentiment Analysis, and Prominent Analysis using Google's GEMINI API ",
    tags=["Analysis"],
)
@base.route("/gen-all-analysis")
async def gen_all_analysis(request: FromQueries[URLRequest]):
    """
    Getting analysis from all analysis functions available.

    @param url: The URL that will be used for analysis.
    """
    validated_url = str(request.value.url)
    await asyncio.gather(
        rc_analysis(validated_url),
        sentiment_analysis(validated_url),
        prominent_analysis(validated_url)
    )
    current_data = await get_current_data(validated_url)
    if current_data is not None:
        return {
            validated_url: current_data.url,
            "masked-url": current_data.masked_url,
            "rc-analysis": current_data.rc_analysis,
            "sentiment-analysis": current_data.sentiment_analysis,
            "prominent_analysis": current_data.prominent_analysis,
        }


@docs(
    responses={200: "Analysis Done Successfully", 500: "Internal Server Error with error message"},
    description="This endpoint will perform Root Cause Analysis (5W1H) using Google's GEMINI API ",
    tags=["Analysis"],
)
@base.route("/gen-rc-analysis")
async def gen_rc_analysis(request: FromQueries[URLRequest]):
    """
    Getting Root Cause Analysis.

    @param url: The URL that will be used for analysis.
    """
    validated_url = str(request.value.url)
    # The rc_analysis function is already async and handles its own threading with to_thread
    # So, direct await is appropriate here.
    await rc_analysis(validated_url)
    current_data = await get_current_data(validated_url)
    if current_data is not None:
        return {
            validated_url: current_data.url,
            "masked-url": current_data.masked_url,
            "rc-analysis": current_data.rc_analysis,
        }
