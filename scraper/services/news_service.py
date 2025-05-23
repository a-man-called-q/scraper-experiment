import asyncio
from email.utils import parsedate_to_datetime  # Parses RFC 2822 dates

from gnews import GNews
from googlenewsdecoder import new_decoderv1

from scraper.configs.constants import INTERVAL_TIME, MAX_RESULTS, NEWS_PERIOD
from scraper.configs.models import Site
from scraper.schemas import ResponseJSON, Status
from scraper.libs.logger import logger
from scraper.services.analysis_service import extract_content_site, rc_analysis

# Initialize GNews
news_scraper = GNews(max_results=MAX_RESULTS, period=NEWS_PERIOD)


async def _get_news_real_url_and_content(news: dict[str, str], use_rca: bool, keyword: str) -> None:
    truncated_string = news["url"][:30] + "..." if len(news["url"]) > 30 else news["url"]
    logger.info(f"Getting Real URL from {truncated_string}")
    decoder = await asyncio.to_thread(new_decoderv1, news["url"], interval=INTERVAL_TIME)
    result = decoder["decoded_url"]
    logger.info("Real URL Retrieved")
    site = await extract_content_site(result) # Uses analysis_service
    logger.info("Saving Masked URL and Real URL to Database...")
    await Site.create(
        masked_url=news["url"],
        url=result,
        title=site.title,
        content=site.content,
        keyword=keyword,
        published_date=parsedate_to_datetime(news["published date"]),
    )
    logger.info("Masked URL and Real URL Saved to Database")
    if use_rca:
        await rc_analysis(result) # Uses analysis_service


async def get_news_list(keyword: str, use_rca: bool) -> ResponseJSON:
    try:
        logger.info("Initializing Scraper...")
        logger.info("Scraper Initialized")

        logger.info("Getting News...")
        latest_news = await asyncio.to_thread(news_scraper.get_news, keyword)

        news_count = len(latest_news) if latest_news else 0
        logger.info(f"{news_count} News Retrieved")

        if latest_news:
            tasks = [_get_news_real_url_and_content(news, use_rca, keyword) for news in latest_news]
            await asyncio.gather(*tasks)
        return ResponseJSON(
            status=Status.SUCCESS, message=f"{news_count} News fetched successfully"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        return ResponseJSON(status=Status.ERROR, message=str(e))
