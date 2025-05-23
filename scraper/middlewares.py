import random
from scrapy.exceptions import NotConfigured
from scrapy.utils.log import logger # Use Scrapy's logger

class CustomRotatingProxyMiddleware:
    def __init__(self, settings):
        self.proxies = settings.getlist('ROTATING_PROXY_LIST')
        if not self.proxies:
            # If the list is empty, this middleware will not be used.
            # However, Scrapy might still log a warning if it's in DOWNLOADER_MIDDLEWARES
            # and no proxies are set. It's better to not even enable it if no proxies.
            # For simplicity here, we let it initialize.
            logger.info("ROTATING_PROXY_LIST is empty. CustomRotatingProxyMiddleware will not assign proxies.")
        else:
            logger.info(f"CustomRotatingProxyMiddleware initialized with {len(self.proxies)} proxies.")

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        if not crawler.settings.getlist('ROTATING_PROXY_LIST'):
            # If ROTATING_PROXY_LIST is empty or not set, don't activate the middleware
            # This prevents errors if it's in settings but no proxies are provided
            raise NotConfigured("ROTATING_PROXY_LIST is not set or empty, disabling CustomRotatingProxyMiddleware.")
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # Don't overwrite proxy if it's already set in request meta
        if 'proxy' in request.meta:
            return

        if self.proxies:
            proxy_address = random.choice(self.proxies)
            request.meta['proxy'] = proxy_address
            logger.debug(f"Using proxy: {proxy_address} for request: {request.url}")
        elif 'proxy' not in request.meta:
            # This part is tricky: if no proxies are set, and no proxy is in meta,
            # then the request proceeds without a proxy.
            # If the intention is to *always* use a proxy from the list,
            # then an error should be raised or the request dropped if self.proxies is empty.
            # For now, it will simply not add a proxy if the list is empty.
            pass
