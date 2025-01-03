import json
import boto3
import botocore.client
import os
import sys
import pytest

from importlib import reload
from unittest.mock import patch
from moto import mock_aws

sys.path.append(os.path.join(os.getcwd(), "functions"))
sys.path.append(os.path.join(os.getcwd(), "layers", "chatbot"))

test_messages = [
    "Create me a nursery rhyme about goats",
    "Here's a silly nursery rhyme about goats:\n\nLittle Billy Goat\nOn the rocky hill did stoat\nMunching grass and leaves galore\nHis tummy full, he asked for more\n\nSee the goats upon the ridge\nPrancing, skipping off the bridge\nLeaping over rocks and logs\nWagging their little tails like dogs\n\nNanny goats with kids so small\nClimbing up the stone wall\nNibbling here and munching there\nGoats are funny I do swear!\n\nBaaaa baaaa black sheep, have you any wool?\nNo kind sir, I'm just a goat\nIsn't that the truth!",
    "Can you make it shorter and two verses?",
    "Here's a shorter nursery rhyme about goats with two verses:\n\nLittle kid, little kid, munching leaves so green,\nClimbing up the old oak tree, the happiest ever seen.\nFrolicking and leaping high, your antics make us smile,\nBringing joy to the farmyard, if only for a while.\n\nBilly goats with horns so grand, guarding the herd with care,\nButting heads in playful jest, without a worry or care.\nProviding milk and cheese for us, in your simple way,\nDelightful little creatures, enjoying each new day.",
]


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
            response["output"]["message"]["content"][0]["text"] = test_messages[1]
            return response
        if len(kwarg["messages"]) == 3:
            response["output"]["message"]["content"][0]["text"] = test_messages[3]
            return response
    return orig(self, operation_name, kwarg)


@mock_aws
class TestBedrockChatbot:
    def test_chatbot_one_interaction_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        create_ddb_table,
    ):
        # The lambda function retrieves the Bedrock model ID environment variable outside the handler. It therefore needs to be set before the function is imported
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        # Import the lambda handler function from the chatbot app
        from chatbot.app import lambda_handler
        # Force reload so code outside the handler is re-executed
        app = reload(sys.modules["chatbot.app"])
        # Get test event that is in the format of a REST API Gateway proxy integration
        event = chatbot_lambda_event
        # Set the event body with the prompt to be used for testing and an empty list of messages (as first message in the conversation)
        event["body"] = json.dumps({"prompt": test_messages[0], "messages": []})
        # Mock the Bedrock API call and invoke the lambda handler
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)
        # Verify the response status code is 200 (success)
        assert response["statusCode"] == 200
        # Parse the response body
        body = json.loads(response["body"])
        # Verify there are 2 messages in the conversation (prompt and response)
        assert len(body["messages"]) == 2
        # Verify the messages are as expected
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["content"][0]["text"] == test_messages[0]
        assert body["messages"][1]["role"] == "assistant"
        assert body["messages"][1]["content"][0]["text"] == test_messages[1]

        # Get the items currently in the DDB table for the session
        session_id = body["session_id"]
        items = self._get_current_items(session_id)

        # Verify the ddb records are as expected
        assert len(items) == 2
        assert items[0]["session_id"] == session_id
        assert items[0]["role"] == "user"
        assert items[0]["content"][0]["text"] == test_messages[0]
        assert items[1]["session_id"] == session_id
        assert items[1]["role"] == "assistant"
        assert items[1]["content"][0]["text"] == test_messages[1]

    def test_chatbot_two_interaction_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        create_ddb_table,
    ):
        # The lambda function retrieves the Bedrock model ID environment variable outside the handler. It therefore needs to be set before the function is imported
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        # Import the lambda handler function from the chatbot app
        from chatbot.app import lambda_handler
        # Force reload so code outside the handler is re-executed
        app = reload(sys.modules["chatbot.app"])

        # Get test event that is in the format of a REST API Gateway proxy integration
        event = chatbot_lambda_event
        # Set the event body with the prompt to be used for testing and an empty list of messages (as first message in the conversation)
        event["body"] = json.dumps({"prompt": test_messages[0], "messages": []})
        # Mock the Bedrock API call and invoke the lambda handler
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)

        # Check the response from the lambda handler is a 200
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        # Verify there are two messages in the response
        assert len(body["messages"]) == 2
        # Verify the messages are as expected
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["content"][0]["text"] == test_messages[0]
        assert body["messages"][1]["role"] == "assistant"
        assert body["messages"][1]["content"][0]["text"] == test_messages[1]

        # Get the items currently in the DDB table for the session
        session_id = body["session_id"]
        items = self._get_current_items(session_id)

        # Verify the ddb records are as expected
        assert len(items) == 2
        assert items[0]["session_id"] == session_id
        assert items[0]["role"] == "user"
        assert items[0]["content"][0]["text"] == test_messages[0]
        assert items[1]["session_id"] == session_id
        assert items[1]["role"] == "assistant"
        assert items[1]["content"][0]["text"] == test_messages[1]

        # Retrieve the response body from the lambda handler response, this includes the user prompt and the assistant response as messages
        event_body = json.loads(response["body"])
        # Add another prompt for the second call to the lambda handler
        event_body["prompt"] = test_messages[2]
        event["body"] = json.dumps(event_body)

        # Mock the Bedrock API call and invoke the lambda handler with the new prompt and the existing messages
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            response = lambda_handler(event, base_lambda_context)

        # Check the response from the lambda handler is a 200
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        # Verify there are four messages in the response
        assert len(body["messages"]) == 4
        # Verify the messages are as expected
        assert body["messages"][2]["role"] == "user"
        assert body["messages"][2]["content"][0]["text"] == test_messages[2]
        assert body["messages"][3]["role"] == "assistant"
        assert body["messages"][3]["content"][0]["text"] == test_messages[3]

        # Get the items currently in the DDB table for the session
        session_id = body["session_id"]
        items = self._get_current_items(session_id)

        # Verify the ddb records are as expected
        assert len(items) == 4
        assert items[2]["session_id"] == session_id
        assert items[2]["role"] == "user"
        assert items[2]["content"][0]["text"] == test_messages[2]
        assert items[3]["session_id"] == session_id
        assert items[3]["role"] == "assistant"
        assert items[3]["content"][0]["text"] == test_messages[3]

    # Get the current items from the mock DDB table based on the session id.
    def _get_current_items(self, session_id):
        table_name = os.environ["DDB_TABLE_NAME"]
        ddb_resource = boto3.resource("dynamodb")
        ddb_table = ddb_resource.Table(table_name)

        response = ddb_table.query(
            KeyConditions={
                "session_id": {
                    "AttributeValueList": [session_id],
                    "ComparisonOperator": "EQ",
                }
            }
        )
        return response["Items"]
