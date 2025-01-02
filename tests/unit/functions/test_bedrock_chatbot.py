import json
import botocore.client
import os
import sys

from unittest.mock import patch
from moto import mock_aws

sys.path.append(os.path.join(os.getcwd(), "functions"))
sys.path.append(os.path.join(os.getcwd(), "layers", "chatbot"))

orig = botocore.client.BaseClient._make_api_call


def mock_make_api_call(self, operation_name, kwarg):
    if operation_name == "Converse":
        response = {
            "ResponseMetadata": {
                "RequestId": "12345678-9012-3456-7890123456789012",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "date": "Wed, 01 Jan 2025 00:00:00 GMT",
                    "content-type": "application/json",
                    "content-length": "703",
                    "connection": "keep-alive",
                    "x-amzn-requestid": "12345678-9012-3456-7890123456789012",
                },
                "RetryAttempts": 5,
            },
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": ""}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 54, "outputTokens": 156, "totalTokens": 210},
            "metrics": {"latencyMs": 3466},
        }

        # Check to see if responding to the first message in the conversation
        if len(kwarg["messages"]) == 1:
            response["output"]["message"]["content"][0][
                "text"
            ] = "Here's a silly nursery rhyme about goats:\\n\\nLittle Billy Goat\\nOn the rocky hill did stoat\\nMunching grass and leaves galore\\nHis tummy full, he asked for more\\n\\nSee the goats upon the ridge\\nPrancing, skipping off the bridge\\nLeaping over rocks and logs\\nWagging their little tails like dogs\\n\\nNanny goats with kids so small\\nClimbing up the stone wall\\nNibbling here and munching there\\nGoats are funny I do swear!\\n\\nBaaaa baaaa black sheep, have you any wool?\\nNo kind sir, I'm just a goat\\nIsn't that the truth!"
            return response
        if len(kwarg["messages"]) == 3:
            response["output"]["message"]["content"][0][
                "text"
            ] = "Here's a shorter nursery rhyme about goats with two verses:\\n\\nLittle kid, little kid, munching leaves so green,\\nClimbing up the old oak tree, the happiest ever seen.\\nFrolicking and leaping high, your antics make us smile,\\nBringing joy to the farmyard, if only for a while.\\n\\nBilly goats with horns so grand, guarding the herd with care,\\nButting heads in playful jest, without a worry or care.\\nProviding milk and cheese for us, in your simple way,\\nDelightful little creatures, enjoying each new day."
            return response
    return orig(self, operation_name, kwarg)


@mock_aws
class TestBedrockChatbot:
    def test_chatbot_first_message_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        create_ddb_table,
    ):
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        from chatbot.app import lambda_handler

        event = chatbot_lambda_event
        event["body"] = json.dumps(
            {"prompt": "Create me a nursery rhyme about goats", "messages": []}
        )
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["messages"]) == 2

    def test_chatbot_second_message_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        create_ddb_table,
    ):
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        from chatbot.app import lambda_handler

        event = chatbot_lambda_event
        event["body"] = json.dumps(
            {"prompt": "make it shorter and two verses", "messages": []}
        )
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)

        event_body = json.loads(response["body"])
        event_body["prompt"] = "make it shorter and two verses"
        event["body"] = json.dumps(event_body)
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["messages"]) == 4
