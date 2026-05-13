class Room:
    """
    Represents a single room in the world.
    Contains entities, items, and exits to other rooms.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

        self.contents = {
            "entities": [],
            "items": []
        }

        self.exits = {}

        # Room dimensions (currently unused but reserved for grid logic)
        self.width = 10
        self.height = 10


    # =========================================================
    # ROOM CONNECTIONS
    # =========================================================

    def add_exit(self, direction, room):
        """
        Connects this room to another room in a valid direction.
        """
        valid_directions = ["north", "south", "east", "west"]

        if direction not in valid_directions:
            raise ValueError(
                f"Invalid direction: {direction}. "
                f"Valid directions are: {', '.join(valid_directions)}"
            )

        self.exits[direction] = room


    # =========================================================
    # DESCRIPTION / DISPLAY
    # =========================================================

    def describe(self):
        """
        Returns a full text description of the room,
        including entities, items, and exits.
        """
        text = f"You are in {self.name}. {self.description}"

        # -------------------------
        # ENTITIES
        # -------------------------
        if self.contents["entities"]:
            text += "\nCharacters:"
            for entity in self.contents["entities"]:
                status = "(dead)" if entity.is_dead else ""
                text += f"\n- {entity.name} {status} at {entity.position}"
        else:
            text += "\nCharacters: None"

        # -------------------------
        # ITEMS
        # -------------------------
        if self.contents["items"]:
            text += "\nItems:"
            for item in self.contents["items"]:
                text += f"\n- {item.name} at {item.position}"
        else:
            text += "\nItems: None"

        # -------------------------
        # EXITS
        # -------------------------
        if self.exits:
            text += "\nExits: " + ", ".join(self.exits.keys())
        else:
            text += "\nExits: None"

        return text


    # =========================================================
    # DEBUG REPRESENTATION
    # =========================================================

    def __repr__(self):
        return f"Room(name={self.name})"


# =========================================================
# DUNGEON CONTAINER
# =========================================================

class Dungeon:
    """
    Container for multiple rooms.
    Handles basic lookup and storage.
    """

    def __init__(self, name: str):
        self.name = name
        self.rooms = {}


    # =========================================================
    # ROOM MANAGEMENT
    # =========================================================

    def add_room(self, room: Room):
        """
        Adds a room to the dungeon.
        """
        self.rooms[room.name] = room


    def get_room(self, name: str):
        """
        Retrieves a room by name.
        Returns None if not found.
        """
        return self.rooms.get(name)