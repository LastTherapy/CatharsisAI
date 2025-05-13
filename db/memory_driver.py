import datetime
from models.message import Message
from models.history import History, Row
from typing import DefaultDict
from collections import defaultdict

MAX_HISTORY = 20


class MemoryDriver:
    def __init__(self):
        self.history: DefaultDict[int, History] = defaultdict(History)

    def add(self, chat_id: int, user_prompt: str, output: str):
        row: Row = Row(user_prompt=Message("user", user_prompt), output=Message("assistant", output))
        self.history[chat_id].add(row)
        pass

    def get_history(self, chat_id: int):
        return self.history[chat_id].get_history()

    def close(self):
        pass
