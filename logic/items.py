from abc import abstractmethod
from logic.entities import Entity


# =========================================================
# BASE ITEM
# =========================================================

class Item(Entity):
    """
    Base class for all items in the game world.
    """

    def __init__(self, name, position):
        super().__init__(name, position)

    def __repr__(self):
        return f"Item(name={self.name}, position={self.position})"

    @abstractmethod
    def describe(self):
        pass


# =========================================================
# WEAPONS
# =========================================================

class Weapon(Item):
    """
    Base weapon class.
    """

    def __init__(self, name, position, damage, ap_cost, tag=None):
        super().__init__(name, position)

        self.damage = damage
        self.ap_cost = ap_cost
        self.tag = tag

    def __repr__(self):
        return (
            f"Weapon(name={self.name}, position={self.position}, "
            f"damage={self.damage}, ap_cost={self.ap_cost}, tag={self.tag})"
        )

    def describe(self):
        return f"{self.name} is a weapon that deals {self.damage} damage."


# -------------------------
# SPECIFIC WEAPONS
# -------------------------

class Sword(Weapon):
    """
    Versatile weapon type.
    """
    tag = "versatile"

    def __str__(self):
        return f"{self.name} (Sword, Damage: {self.damage})"

    def describe(self):
        return (
            f"{self.name} is an excellent sword forged by dwarves of old. "
            f"It deals {self.damage} damage."
        )


class Club(Weapon):
    """
    Heavy blunt weapon.
    """
    tag = "heavy"

    def __str__(self):
        return f"{self.name} (Club, Damage: {self.damage})"

    def describe(self):
        return (
            f"{self.name} is a crude goblin-made club. "
            f"It deals {self.damage} damage."
        )


# =========================================================
# CONSUMABLES
# =========================================================

class Consumable(Item):
    """
    Base class for consumable items.
    """

    def __init__(self, name, position, effect):
        super().__init__(name, position)
        self.effect = effect

    def __repr__(self):
        return f"Consumable(name={self.name}, position={self.position}, effect={self.effect})"

    def describe(self):
        return f"{self.name} has an effect: {self.effect}."


class HealthPotion(Consumable):
    """
    Restores player health.
    """

    def __str__(self):
        return f"{self.name} (Health Potion, Effect: {self.effect})"

    def describe(self):
        return (
            f"{self.name} is a magical concoction that restores "
            f"{self.effect} health points."
        )


# =========================================================
# VALUABLE ITEMS
# =========================================================

class Valuables(Item):
    """
    Items used for currency or progression value.
    """

    def __init__(self, name, position, value):
        super().__init__(name, position)
        self.value = value

    def __repr__(self):
        return f"Valuable(name={self.name}, position={self.position}, value={self.value})"

    def describe(self):
        return (
            f"{self.name} is a valuable item worth {self.value} gold coins."
        )