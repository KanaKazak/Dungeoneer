from abc import abstractmethod
from logic.damage import DamageType
from logic.entities import Entity


# =========================================================
# BASE ITEM
# =========================================================

class Item(Entity):
    """
    Base class for all items in the game world.
    """

    def __init__(self, name, position, weight=0, category="misc"):
        super().__init__(name, position)
        self.weight = weight
        self.category = category
        self.is_quest_item = category == "quest"

    def __repr__(self):
        return f"Item(name={self.name}, position={self.position}, weight={self.weight}, category={self.category})"

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

    def __init__(self, name, position, damage: DamageType, ap_cost, tag=None, ranged=None):
        super().__init__(name, position, category="weapon")

        self.damage = damage
        self.ap_cost = ap_cost
        self.tag = tag
        self.ranged = ranged

    def __repr__(self):
        return (
            f"Weapon(name={self.name}, position={self.position}, "
            f"damage={self.damage}, ap_cost={self.ap_cost}, tag={self.tag}, ranged={self.ranged})"
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

    def __init__(self, name, position, damage: DamageType, ap_cost, tag="versatile", ranged=False):
        super().__init__(name, position, damage, ap_cost, tag, ranged)
        self.weight = 5

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

    def __init__(self, name, position, damage: DamageType, ap_cost, tag="heavy", ranged=False):
        super().__init__(name, position, damage, ap_cost, tag, ranged)
        self.weight = 4

    def __str__(self):
        return f"{self.name} (Club, Damage: {self.damage})"

    def describe(self):
        return (
            f"{self.name} is a crude goblin-made club. "
            f"It deals {self.damage} damage."
        )

class Bow(Weapon):
    """
    Light ranged weapon.
    """

    def __init__(self, name, position, damage: DamageType, ap_cost, tag="light", ranged=True):
        super().__init__(name, position, damage, ap_cost, tag, ranged)
        self.weight = 3

    def __str__(self):
        return f"{self.name} (Bow, Damage: {self.damage})"

    def describe(self):
        return (
            f"{self.name} is a finely crafted elven bow. "
            f"It deals {self.damage} damage from a distance."
        )

# =========================================================
# CONSUMABLES
# =========================================================

class Consumable(Item):
    """
    Base class for consumable items.
    """

    def __init__(self, name, position, effect):
        super().__init__(name, position, weight=0.5, category="consumable")
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
# CLOTHING AND ARMOR
# =========================================================

class Clothing_Armor(Item):
    """
    Items that can be worn for protection or style, but also have value.
    """

    def __init__(self, name, position, value):
        super().__init__(name, position, weight=1, category="Clothing_Armor")
        self.value = value

    def __repr__(self):
        return f"Clothing_Armor(name={self.name}, position={self.position}, value={self.value})"

    def describe(self):
        return (
            f"{self.name} is a piece of clothing or armor worth {self.value} gold coins."
        )
    
# =========================================================
# QUEST ITEMS
# =========================================================
class QuestItem(Item):
    """
    Items that are important for quests and cannot be discarded.
    """

    def __init__(self, name, position, description):
        super().__init__(name, position, weight=0, category="quest")
        self.description = description

    def __repr__(self):
        return f"QuestItem(name={self.name}, position={self.position}, description={self.description})"
    
# =========================================================
# SPECIFIC QUEST ITEMS
# =========================================================

class GoldMedal(QuestItem):
    """
    A golden medal that is important for a quest.
    """

    def __str__(self):
        return f"{self.name} (Gold Medal, Description: {self.description})"

    def describe(self):
        return (
            f"{self.name} is a shiny gold medal with intricate engravings. "
            f"It is the dungeon's most prized artifact."
        )
