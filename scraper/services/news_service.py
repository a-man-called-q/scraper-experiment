import asyncio
from email.utils import parsedate_to_datetime

# Removed GNews and googlenewsdecoder imports and related constants
# from gnews import GNews
# from googlenewsdecoder import new_decoderv1
# from scraper.configs.constants import INTERVAL_TIME, MAX_RESULTS, NEWS_PERIOD

import scrapydo
from scraper.spiders.news_spider import NewsSpider # Import the spider

from scraper.configs.models import Site
from scraper.schemas import ResponseJSON, Status
from scraper.libs.logger import logger
from scraper.services.analysis_service import extract_content_site, rc_analysis

# Initialize scrapydo
# This should ideally be called once when the application starts.
# Placing it at module level ensures it's run when the module is imported.
try:
    scrapydo.setup()
    logger.info("Scrapydo setup successful.")
except RuntimeError as e:
    if "reactor already installed" in str(e).lower():
        logger.info("Scrapydo reactor already installed.")
    else:
        logger.error(f"Scrapydo setup failed with an unexpected RuntimeError: {e}", exc_info=True)
        # Depending on the application's fault tolerance, you might re-raise or handle differently
        raise
except Exception as e:
    logger.error(f"An unexpected error occurred during scrapydo.setup(): {e}", exc_info=True)
    # Handle or re-raise as appropriate for your application's error handling strategy
    raise


# Removed global GNews instance:
# news_scraper = GNews(max_results=MAX_RESULTS, period=NEWS_PERIOD)


async def _process_single_news_item(news_item: dict, use_rca: bool, keyword_from_request: str) -> None:
    '''Helper function to process each news item from Scrapy.'''
    try:
        real_url = news_item.get('real_url')
        google_news_url = news_item.get('google_news_url')
        spider_title = news_item.get('title', 'N/A') # Title from spider
        publication_date_str = news_item.get('publication_date')
        # keyword_from_spider = news_item.get('keyword') # Spider also includes keyword

        if not real_url or not publication_date_str:
            logger.warning(f"Missing real_url or publication_date for item: '{spider_title}'. Google URL: '{google_news_url}'. Skipping.")
            return

        logger.info(f"Processing article: '{spider_title}' from URL: {real_url}")

        # 1. Extract content using analysis_service
        site_data = await extract_content_site(real_url)
        if not site_data or not site_data.content: # Ensure content is also present
            logger.warning(f"Could not extract content or content is empty for {real_url}. Title: '{site_data.title if site_data else 'N/A'}'. Skipping.")
            return

        # 2. Parse publication date
        try:
            parsed_published_date = parsedate_to_datetime(publication_date_str)
        except Exception as e:
            logger.error(f"Error parsing publication date '{publication_date_str}' for {real_url}: {e}. Skipping.")
            return

        # 3. Save to database
        final_title = site_data.title if site_data.title else spider_title # Prefer title from extraction, fallback to spider's
        logger.info(f"Saving article to database: '{final_title}' (URL: {real_url})")
        await Site.create(
            masked_url=google_news_url,
            url=real_url,
            title=final_title,
            content=site_data.content,
            keyword=keyword_from_request, # Using the keyword passed to get_news_list
            published_date=parsed_published_date,
        )
        logger.info(f"Article saved: '{final_title}'")

        # 4. Perform RCA if requested
        if use_rca:
            logger.info(f"Performing RCA for {real_url}")
            await rc_analysis(real_url)
            logger.info(f"RCA completed for {real_url}")

    except Exception as e:
        logger.error(f"Error processing news item '{news_item.get('title', 'N/A')}' (URL: {news_item.get('real_url')}): {e}", exc_info=True)


async def get_news_list(keyword: str, use_rca: bool) -> ResponseJSON:
    try:
        logger.info(f"Starting news fetch for keyword: '{keyword}' using Scrapy with scrapydo")

        logger.info("Invoking Scrapy spider via asyncio.to_thread...")
        try:
            # Pass spider class and keyword argument
            # scrapydo.run_spider is blocking, so it's wrapped in asyncio.to_thread
            scraped_items = await asyncio.to_thread(scrapydo.run_spider, NewsSpider, keyword=keyword)
        except Exception as e:
            logger.error(f"Scrapy spider execution via scrapydo failed for keyword '{keyword}': {e}", exc_info=True)
            return ResponseJSON(status=Status.ERROR, message=f"Scraper execution error: {e}")

        news_count = len(scraped_items) if scraped_items else 0
        logger.info(f"{news_count} news items retrieved by Scrapy spider for keyword '{keyword}'.")

        if scraped_items:
            # Create a list of tasks for asyncio.gather
            tasks = [_process_single_news_item(news_item, use_rca, keyword) for news_item in scraped_items if news_item]
            if tasks: # Ensure there are tasks to run
                await asyncio.gather(*tasks)
                logger.info(f"Finished processing all {len(tasks)} valid news items for keyword '{keyword}'.")
            else:
                logger.info(f"No valid news items with all required fields found for keyword '{keyword}'.")
        else:
            logger.info(f"No news items to process for keyword '{keyword}'.")

        return ResponseJSON(
            status=Status.SUCCESS, message=f"{news_count} News items initially retrieved, processed valid ones. Keyword: '{keyword}'"
        )
    except Exception as e:
        logger.error(f"Error in get_news_list for keyword '{keyword}': {e}", exc_info=True)
        return ResponseJSON(status=Status.ERROR, message=f"An unexpected error occurred: {e}")
