from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def __str__(self):
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return f"{self.role}: {self.content}"

    def __dict__(self):
        return {
            "role": self.role,
            "content": self.content,
        }