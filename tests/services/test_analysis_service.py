import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest # Make sure pytest is recognized

from scraper.services.analysis_service import extract_content_site, rc_analysis
from scraper.schemas import ResponseContent
# Note: rc_analysis and its dependencies might require more imports later for step 4

@pytest.mark.asyncio
async def test_extract_content_site_success():
    mock_url = "http://example.com/article"
    expected_title = "Test Title"
    expected_content = "Test content."
    
    # Mock the response from model.generate_content
    mock_llm_response = MagicMock()
    # The actual response text needs to be a JSON string as expected by the function
    mock_llm_response.text = json.dumps({"title": expected_title, "content": expected_content})

    # Patch 'model.generate_content' within the analysis_service module
    # It's 'scraper.services.analysis_service.model'
    with patch('scraper.services.analysis_service.model.generate_content', return_value=mock_llm_response) as mock_generate_content:
        # Ensure asyncio.to_thread is handled. Since extract_content_site uses await asyncio.to_thread(model.generate_content, ...),
        # the patching should still work as it replaces the 'model.generate_content' callable before to_thread gets it.
        result = await extract_content_site(mock_url)

        # Assert that the mock was called correctly
        mock_generate_content.assert_called_once()
        # Check the first argument of the call (the prompt string)
        called_prompt_args = mock_generate_content.call_args[0][0]
        assert mock_url in called_prompt_args
        
        # Assert the result
        assert isinstance(result, ResponseContent)
        assert result.title == expected_title
        assert result.content == expected_content

@pytest.mark.asyncio
async def test_rc_analysis_success():
    mock_url = "http://example.com/article_for_rc"
    mock_analysis_text = "This is the RC analysis."

    mock_llm_response = MagicMock()
    mock_llm_response.text = mock_analysis_text

    # Mock database interaction
    # This mock represents the object returned by get_current_data
    mock_db_data_instance = MagicMock()
    mock_db_data_instance.rc_analysis = None # Initial state
    mock_db_data_instance.has_rc_analysis = False
    # Mock the save method on this instance as an AsyncMock
    mock_db_data_instance.save = AsyncMock()


    # Patch model.generate_content
    # Patch get_current_data (it's imported directly in analysis_service from scraper.libs.utils)
    with patch('scraper.services.analysis_service.model.generate_content', return_value=mock_llm_response) as mock_gen_content, \
         patch('scraper.services.analysis_service.get_current_data', return_value=mock_db_data_instance) as mock_get_data:
        # Note: We don't need to patch mock_db_data_instance.save here in the context manager
        # because we've already set it up as an AsyncMock on the instance itself.

        await rc_analysis(mock_url)

        mock_gen_content.assert_called_once()
        # You can add more assertions on the prompt if needed
        # e.g., check if RC_ANALYSIS_PROMPT and mock_url are in mock_gen_content.call_args[0][0]

        mock_get_data.assert_called_once_with(mock_url)
        
        # Assertions on the instance that was (conceptually) modified
        assert mock_db_data_instance.rc_analysis == mock_analysis_text
        assert mock_db_data_instance.has_rc_analysis is True
        mock_db_data_instance.save.assert_awaited_once()
