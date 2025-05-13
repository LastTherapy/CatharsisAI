from typing import List
import datetime
from models.message import Message
from settings import MAX_HISTORY


class Row:
    row_id: int
    input: Message
    input_media: List[Message]
    output: Message
    timestamp: str

    def __init__(self, row_id: int = None, user_prompt: Message = None, output: Message = None, input_media: List[Message] = None):
        self.row_id = row_id
        self.user_prompt = user_prompt
        self.output = output
        self.input_media = input_media
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class History:
    def __init__(self):
        self.history = []

    def add(self,  row: Row):
        """
        Adds a row to the history with a timestamp and database-friendly format
        :param row:
        :return:
        """
        if len(self.history) >= MAX_HISTORY:
            self.history.pop(0)

        self.history.append(row)

    def get_history(self) -> List:
        """
        Returns a list of history messages in format required by OpenAI-style API
        :return:
        """
        chat_history = []
        for row in self.history:
            chat_history.append({"role": "user", "content": row.user_prompt.content})
            chat_history.append({"role": "assistant", "content": row.output.content})
        return chat_history

    def as_table(self):
        return self.history
