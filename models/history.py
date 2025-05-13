from message import Message
import datetime

class History:
    def __init__(self):
        self.history = []

    def add(self,  input: Message, output: Message):
        self.history.append([None, input.content, output.content, datetime.datetime.now()])

    def as_table(self):
        return self.history
