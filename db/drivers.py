import sqlite3
from models.message import Message


class SimpleSliteDriver:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.conn = sqlite3.connect(file_path)

    def __create_table(self, chat_id: int):
        cursor = self.conn.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS chat_{chat_id} (id INTEGER PRIMARY KEY AUTOINCREMENT, input TEXT, media_input TEXT, output TEXT, timestamp TEXT)")
        self.conn.commit()
        cursor.close()

    def get_chat_history(self, chat_id: int):
        cursor = self.conn.cursor()
        self.__create_table(chat_id)
        cursor.execute(f"SELECT * FROM chat_{chat_id}")
        result = cursor.fetchall()
        cursor.close()
        return result

    def update_chat_history(self, history: list, chat_id: int):
        cursor = self.conn.cursor()
        self.__create_table(chat_id)
        self.conn.commit()


if __name__ == "__main__":
    driver = SimpleSliteDriver("test.db")
    print(driver.get_chat_history(1))