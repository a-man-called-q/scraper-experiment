from unittest.mock import patch, AsyncMock
import pytest
from blacksheep.testing import TestClient
# from blacksheep import Application # Not strictly needed if using TestClient(app)
from scraper.main import create_app # To get the app instance
# from scraper.schemas import SiteResponse # Not strictly needed for these tests as we check raw JSON
from scraper.configs.models import Site # To mock its methods
from datetime import datetime

from scraper.services.news_service import NewsSpider # For type hinting if needed, not strictly for patching path
from scraper.schemas import ResponseContent # For creating mock return for extract_content_site


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.mark.asyncio
async def test_get_data_success_empty(client): # Use the client fixture
    # Mock the Site.all() method to return an empty list (async result)
    # The path to patch is where Site is defined and 'all' is accessed.
    with patch('scraper.configs.models.Site.all', new_callable=AsyncMock, return_value=[]) as mock_site_all:
        response = await client.get("/get-data/")

        assert response.status_code == 200 # Expect 200 OK for an empty list as per current implementation
        json_response = response.json()
        assert json_response == [] # Expect an empty list
        mock_site_all.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_data_success_with_data(client): # Use the client fixture
    # Prepare mock Site model instances (simplified, not full Tortoise models)
    # These are more like dictionaries or simple objects for assertion comparison.
    # The actual Site() instantiation is not strictly needed for the mock_site_instance
    # as long as it has the attributes that the SiteResponse schema will access.
    # For simplicity and direct attribute access matching SiteResponse fields:
    current_time = datetime.utcnow()
    mock_site_data = {
        "id": 1, "title": "Test Title 1", "published_date": current_time, "keyword": "test1",
        "content": "Content 1", "masked_url": "masked1.com", "url": "real1.com",
        "is_extracted": True, "has_rc_analysis": False, "rc_analysis": None,
        "has_sentiment_analysis": False, "sentiment_analysis": None,
        "has_prominent_analysis": False, "prominent_analysis": None,
        "created_at": current_time, "updated_at": current_time
    }
    
    # Create a mock object that behaves like a Site model instance for the purpose of this test
    mock_site_instance_1 = Site(**mock_site_data)


    # Mock Site.all() to return a list containing our mock instance
    with patch('scraper.configs.models.Site.all', new_callable=AsyncMock, return_value=[mock_site_instance_1]) as mock_site_all:
        response = await client.get("/get-data/")

        assert response.status_code == 200
        json_response = response.json()
        
        assert len(json_response) == 1
        item = json_response[0]
        assert item['id'] == mock_site_instance_1.id
        assert item['title'] == mock_site_instance_1.title
        assert item['url'] == mock_site_instance_1.url
        assert item['keyword'] == mock_site_instance_1.keyword
        assert item['content'] == mock_site_instance_1.content
        # Timestamps need careful handling due to potential microsecond differences in serialization.
        # Compare ISO format strings up to seconds if direct datetime object comparison is tricky.
        assert datetime.fromisoformat(item['published_date']).replace(tzinfo=None) == mock_site_instance_1.published_date.replace(tzinfo=None)
        assert datetime.fromisoformat(item['created_at']).replace(tzinfo=None) == mock_site_instance_1.created_at.replace(tzinfo=None)
        assert datetime.fromisoformat(item['updated_at']).replace(tzinfo=None) == mock_site_instance_1.updated_at.replace(tzinfo=None)


        mock_site_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_news_success(client): # Assuming 'client' fixture is defined as in other tests
    keyword = "testkeyword"
    use_rca = False

    # Mock data from Scrapy spider
    mock_spider_item_1 = {
        'title': 'Spider Title 1',
        'google_news_url': 'http://news.google.com/rss/item1',
        'real_url': 'http://example.com/realarticle1',
        'publication_date': 'Tue, 20 Feb 2024 00:00:00 GMT', # Example RFC 2822 date
        'keyword': keyword
    }
    mock_scraped_items = [mock_spider_item_1]

    # Mock for extract_content_site
    mock_site_content = ResponseContent(title="Extracted Title 1", content="Extracted content 1.")

    # Patch the dependencies in news_service
    # The key is to patch where the names are looked up.
    # Note: The actual path to NewsSpider for the assertion is scraper.spiders.news_spider.NewsSpider
    # but for patching asyncio.to_thread, we are just checking the argument passed to it.
    with patch('scraper.services.news_service.asyncio.to_thread', new_callable=AsyncMock, return_value=mock_scraped_items) as mock_run_spider_thread, \
         patch('scraper.services.news_service.extract_content_site', new_callable=AsyncMock, return_value=mock_site_content) as mock_extract_content, \
         patch('scraper.services.news_service.Site.create', new_callable=AsyncMock) as mock_site_create, \
         patch('scraper.services.news_service.rc_analysis', new_callable=AsyncMock) as mock_rca:

        response = await client.get(f"/get-news/?keyword={keyword}&use_rca={use_rca}")

        assert response.status_code == 200
        json_response = response.json()
        # Based on current get_news_list route, the message is:
        # f"{news_count} News items initially retrieved, processed valid ones. Keyword: '{keyword}'"
        # We need to align this with the actual message format from news_service.py
        # From news_service.py: ResponseJSON(status=Status.SUCCESS, message=f"{news_count} News items initially retrieved, processed valid ones. Keyword: '{keyword}'")
        assert json_response['status'] == 'SUCCESS'
        assert json_response['message'] == f"{len(mock_scraped_items)} News items initially retrieved, processed valid ones. Keyword: '{keyword}'"


        # Assert that our mocks were called
        mock_run_spider_thread.assert_called_once()
        # The first argument to to_thread is scrapydo.run_spider, then NewsSpider, then keyword
        # We need to import the actual NewsSpider class for this comparison
        from scraper.spiders.news_spider import NewsSpider as ActualNewsSpider
        assert mock_run_spider_thread.call_args[0][0].__name__ == 'run_spider' # Check it's scrapydo.run_spider
        assert mock_run_spider_thread.call_args[0][1] == ActualNewsSpider # Check spider class
        assert mock_run_spider_thread.call_args[1]['keyword'] == keyword # Check keyword arg

        mock_extract_content.assert_called_once_with(mock_spider_item_1['real_url'])
        
        mock_site_create.assert_called_once()
        # Detailed check for Site.create arguments:
        create_args = mock_site_create.call_args[1] # .kwargs
        assert create_args['masked_url'] == mock_spider_item_1['google_news_url']
        assert create_args['url'] == mock_spider_item_1['real_url']
        assert create_args['title'] == mock_site_content.title
        assert create_args['content'] == mock_site_content.content
        assert create_args['keyword'] == keyword
        # publication_date is parsed, so direct comparison might be tricky. Check it's a datetime.
        assert isinstance(create_args['published_date'], datetime)

        if use_rca:
            mock_rca.assert_called_once_with(mock_spider_item_1['real_url'])
        else:
            mock_rca.assert_not_called()

@pytest.mark.asyncio
async def test_get_news_no_results_from_spider(client):
    keyword = "testkeyword_no_results"
    use_rca = False
    mock_scraped_items = [] # Spider returns nothing

    with patch('scraper.services.news_service.asyncio.to_thread', new_callable=AsyncMock, return_value=mock_scraped_items) as mock_run_spider_thread, \
         patch('scraper.services.news_service.extract_content_site', new_callable=AsyncMock) as mock_extract_content, \
         patch('scraper.services.news_service.Site.create', new_callable=AsyncMock) as mock_site_create:

        response = await client.get(f"/get-news/?keyword={keyword}&use_rca={use_rca}")

        assert response.status_code == 200 # Expect 200 OK
        json_response = response.json()
        # Message from news_service.py: f"{news_count} News items initially retrieved, processed valid ones. Keyword: '{keyword}'"
        assert json_response['status'] == 'SUCCESS'
        assert json_response['message'] == f"0 News items initially retrieved, processed valid ones. Keyword: '{keyword}'"
        
        mock_run_spider_thread.assert_called_once()
        mock_extract_content.assert_not_called()
        mock_site_create.assert_not_called()
            
@pytest.mark.asyncio
async def test_get_news_spider_execution_error(client):
    keyword = "testkeyword_spider_error"
    use_rca = False

    # Simulate an error during spider execution (within asyncio.to_thread)
    with patch('scraper.services.news_service.asyncio.to_thread', new_callable=AsyncMock, side_effect=Exception("Spider Boom!")) as mock_run_spider_thread:
        response = await client.get(f"/get-news/?keyword={keyword}&use_rca={use_rca}")

        # The route in main.py catches Exception and returns a generic 500 if not HTTPException
        # The news_service.py get_news_list returns ResponseJSON with status ERROR
        # The main.py route then checks this result.status
        # if result.status == Status.ERROR: raise HTTPException(status_code=500, detail=result.message)

        assert response.status_code == 500 
        json_response = response.json()
        # news_service.py returns: message=f"Scraper execution error: {e}"
        assert "Scraper execution error: Spider Boom!" in json_response['detail']
        mock_run_spider_thread.assert_called_once()

@pytest.mark.asyncio
async def test_get_news_processing_error_for_item(client):
    keyword = "testkeyword_item_error"
    use_rca = False
    mock_spider_item_1 = {
        'title': 'Good Spider Title 1', 'google_news_url': 'http://news.google.com/rss/item1', 
        'real_url': 'http://example.com/realarticle1', 'publication_date': 'Tue, 20 Feb 2024 00:00:00 GMT', 'keyword': keyword
    }
    mock_spider_item_error = { # This item will cause an error
        'title': 'Bad Spider Item', 'google_news_url': 'http://news.google.com/rss/item_error',
        'real_url': 'http://example.com/realarticle_error', 'publication_date': 'Wed, 21 Feb 2024 00:00:00 GMT', 'keyword': keyword
    }
    mock_scraped_items = [mock_spider_item_1, mock_spider_item_error]

    mock_site_content_good = ResponseContent(title="Extracted Good Title", content="Good content.")
    
    # extract_content_site will fail for the second item
    async def extract_side_effect(url):
        if url == mock_spider_item_error['real_url']:
            # Option 2: return None (as per current _process_single_news_item handling)
            return None 
        return mock_site_content_good

    with patch('scraper.services.news_service.asyncio.to_thread', new_callable=AsyncMock, return_value=mock_scraped_items) as mock_run_spider_thread, \
         patch('scraper.services.news_service.extract_content_site', new_callable=AsyncMock, side_effect=extract_side_effect) as mock_extract_content, \
         patch('scraper.services.news_service.Site.create', new_callable=AsyncMock) as mock_site_create:

        response = await client.get(f"/get-news/?keyword={keyword}&use_rca={use_rca}")

        assert response.status_code == 200 # The overall request is still 200
        json_response = response.json()
        # _process_single_news_item logs errors but doesn't make get_news_list fail fully.
        # The message reflects total items *initially retrieved*.
        assert json_response['status'] == 'SUCCESS'
        assert json_response['message'] == f"{len(mock_scraped_items)} News items initially retrieved, processed valid ones. Keyword: '{keyword}'"


        mock_run_spider_thread.assert_called_once() # Corrected from .assert_called_once
        assert mock_extract_content.call_count == len(mock_scraped_items)
        # Site.create should only be called for the good item
        mock_site_create.assert_called_once() 
        create_args = mock_site_create.call_args[1]
        assert create_args['url'] == mock_spider_item_1['real_url']
