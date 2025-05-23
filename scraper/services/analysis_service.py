import asyncio
import json

from google import generativeai

from scraper.configs.constants import (
    AI_MODEL,
    EXTRACTING_PROMPT,
    GEMINI_API_KEY,
    PROMINENT_ANALYSIS_PROMPT,
    RC_ANALYSIS_PROMPT,
    SENTIMENT_ANALYSIS_PROMPT,
)
from scraper.schemas import ResponseContent
from scraper.libs.logger import logger
from scraper.libs.utils import get_current_data

# Initialize the generative AI model
generativeai.configure(api_key=GEMINI_API_KEY)
model = generativeai.GenerativeModel(AI_MODEL)


async def _generate_analysis(
    url: str, analysis_type: str, prompt: str | None, analysis_field: str, has_analysis_field: str
):
    logger.info(f"Preparing to generate {analysis_type} for {url}")
    response = await asyncio.to_thread(model.generate_content, f"{prompt} {url}")
    logger.info(f"{analysis_type} Generated")
    current_data = await get_current_data(url)
    if current_data:
        logger.info(f"Saving {analysis_type} to Database...")
        setattr(current_data, analysis_field, response.text)
        setattr(current_data, has_analysis_field, True)
        await current_data.save()
        logger.info(f"{analysis_type} Saved to Database")
    else:
        logger.error("URL not found in Database, please re-check the URL")


async def rc_analysis(url: str):
    await _generate_analysis(
        url, "Root Cause Analysis", RC_ANALYSIS_PROMPT, "rc_analysis", "has_rc_analysis"
    )


async def sentiment_analysis(url: str):
    await _generate_analysis(
        url,
        "Sentiment Analysis",
        SENTIMENT_ANALYSIS_PROMPT,
        "sentiment_analysis",
        "has_sentiment_analysis",
    )


async def prominent_analysis(url: str):
    await _generate_analysis(
        url,
        "Prominent Analysis",
        PROMINENT_ANALYSIS_PROMPT,
        "prominent_analysis",
        "has_prominent_analysis",
    )


async def extract_content_site(url: str):
    logger.info(f"Preparing to extract content for {url}")
    logger.info(f"using prompt: {EXTRACTING_PROMPT}")
    response = await asyncio.to_thread(model.generate_content, f"{EXTRACTING_PROMPT} {url}")
    logger.info("Content Extracted.")
    logger.info(response.text.strip("```json").strip("```"))
    return ResponseContent(**json.loads(response.text.strip("```json").strip("```")))
