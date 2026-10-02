import json
import os
import tempfile

class ConversationHistoryManager:
    def __init__(self, conversation_file="ASSETS/conversation_history.json", history_offset=400):
        self.history_offset = history_offset
        self.conversation_file = conversation_file
        if os.path.exists(conversation_file):
            # If conversation file exists, check if it's empty
            if os.stat(conversation_file).st_size == 0:
                # If file is empty, initialize self.history to an empty list
                self.history = []
            else:
                # If file is not empty, load the list from the file
                with open(conversation_file, "r") as file:
                    self.history = json.load(file)
                
                # Check if the last entry in history is a user entry
                if self.history and self.history[-1].get("role") == "user":
                    # If the last entry is a user entry, pop it out from both history and file
                    self.history.pop()
                    with open(conversation_file, "w") as file:
                        json.dump(self.history, file, indent=4)
        else:
            # If conversation file doesn't exist, initialize self.history to an empty list
            self.history = []

    def count_words(self):
        return sum(len(entry["content"].split()) for entry in self.history)

    def strip_history(self):
        total_words = self.count_words()
        while total_words > self.history_offset and self.history:
            total_words -= len(self.history.pop(0)["content"].split())
        return self.history

    def store_history(self, history):
        self.history = history
        self.strip_history()

    def record_turn(self, user_query, assistant_response):
        """Commit a selected conversational turn before publishing its RAM view.

        Action requests are deliberately not conversation turns. Keep the legacy
        update_file API for callers that already store their pending user entry.
        """
        if not isinstance(user_query, str) or not isinstance(assistant_response, str):
            raise TypeError("Conversation entries must be text")
        turn = [{"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response}]
        pending_history = self.history + turn
        words = sum(len(entry["content"].split()) for entry in pending_history)
        while words > self.history_offset and pending_history:
            words -= len(pending_history.pop(0)["content"].split())

        data = []
        if os.path.exists(self.conversation_file) and os.path.getsize(self.conversation_file):
            with open(self.conversation_file, "r") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Conversation archive must be a list")

        temporary_path = None
        try:
            directory = os.path.dirname(os.path.abspath(self.conversation_file))
            with tempfile.NamedTemporaryFile(mode="w", dir=directory,
                                             prefix=".conversation-", delete=False) as file:
                temporary_path = file.name
                json.dump(data + turn, file, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.conversation_file)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)

        self.history = pending_history

    def update_file(self, user_query, assistant_response):
        conversation_json = [{"role": "user", "content": user_query}, {"role": "assistant", "content": assistant_response}]
        data = []
        if os.path.exists(self.conversation_file) and os.path.getsize(self.conversation_file) > 0:
            with open(self.conversation_file, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    pass

        for entry in conversation_json:
            if isinstance(entry, dict):
                data.append(entry)

        with open(self.conversation_file, "w") as file:
            json.dump(data, file, indent=4)

        self.store_history(self.history + [{"role": "assistant", "content": assistant_response}])

    def load_history(self):
        with open(self.conversation_file, "r") as file:
            self.history = json.load(file)

    def strip_history_by_word_limit(self, word_limit):
        total_words = 0
        trimmed_history = []

        # Traverse the history from the end to the beginning
        for entry in reversed(self.history):
            entry_words = len(entry["content"].split())
            if total_words + entry_words > word_limit:
                break
            trimmed_history.insert(0, entry)
            total_words += entry_words

        self.history = trimmed_history



if __name__ == "__main__":

    history_manager = ConversationHistoryManager()

    while True:
        user_query = input("You: ")
        if user_query.lower() == '/bye':
            print("Exiting chat...")
            break

        history_manager.store_history(history_manager.history + [{"role": "user", "content": user_query}])
        print("\n\n\033[93m" + str(history_manager.history) + "\033[0m\n\n")
        history_manager.update_file(user_query, "THIS IS THE ASSISTANT RESPONSE")
