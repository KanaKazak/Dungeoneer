from logic.events import EventQueue


class GameState:
    def __init__(self):
        self.player = None
        self.current_room = None
        self.dungeon = None
        self.messages = ["Welcome to Dungeoneer"]
        self.running = True
        self.events = EventQueue()

def log(text, messages=None):
    if messages is not None:
        messages.append(text)
        if len(messages) > 25:
            messages.pop(0)
    else:
        print(text)

