import os
import sys
from dotenv import load_dotenv
import logging

# import json
from flask import Flask, request

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.helpers.error_handlers import handle_error
from src.genai.get_ai_response import get_ai_response

# ==================================================================
load_dotenv()
app = Flask(__name__)

# LINE configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
lineConfiguration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
lineHandler = WebhookHandler(LINE_CHANNEL_SECRET)

# Setup logging
app.logger.setLevel(logging.INFO)
if not app.logger.handlers:
    app.logger.addHandler(logging.StreamHandler(sys.stdout))


# ==================================================================
@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook():
    # Get X-Line-Signature header
    signature = request.headers.get("X-Line-Signature")

    # Get request body
    body = request.get_data(as_text=True)
    # app.logger.info(f"Request body: {body}")

    x_forwarded = request.environ.get("HTTP_X_FORWARDED_FOR", "")
    ip_addr = request.environ.get("remote_addr", "")
    app.logger.info(f"HTTP_X_FORWARDED_FOR: {x_forwarded} / remote_addr: {ip_addr}")

    try:
        lineHandler.handle(body, signature)
    except InvalidSignatureError as e:
        return handle_error(
            400, e, "Invalid signature. Please check your channel access token or channel secret."
        )
    except Exception as e:
        return handle_error(500, e, "Unknown error occurred.")

    return "OK"


@lineHandler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # app.logger.info(f"event: {event}")
    sourceType = event.source.type
    userId = event.source.user_id

    # Get mention flag
    mentionees = event.message.mention.mentionees if event.message.mention else []
    mention = any(getattr(mentionee, "is_self", False) for mentionee in mentionees)
    if sourceType == "user" or (sourceType == "group" and mention):
        app.logger.info(f"event: {event}")
        # responseMessage = f"你說的是：[ {event.message.text} ]"
        responseMessage = get_ai_response(event.message.text, userId)
        with ApiClient(lineConfiguration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token, messages=[TextMessage(text=responseMessage)]
                )
            )


# For local testing
# @app.route("/chat", methods=["POST"])
# def chat():
#     try:
#         body = request.get_json()
#         app.logger.info(f"Request body: {body}")

#         user_input = body["user_input"]
#         user_id = body["user_id"]

#         result = get_ai_response(user_input, user_id)
#     except Exception as e:
#         return handle_error(500, e, "Unknown error occurred.")

#     return result


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
