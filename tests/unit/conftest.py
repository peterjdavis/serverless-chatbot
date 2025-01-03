import os
import pytest
import boto3

from moto import mock_aws

@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

@pytest.fixture()
def ddb_client():
    with mock_aws():
        yield boto3.client("dynamodb")

@pytest.fixture()
def create_ddb_table(ddb_client):
    table_name = "ChatbotHistory"
    try:
        ddb_table = ddb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},
                {"AttributeName": "sequence", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "sequence", "AttributeType": "N"}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    except Exception as e:
        print(e)
        
    os.environ['DDB_TABLE_NAME'] = table_name

    yield ddb_table