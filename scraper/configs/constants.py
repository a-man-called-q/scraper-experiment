import os

from dotenv import load_dotenv

load_dotenv(override=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGER_FILE_NAME = os.getenv("LOGGER_FILE_NAME", "news_scraper.log")

# Scraper
INTERVAL_TIME = int(os.getenv("INTERVAL_TIME", 5))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 3))
NEWS_PERIOD = os.getenv("NEWS_PERIOD", "7d")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

# Analysis
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEFAULT_RC_ANALYSIS_PROMPT = "Perform a detailed 5W1H analysis of the provided content. Break down the information explicitly into the following categories:\n1. Who: Identify the key individuals, groups, or entities involved.\n2. What: Define the main event, action, or subject matter.\n3. When: Specify the time frame or timeline of relevance.\n4. Where: Determine the location(s) or setting of the events.\n5. Why: Explain the reasons, motivations, or context behind the events.\n6. How: Describe the methods, processes, or means by which the events occurred.\nEnsure the output is concise, structured, and relevant to the content, with no additional commentary or irrelevant information. the provided content url is"
RC_ANALYSIS_PROMPT = os.getenv("RC_ANALYSIS_PROMPT", DEFAULT_RC_ANALYSIS_PROMPT)

DEFAULT_SENTIMENT_ANALYSIS_PROMPT = "Analyze the sentiment (e.g., positive, negative, neutral) of the content at the following URL:"
SENTIMENT_ANALYSIS_PROMPT = os.getenv("SENTIMENT_ANALYSIS_PROMPT", DEFAULT_SENTIMENT_ANALYSIS_PROMPT)

DEFAULT_PROMINENT_ANALYSIS_PROMPT = "Identify and list the prominent details, key entities, and main topics from the content at the following URL:"
PROMINENT_ANALYSIS_PROMPT = os.getenv("PROMINENT_ANALYSIS_PROMPT", DEFAULT_PROMINENT_ANALYSIS_PROMPT)

DEFAULT_EXTRACTING_PROMPT = "Extract the title and content from the given URL and return them as a single-line, valid JSON string, with no surrounding backticks, markdown, or other commentary. The JSON must adhere to the following format: {\"title\": \"Title of the URL, or 'N/A' if unavailable\", \"content\": \"Content of the URL article, or 'N/A' if unavailable\"}. The output must contain only the single-line, valid JSON string. Ensure proper JSON escaping for special characters within the title and content fields (e.g., quotes, backslashes, etc.). Prioritize extracting the most relevant content, focusing on the main article text and excluding navigation, ads, or boilerplate. If the URL points to a non-textual resource (e.g., an image or PDF), return \"N/A\" for both \"title\" and \"content\". Handle potential errors (e.g., network issues, invalid URLs) gracefully and return a valid JSON with \"N/A\" values where necessary."
EXTRACTING_PROMPT = os.getenv("EXTRACTING_PROMPT", DEFAULT_EXTRACTING_PROMPT)
