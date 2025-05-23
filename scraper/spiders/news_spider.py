import scrapy
from urllib.parse import urlencode, urlparse, parse_qs

class NewsSpider(scrapy.Spider):
    name = "news_google"
    # It's good practice to also allow the domains of common redirect services if any are used by Google News,
    # or the domains of the actual news sources, though the latter can be very broad.
    # For now, focusing on news.google.com and letting Scrapy handle redirects to final destinations.
    allowed_domains = ["news.google.com"]

    custom_settings = {
        'ROBOTSTXT_OBEY': False, # Required to fetch search results, use responsibly

        # Throttling / Politeness
        'DOWNLOAD_DELAY': 2,  # Time in seconds between requests
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0, # Try to keep it low and respectful
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2, # Max concurrent requests to any single domain
        'CONCURRENT_REQUESTS': 4, # Max concurrent requests overall

        # User-Agent Rotation
        # Scrapy will pick from this list if the UserAgentMiddleware is active (default)
        'USER_AGENTS': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0',
        ],

        # Basic Proxy Setup (placeholder for a list of proxies)
        'ROTATING_PROXY_LIST': [],

        # DOWNLOADER_MIDDLEWARES will be populated later if specific middleware for proxies is added.
        # Scrapy's default UserAgentMiddleware will use the USER_AGENTS list.
        # Scrapy's default HttpProxyMiddleware is also active.
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.CustomRotatingProxyMiddleware': 610,
            # Scrapy's UserAgentMiddleware (default priority 500) will handle USER_AGENTS.
            # Scrapy's HttpProxyMiddleware (default priority 750) will use request.meta['proxy'] if set by our middleware.
        },
    }

    def __init__(self, keyword=None, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        if not keyword:
            raise ValueError("Keyword must be provided for NewsSpider")
        self.keyword = keyword
        # Using a slightly different URL structure that's commonly seen and often more stable.
        # hl=en&gl=US ensures results are in English for the US.
        self.start_urls = [f"https://news.google.com/rss/search?q={urlencode({'q': keyword})[2:]}&hl=en&gl=US&ceid=US:en"]
        self.logger.info(f"Spider initialized for keyword: '{keyword}', start URL: {self.start_urls[0]}")

    def parse(self, response):
        # This method parses the RSS feed from Google News.
        # RSS feeds have a more structured and stable format than HTML pages.
        self.logger.info(f"Parsing RSS feed from {response.url}")

        # RSS items are usually within <item> tags
        items = response.xpath('//item')
        self.logger.info(f"Found {len(items)} items in RSS feed.")

        if not items:
            self.logger.warning(f"No items found in RSS feed for keyword '{self.keyword}'. Check the start URL or Google News RSS format.")
            return

        for item in items:
            title = item.xpath('title/text()').get()
            # The <link> tag in Google News RSS usually points to an intermediate Google News URL
            google_news_url = item.xpath('link/text()').get()
            # The <pubDate> tag contains the publication date
            publication_date_str = item.xpath('pubDate/text()').get()

            self.logger.info(f"Extracted from RSS: Title='{title}', GoogleLink='{google_news_url}', PubDate='{publication_date_str}'")

            if google_news_url:
                # The link from RSS is what we need to "decode" or follow to get the real URL.
                # Scrapy's Request will handle following this link.
                # We pass the extracted data via meta.
                yield scrapy.Request(
                    google_news_url,
                    callback=self.parse_article,
                    meta={
                        'title': title,
                        'publication_date': publication_date_str,
                        'google_url': google_news_url # This is the URL from the RSS <link>
                    }
                )
            else:
                self.logger.warning(f"Could not extract google_news_url for title: '{title}'")

    def parse_article(self, response):
        # This method is the callback after following the Google News link from the RSS feed.
        # response.url should be the real article URL.
        # response.request.meta contains the data passed from the parse method.
        title = response.request.meta['title']
        publication_date = response.request.meta['publication_date']
        google_url = response.request.meta['google_url'] # The intermediate Google News URL from RSS
        real_url = response.url # The final URL after redirects

        self.logger.info(f"Successfully resolved real URL: '{real_url}' for article: '{title}'")

        yield {
            'title': title,
            'google_news_url': google_url, # This is the intermediate google news link
            'real_url': real_url,          # This is the actual article URL
            'publication_date': publication_date,
            'keyword': self.keyword
        }
