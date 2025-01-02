import boto3

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError, BotoCoreError

from models import Messages, Message

logger = Logger()


class DynamoDB:
    def __init__(self, table_name: str):
        try:
            self._create_ddb_table(table_name)
        except Exception as e:
            logger.error(f"Error initializing DynamoDB: {e}")
            raise

    def _create_ddb_table(self, table_name: str):
        try:
            ddb_resource = boto3.resource("dynamodb")
            self.table = ddb_resource.Table(table_name)

        except ClientError as e:
            logger.error(f"AWS Client Error: {e.response['Error']['Message']}")
            raise  # Re-raise the exception after logging
        except BotoCoreError as e:
            logger.error(f"Boto3 Core Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Bedrock client: {str(e)}")
            raise

    def save_last_message(self, messages: Messages):
        message: Message = messages.messages[-1]
        try:
            self.table.put_item(
                Item={
                    "session_id": messages.session_id,
                    "sequence": len(messages.messages),
                    "role": message.role.value,
                    "content": [item.to_dict() for item in message.content]
                }
            )
        except ClientError as e:
            logger.error(f"AWS Client Error: {e.response['Error']['Message']}")
            raise  # Re-raise the exception after logging
        except BotoCoreError as e:
            logger.error(f"Boto3 Core Error: {str(e)}")

        return message