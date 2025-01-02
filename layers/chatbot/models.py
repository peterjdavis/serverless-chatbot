from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Role(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'

class ContentItem(BaseModel):
    text: str = Field(..., min_length=1)
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text
        }

class Message(BaseModel):
    role: Role = Role.USER 
    content: List[ContentItem]

    def to_dict(self) -> Dict:
        return {
            'role': self.role.value,
            'content': [item.to_dict() for item in self.content]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=Role(data['role']),
            content=[ContentItem(**item) for item in data['content']]
        )

class Messages(BaseModel):
    session_id: str
    messages: List[Message]

    def append(self, message: Message):
        self.messages.append(message)

    @classmethod
    def from_message_list(cls, session_id: str, messages: List[Message]) -> 'Messages':
        return cls(session_id=session_id, messages=messages)

    def to_dict(self) -> Dict:
        return {
            'messages': [message.to_dict() for message in self.messages]
        }

class Event(BaseModel):
    session_id: Optional[str] = Field(default_factory=lambda: uuid4().hex)
    prompt: str
    messages: List[Message]

    # def to_dict(self) -> Dict:
    #     return {
    #         'prompt': self.prompt,
    #         'messages': [message.to_dict() for message in self.messages]
    #     }
    # @classmethod
    # def from_message_list(cls, messages: List[Message]) -> 'Messages':
    #     return cls(messages=messages)


