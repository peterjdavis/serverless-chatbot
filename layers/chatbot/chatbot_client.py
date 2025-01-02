from bedrock import Bedrock
from dynamodb import DynamoDB
from models import Messages

class Chatbot:
    def __init__(self, model_id:str, table_name: str):
        self.bedrock = Bedrock(model_id)
        self.ddb = DynamoDB(table_name)

    def converse(self, system_prompts, messages: Messages):
        response = self.ddb.save_last_message(messages)
        response = self.bedrock.converse(system_prompts, messages)
        messages.append(response)
        response = self.ddb.save_last_message(messages)
        return messages