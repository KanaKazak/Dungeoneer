import random

from logic.combat import attack, determine_initiative
from logic.dungeon import Room, Dungeon
from logic.entities import Player, Goblin
from logic.inventory_manipulation import inventory_manipulation
from logic.items import Club, GoldMedal, Sword, HealthPotion
from logic.loot import loot
from logic.movement import move_player
from logic.progress import save_progress
from logic.input_handler import get_input
from logic.enemy_ai import enemy_turn


# =========================================================
# WORLD DATA
# =========================================================

room_table = {
    "Damp Cellar": "Moss covers the walls.",
    "Bone Chamber": "Bones litter the floor.",
    "Forgotten Hall": "A sense of dread fills the air.",
    "Rat's Nest": "The sound of dripping water echoes.",
    "Dark Corridor": "Shadows dance on the walls."
}

starting_point = (5, 1)


# =========================================================
# PLACEHOLDER SYSTEMS
# =========================================================

def upgrade_character():
    print("To be implemented: Upgrade character stats, skills, etc.")


def options():
    print("To be implemented: Game options, settings, etc.")


# =========================================================
# GAME START
# =========================================================

def initialize_game(state, player_name = "Hero"): #player name hardcoded for now
    state.player = Player(name=player_name, position=starting_point, health=100)
    state.dungeon, state.current_room = generate_dungeon(state.player)
    state.current_room.is_visited = True

def start_new_game():
    """
    Creates player, generates dungeon, and starts main loop.
    """
    print("Starting a new game...")

    player_name = get_input("Enter your character's name: ", None)
    print(f"Welcome, {player_name}! Your adventure begins now.")

    player = Player(name=player_name, position=starting_point, health=100)

    dungeon, current_room = generate_dungeon(player)

    print(current_room.describe())

    game_loop(player, current_room, dungeon)


# =========================================================
# MAIN GAME LOOP
# =========================================================

def game_loop(player, current_room, dungeon):
    """
    Handles turn order and alternates between player and enemies.
    """
    turn_order = get_turn_order(player, current_room)

    while player.is_alive():

        if len(turn_order) > 1:
            print_turn_order(turn_order)

        for entity in turn_order:

            if not player.is_alive():
                break

            if entity == player:
                current_room, traversed = player_turn(player, current_room)

                if traversed:
                    turn_order = get_turn_order(player, current_room)
                    break

            else:
                if not entity.is_dead:
                    enemy_turn(entity, player, current_room)

        turn_order = get_turn_order(player, current_room)


def get_turn_order(player, current_room):
    """
    Builds initiative list for current room.
    """
    return determine_initiative(
        [player] + [e for e in current_room.contents["entities"] if not e.is_dead]
    )


def print_turn_order(turn_order):
    order_names = [e.name for e in turn_order]
    print(f"Initiative order: {', '.join(order_names)}")


# =========================================================
# PLAYER TURN SYSTEM
# =========================================================

def player_turn(player, current_room):
    """
    Handles all player actions within a turn.
    """
    player.reset_ap()
    player.movement_multiplier = 1
    player.movement = 0

    traversed = False

    while player.ap > 0:

        time_sensitive = any(
            e for e in current_room.contents["entities"] if not e.is_dead
        )

        print(f"\nYou have {player.ap} AP.")

        command = get_input(
            "Command (move, look, attack, loot, inventory, traverse, pos): ",
            player
        )

        # -----------------------------------------------------
        # MOVEMENT
        # -----------------------------------------------------
        if command == "move" and player.ap >= 1:
            move_player(player, current_room, time_sensitive)

        # -----------------------------------------------------
        # LOOK
        # -----------------------------------------------------
        elif command == "look" and player.ap >= 1:
            if time_sensitive:
                player.ap -= 1
            print(current_room.describe())

        # -----------------------------------------------------
        # ATTACK
        # -----------------------------------------------------
        elif command == "attack" and player.ap >= player.attack_ap_cost():
            attack(player, current_room, time_sensitive)

        # -----------------------------------------------------
        # LOOT
        # -----------------------------------------------------
        elif command == "loot" and player.ap >= 1:
            loot(player, current_room, time_sensitive)

        # -----------------------------------------------------
        # INVENTORY
        # -----------------------------------------------------
        elif command == "inventory" and player.ap >= 1:
            inventory_manipulation(player, time_sensitive)

        # -----------------------------------------------------
        # TRAVERSE ROOMS
        # -----------------------------------------------------
        elif command.startswith("traverse"):
            direction = command.split()[1]

            if direction not in current_room.exits:
                print("You can't go that way.")
                continue

            cost = 4

            if time_sensitive and player.ap < cost:
                print("Not enough AP to traverse during combat.")
                continue

            current_room = current_room.exits[direction]
            traversed = True

            if time_sensitive:
                player.ap -= cost

            player.position = starting_point

            print(f"You traverse {direction} to the {current_room.name}.")
            print(current_room.describe())
            break

        # -----------------------------------------------------
        # POSITION DEBUG
        # -----------------------------------------------------
        elif command in ["pos", "where"]:
            print(f"You are at {player.position}.")

        else:
            print("Invalid command.")

    return current_room, traversed


# =========================================================
# DUNGEON GENERATION
# =========================================================

def generate_dungeon(player):
    """
    Creates procedural dungeon with rooms, enemies, and loot.
    """
    num_rooms = random.randint(3, 5)

    rooms = []

    # -------------------------
    # CREATE ROOMS
    # -------------------------
    for _ in range(num_rooms):
        name, desc = random.choice(list(room_table.items()))
        rooms.append(Room(name=name, description=desc))

    # -------------------------
    # CONNECT ROOMS LINEARLY
    # -------------------------
    for i in range(num_rooms - 1):
        rooms[i].exits["north"] = rooms[i + 1]
        rooms[i + 1].exits["south"] = rooms[i]

    # -------------------------
    # POPULATE ROOMS
    # -------------------------
    for room in rooms:

        # ENEMIES
        if random.random() < 0.5:
            spawn_goblin(room)

        # ITEMS
        if random.random() < 0.5:
            spawn_loot(room)

    # -------------------------
    # WIN CONDITION ITEM
    # -------------------------
    spawn_goal_item(rooms[-1])

    # -------------------------
    # BUILD DUNGEON OBJECT
    # -------------------------
    dungeon = Dungeon("Procedural Dungeon")

    for room in rooms:
        dungeon.add_room(room)

    return dungeon, rooms[0]


# =========================================================
# SPAWN HELPERS
# =========================================================

def spawn_goblin(room):
    position = (random.randint(1, room.width), random.randint(1, room.height))
    while position == starting_point:
        position = (random.randint(1, room.width), random.randint(1, room.height))
    goblin = Goblin(
        name="Goblin",
        position=position,
        health=30,
        level=1
    )

    club = Club(
        name="Club",
        position=goblin.position,
        damage=4,
        ap_cost=1
    )

    goblin.inventory.append(club)
    goblin.equipped_weapon = club

    room.contents["entities"].append(goblin)


def spawn_loot(room):
    position = (random.randint(1, room.width), random.randint(1, room.height))
    while position == starting_point:
        position = (random.randint(1, room.width), random.randint(1, room.height))
    if random.random() < 0.5:
        item = Sword(
            name="Rusty Sword",
            position=position,
            damage=5,
            ap_cost=2
        )
    else:
        item = HealthPotion(
            name="Health Potion",
            position=position,
            effect=20
        )

    room.contents["items"].append(item)


def spawn_goal_item(room):
    gold_medal = GoldMedal(
        name="Gold Medal",
        position=(random.randint(1, room.width), random.randint(1, room.height)),
        description="The most prized artifact in the dungeon."
    )

    room.contents["items"].append(gold_medal)