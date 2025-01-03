from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestValidationError,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.metrics import MetricUnit

from botocore.exceptions import ClientError

from models import Messages, Message, Event, ContentItem
from chatbot_client import Chatbot

import os

app = APIGatewayRestResolver(enable_validation=True)
tracer = Tracer()
logger = Logger()

MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]

chatbot_client = Chatbot(MODEL_ID, DDB_TABLE_NAME)

@app.exception_handler(RequestValidationError)
def handle_validation_error(ex: RequestValidationError):
    logger.error(
        "Request failed validation", path=app.current_event.path, errors=ex.errors()
    )

    return Response(
        status_code=422,
        content_type=content_types.APPLICATION_JSON,
        body="Invalid data",
    )


@app.post("/chat")
@tracer.capture_method
def chat(event: Event):
    system_prompts = [
        {
            "text": "You are a chatbot that responses to user prompts, if you don't know an answer say I'm sorry I don't know.  Ensure responses are accurate and not offensive"
        }
    ]

    try:
        messages = Messages.from_message_list(
            session_id=event.session_id, messages=event.messages
        )

        content = ContentItem(text=event.prompt)
        message = Message(role="user", content=[content])
        messages.append(message)

        messages = chatbot_client.converse(system_prompts, messages)

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print(f"A client error occurred: {message}")
        raise
    except Exception as err:
        logger.error("An error occurred: %s", err)
        print(f"An error occurred: {err}")
        raise

    return messages


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
