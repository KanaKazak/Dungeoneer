from logic.progress import save_progress
from logic.combat import is_within_melee_range
from logic.input_handler import get_input
from logic.messages import add_message


# =========================================================
# MAIN LOOT FUNCTION
# =========================================================

def loot(player, current_room, time_sensitive=False):
    """
    Handles looting items and corpses in the current room.
    """

    room_items = current_room.contents["items"]
    corpses = [e for e in current_room.contents["entities"] if e.is_dead]

    lootable = room_items + corpses

    if not lootable:
        print("There are no items to loot.")
        return

    lootable_in_range = [
        obj for obj in lootable
        if is_within_melee_range(player, obj)
    ]

    if not lootable_in_range:
        print("There are no items within range to loot.")
        return

    # If only one target, auto-resolve
    if len(lootable_in_range) == 1:
        handle_loot_target(player, lootable_in_range[0], current_room, time_sensitive)
        return

    # Otherwise present menu
    show_loot_menu(player, lootable_in_range, current_room, time_sensitive)


# =========================================================
# LOOT MENU
# =========================================================

def show_loot_menu(player, lootable_in_range, current_room, time_sensitive):
    """
    Displays loot options and processes player choice.
    """

    for i, obj in enumerate(lootable_in_range, 1):
        if is_corpse(obj):
            print(f"{i}. {obj.name} corpse at {obj.position} [{len(obj.inventory)} items]")
        else:
            print(f"{i}. {obj.name} at {obj.position}")

    choice = get_input("What do you want to loot? ", player).lower()

    if choice == "none":
        return

    # direct item match
    for obj in lootable_in_range:
        if obj.name.lower() == choice:
            handle_loot_target(player, obj, current_room, time_sensitive)
            return

    # corpse explicit match ("goblin corpse")
    for obj in lootable_in_range:
        if is_corpse(obj) and f"{obj.name.lower()} corpse" == choice:
            handle_corpse_loot(player, obj, time_sensitive)
            return

    print("Invalid choice.")


# =========================================================
# LOOT HANDLER DISPATCH
# =========================================================

def handle_loot_target(player, target, current_room, time_sensitive):
    """
    Routes loot action depending on whether target is item or corpse.
    """

    if is_corpse(target):
        handle_corpse_loot(player, target, time_sensitive)
    else:
        execute_loot(player, target, current_room.contents["items"], time_sensitive)


def handle_corpse_loot(player, corpse, time_sensitive):
    """
    Handles looting from dead enemies.
    """

    if not corpse.inventory:
        print(f"The {corpse.name} corpse has no items.")
        return

    print(f"You search the {corpse.name} corpse and find:")

    for i, item in enumerate(corpse.inventory, 1):
        print(f"{i}. {item.name}")

    choice = get_input("Which item do you want to loot? ", player).lower()

    if choice == "none":
        return

    for item in corpse.inventory:
        if item.name.lower() == choice:
            execute_loot(player, item, corpse.inventory, time_sensitive)
            return

    print("Invalid choice.")


# =========================================================
# CORE LOOT EXECUTION
# =========================================================

def execute_loot(player, item, source, time_sensitive=False, state=None):
    """
    Moves item from world to player inventory.
    """

    if time_sensitive:
        player.ap -= 1

    player.inventory.append(item)
    source.remove(item)

    add_message(f"You loot the {item.name}.", state.messages)

    # -------------------------
    # WIN CONDITION ITEM
    # -------------------------
    if item.name.lower() == "gold medal":
        handle_win_condition(player, state)


# =========================================================
# WIN CONDITION
# =========================================================

def handle_win_condition(player, state):
    """
    Ends game when victory item is obtained.
    """

    player.gain_exp(100, state)  # grant some exp for winning

    add_message("You have collected the prize and won the game! Congratulations!", state.messages)

    save_progress(player.total_exp, player.level, player.attributes, player.perks)

    state.events.emit("win")


# =========================================================
# UTILITIES
# =========================================================

def is_corpse(obj):
    """
    Checks if object is a dead entity (corpse).
    """
    return hasattr(obj, "is_dead")