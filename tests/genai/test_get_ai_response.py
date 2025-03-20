import pytest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime
from src.genai.get_ai_response import (
    LLMProvider,
    llm_provider_factory,
    create_cat_health_chain,
    get_ai_response,
)


# Testing llm_provider_factory
@pytest.fixture
def reset_env_var():
    """Save it and restore env var after testing"""
    old_env = os.environ.get("LLM_PROVIDER", None)
    yield
    if old_env is not None:
        os.environ["LLM_PROVIDER"] = old_env
    else:
        if "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]


def test_default_provider(reset_env_var):
    """If no default value provided, return Gemini as the LLM Provider"""
    if "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]

    with patch("src.genai.get_ai_response.ChatGoogleGenerativeAI") as mock_gemini:
        mock_gemini.return_value = MagicMock()

        result = llm_provider_factory()

        mock_gemini.assert_called_once_with(model="gemini-2.0-flash")
        assert isinstance(result, MagicMock)


def test_openai_provider(reset_env_var):
    """When LLM_PROVIDER = openai, return OpenAI as the LLM Provider"""
    os.environ["LLM_PROVIDER"] = LLMProvider.OPENAI.value

    with patch("src.genai.get_ai_response.ChatOpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()

        result = llm_provider_factory()

        mock_openai.assert_called_once_with(model="gpt-4o-mini")
        assert isinstance(result, MagicMock)


def test_gemini_provider(reset_env_var):
    """When LLM_PROVIDER = gemini, return Gemini as the LLM Provider"""
    os.environ["LLM_PROVIDER"] = LLMProvider.GEMINI.value

    with patch("src.genai.get_ai_response.ChatGoogleGenerativeAI") as mock_gemini:
        mock_gemini.return_value = MagicMock()

        result = llm_provider_factory()

        mock_gemini.assert_called_once_with(model="gemini-2.0-flash")
        assert isinstance(result, MagicMock)


def test_provider_exception(reset_env_var):
    """When error occured during creating LLM Provider"""
    os.environ["LLM_PROVIDER"] = LLMProvider.GEMINI.value

    with patch("src.genai.get_ai_response.ChatGoogleGenerativeAI") as mock_gemini:
        mock_gemini.side_effect = Exception("Test exception")

        with patch("logging.error") as mock_logging:
            with pytest.raises(Exception) as excinfo:
                llm_provider_factory()

            assert "Test exception" in str(excinfo.value)
            mock_logging.assert_called_once()
            assert "Error creating LLM provider" in mock_logging.call_args[0][0]


# Testing create_cat_health_chain
@pytest.fixture
def mock_cat_data():
    with patch(
        "src.genai.get_ai_response.cat_data",
        {
            "name": "Mochi",
            "birth_year": 2020,
            "sex": "公",
            "breed": "混種貓",
            "medical_history": ["結紮", "預防針"],
        },
    ):
        yield
