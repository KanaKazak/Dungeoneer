from logic.input_handler import get_input
from logic.items import HealthPotion, Weapon, Valuables


# =========================================================
# INVENTORY SYSTEM
# =========================================================

def inventory_manipulation(player, time_sensitive=False):
    """
    Handles inventory viewing and item interaction.
    """

    # -------------------------
    # AP COST
    # -------------------------
    if time_sensitive:
        player.ap -= 1

    # -------------------------
    # EMPTY INVENTORY CHECK
    # -------------------------
    if not player.inventory:
        print("Your inventory is empty.")
        return

    # -------------------------
    # LIST ITEMS
    # -------------------------
    print("You are carrying:")
    for item in player.inventory:
        print(f"- {item.name}")

    # -------------------------
    # ITEM SELECTION
    # -------------------------
    choice = get_input(
        "Which item would you like to use? (Enter item name or 'none'): ",
        player
    ).lower()

    if choice == "none":
        return

    item = next(
        (item for item in player.inventory if item.name.lower() == choice),
        None
    )

    if not item:
        print("Item not found.")
        return

    # -------------------------
    # ITEM HANDLING
    # -------------------------
    handle_item(player, item, time_sensitive)


# =========================================================
# ITEM DISPATCH
# =========================================================

def handle_item(player, item, time_sensitive=False):
    """
    Routes item interaction based on type.
    """

    if isinstance(item, HealthPotion):
        use_consumable(player, item, time_sensitive)
        player.inventory.remove(item)

    elif isinstance(item, Weapon):
        equip_weapon(player, item, time_sensitive)

    elif isinstance(item, Valuables):
        print(f"You examine the {item.name}. It's worth {item.value} gold coins.")

    else:
        print("Nothing happens.")


# =========================================================
# EQUIP WEAPON
# =========================================================

def equip_weapon(player, weapon, time_sensitive=False):
    """
    Equips a weapon to the player.
    """

    if time_sensitive:
        player.ap -= 1

    player.equipped_weapon = weapon
    print(f"You equip the {weapon.name}.")


# =========================================================
# USE CONSUMABLE
# =========================================================

def use_consumable(player, consumable, time_sensitive=False):
    """
    Applies consumable effects (e.g., healing).
    """

    if time_sensitive:
        player.ap -= 1

    print(f"You use the {consumable.name}.")

    player.health = min(
        player.max_health,
        player.health + consumable.effect
    )

    print(
        f"You restore {consumable.effect} HP. "
        f"Current HP: {player.health}/{player.max_health}."
    )