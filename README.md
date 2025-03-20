# Linebot integrated with Gen AI for Cat Health Care

A Linebot leveraging Generative AI models to answer cat-related health questions. It uses LangChain and LangGraph to maintain conversation context, with all chat histories stored in MongoDB.

## Demo

## Features

- Integrated Linebot Messaging API.
- Responds to cat-related questions using Gemini or OpenAI LLM providers.
- Retains chat history to maintain conversation context.

## Setup

### Development

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m src.app
```

To end your session, run:

```bash
deactivate
```

### Production

```bash
# Install dependencies
pip install -r requirements

# Start the server using Gunicorn
gunicorn --bind 0.0.0.0:3000 src.app:app
```

## Planned Improvements

- Delete or archive chat history after a specified duration.
- Add more detailed logging.
