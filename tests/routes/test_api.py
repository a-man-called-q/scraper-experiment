from unittest.mock import patch, AsyncMock
import pytest
from blacksheep.testing import TestClient
# from blacksheep import Application # Not strictly needed if using TestClient(app)
from scraper.main import create_app # To get the app instance
# from scraper.schemas import SiteResponse # Not strictly needed for these tests as we check raw JSON
from scraper.configs.models import Site # To mock its methods
from datetime import datetime

@pytest.mark.asyncio
async def test_get_data_success_empty():
    # Create a TestClient instance.
    app = create_app() 
    client = TestClient(app)

    # Mock the Site.all() method to return an empty list (async result)
    # The path to patch is where Site is defined and 'all' is accessed.
    with patch('scraper.configs.models.Site.all', new_callable=AsyncMock, return_value=[]) as mock_site_all:
        response = await client.get("/get-data/")

        assert response.status_code == 200 # Expect 200 OK for an empty list as per current implementation
        json_response = response.json()
        assert json_response == [] # Expect an empty list
        mock_site_all.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_data_success_with_data():
    app = create_app()
    client = TestClient(app)

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
