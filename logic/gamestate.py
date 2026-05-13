class GameState:
    def __init__(self):
        self.player = None
        self.current_room = None
        self.dungeon = None
        self.messages = ["Welcome to Dungeoneer"]
        self.running = True