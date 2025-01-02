import boto3

from aws_lambda_powertools import Logger
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

from models import Messages, Message

logger = Logger()

# In some regions / models Bedrock requests per minute can be too low for the integration tests so increase the number of retries.
config = Config(retries={"max_attempts": 15, "mode": "adaptive"})


class Bedrock:
    model_id: str

    def __init__(self, model_id):
        self.model_id = model_id
        try:
            self.bedrock_client = self._create_bedrock_client()
        except Exception as e:
            logger.error(f"Error initializing Bedrock client: {str(e)}")
            raise

    def _create_bedrock_client(self):
        try:
            bedrock_client = boto3.client("bedrock-runtime", config=config)
            return bedrock_client
        except ClientError as e:
            logger.error(f"AWS Client Error: {e.response['Error']['Message']}")
            raise  # Re-raise the exception after logging
        except BotoCoreError as e:
            logger.error(f"Boto3 Core Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Bedrock client: {str(e)}")
            raise

    def converse(self, system_prompts, messages: Messages):
        """
        Sends messages to a model.
        Args:
            system_prompts (JSON) : The system prompts for the model to use.
            messages (JSON) : The messages to send to the model.

        Returns:
            response (JSON): The conversation that the model generated.

        """

        logger.info("Generating message with model %s", self.model_id)

        # Inference parameters to use.
        temperature = 0.5
        top_k = 200

        # Base inference parameters to use.
        inference_config = {"temperature": temperature}
        # Additional inference parameters to use.
        additional_model_fields = {"top_k": top_k}

        # Send the message.
        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages.to_dict()["messages"],
                system=system_prompts,
                inferenceConfig=inference_config,
                additionalModelRequestFields=additional_model_fields,
            )
        except ClientError as e:
            logger.error(f"AWS Client Error: {e.response['Error']['Message']}")
            raise  # Re-raise the exception after logging

        # Log token usage.
        token_usage = response["usage"]
        logger.info("Input tokens: %s", token_usage["inputTokens"])
        logger.info("Output tokens: %s", token_usage["outputTokens"])
        logger.info("Total tokens: %s", token_usage["totalTokens"])
        logger.info("Stop reason: %s", response["stopReason"])

        message = Message.from_dict(response["output"]["message"])
        return message
