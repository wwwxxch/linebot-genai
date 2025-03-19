import os
from dotenv import load_dotenv
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# ! logging! to be reviewed!
import logging

load_dotenv(override=True)


class LLMProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


def llm_provider_factory():
    try:
        llm_provider = os.getenv("LLM_PROVIDER", LLMProvider.GEMINI.value)
        if llm_provider == LLMProvider.OPENAI.value:
            return ChatOpenAI(model="gpt-4o-mini")
        elif llm_provider == LLMProvider.GEMINI.value:
            return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    except Exception as e:
        logging.error(f"Error creating LLM provider: {e}")
        raise e
