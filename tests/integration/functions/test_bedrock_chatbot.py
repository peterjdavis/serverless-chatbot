import json
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "functions"))
sys.path.append(os.path.join(os.getcwd(), "layers", "chatbot"))


class TestBedrockChatbotFunction:
    def test_chat_first_message_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        ddb_table_name,
    ):
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        os.environ["DDB_TABLE_NAME"] = ddb_table_name
        from chatbot.app import lambda_handler

        event = chatbot_lambda_event
        event["body"] = json.dumps(
            {"prompt": "Create me a nursery rhyme about goats", "messages": []}
        )
        response = lambda_handler(event, base_lambda_context)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["messages"]) == 2

    def test_chat_second_message_success(
        self,
        bedrock_model_id,
        chatbot_lambda_event,
        base_lambda_context,
        ddb_table_name,
    ):
        os.environ["BEDROCK_MODEL_ID"] = bedrock_model_id
        os.environ["DDB_TABLE_NAME"] = ddb_table_name
        from chatbot.app import lambda_handler

        event = chatbot_lambda_event
        event["body"] = json.dumps(
            {"prompt": "Create me a nursery rhyme about goats", "messages": []}
        )
        response = lambda_handler(event, base_lambda_context)

        event_body = json.loads(response["body"])
        event_body["prompt"] = "make it shorter and two verses"
        event["body"] = json.dumps(event_body)
        response = lambda_handler(event, base_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["messages"]) == 4
