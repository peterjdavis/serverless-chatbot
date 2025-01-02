import pytest
import requests
import boto3

from unittest.mock import MagicMock, patch


class TestBedrockChatbotAPI:
    def test_chat_success(self, chatbot_api_uri, api_success_request_auth):

        json_payload = {
            "prompt": "Create me a nursery rhyme about goats",
            "messages": [],
        }
        response = requests.post(
            chatbot_api_uri, json=json_payload, auth=api_success_request_auth
        )

        assert response.status_code == 200
