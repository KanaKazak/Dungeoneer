from abc import ABC, abstractmethod
import random

from logic.input_handler import get_input
from logic.progress import load_progress
from logic.attributes import Attributes


# =========================================================
# BASE ENTITY
# =========================================================

class Entity(ABC):
    """
    Base class for all world objects with a position.
    """

    def __init__(self, name, position):
        self.name = name
        self.position = position

    def __repr__(self):
        return f"{self.name} at ({self.position[0]}, {self.position[1]})"

    @abstractmethod
    def describe(self):
        pass


# =========================================================
# CHARACTER BASE CLASS
# =========================================================

class Character(Entity):
    """
    Base class for all living entities (player, enemies).
    Handles combat stats, leveling, and movement.
    """

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------

    def __init__(
        self,
        name,
        position,
        health,
        base_hp=100,
        ap=4,
        ap_max=4,
        movement=0,
        level=1,
        equipped_weapon=None
    ):
        self.attributes = Attributes()

        super().__init__(name, position)

        self.base_hp = base_hp
        self.max_health = base_hp + int(self.attributes.get_attribute_bonus("CON") * 2)
        self.health = self.max_health

        self.ap = ap
        self.ap_max = 4 + int(self.attributes.get_attribute_bonus("AGI") // 15)

        self.level = level
        self.exp_threshold = self.level * 100
        self.total_exp = 0

        self.equipped_weapon = equipped_weapon
        self.base_damage = 2  # placeholder until scaling system exists

        self.attack_bonus_temp = 0
        self.movement_multiplier = 1

        self.movement_per_ap = 1
        self.movement = 0

        self.max_carry_weight = 50 + self.attributes.STR * 2

        self.is_dead = False
    def loot_ap_cost(self):
        return 1 # some perks might reduce this
    @property
    def carry_weight(self):
        return sum(item.weight for item in self.inventory)

    # ---------------------------------------------------------
    # COMBAT STATS
    # ---------------------------------------------------------

    @property
    def damage(self):
        return self.equipped_weapon.damage if self.equipped_weapon else self.base_damage

    def attack_ap_cost(self):
        return self.equipped_weapon.ap_cost if self.equipped_weapon else 1

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def is_alive(self):
        return self.health > 0


    # ---------------------------------------------------------
    # RESOURCE MANAGEMENT
    # ---------------------------------------------------------

    def reset_ap(self):
        self.ap = self.ap_max


    # ---------------------------------------------------------
    # EXPERIENCE & LEVELING
    # ---------------------------------------------------------

    def gain_exp(self, amount):
        multiplier = 1 + int(self.attributes.get_attribute_bonus("INT")) * 0.005
        self.total_exp += int(amount * multiplier)

    def level_up(self):
        self.total_exp -= self.exp_threshold
        self.level += 1
        self.exp_threshold = self.level * 100

        print(
            f"{self.name} has leveled up! They are now level {self.level}!\n"
            "For now this does nothing, but later it will increase stats and unlock abilities."
        )


# =========================================================
# PLAYER
# =========================================================

class Player(Character):
    """
    Player-controlled character.
    Handles inventory, progression, and manual stat allocation.
    """

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------

    def __init__(self, name, position, health):
        super().__init__(name, position, health)

        self.inventory = []

        self.total_exp, self.level, self.attributes = load_progress()

        self.exp_threshold = self.level * 100

        # Recalculate derived stats after loading
        self.hp_max = self.base_hp + int(self.attributes.get_attribute_bonus("CON") * 2)
        self.hp = self.hp_max

        self.ap_max = 4 + int(self.attributes.get_attribute_bonus("AGI") // 15)
        self.ap = self.ap_max

        self.movement_per_ap = 1
        self.movement = 0

        self.max_carry_weight = 50 + self.attributes.STR * 2

    # ---------------------------------------------------------
    # DESCRIPTION
    # ---------------------------------------------------------

    def describe(self):
        return (
            f"{self.name} is a mighty hero venturing into the dungeon.\n"
            f"{self.hp}/{self.hp_max} HP | Damage: {self.damage}"
        )


    # ---------------------------------------------------------
    # PLAYER LEVEL UP (ATTRIBUTE ALLOCATION)
    # ---------------------------------------------------------

    def level_up(self):
        super().level_up()

        attribute_points = 5

        print(f"Your current attributes:\n{self.attributes}")
        print(
            f"You have {attribute_points} points to distribute among:\n"
            "STR, CON, DEX, AGI, INT, WIS, CHA, LUCK."
        )

        valid_attributes = ["STR", "CON", "DEX", "AGI", "INT", "WIS", "CHA", "LUCK"]

        while attribute_points > 0:
            choice = get_input(
                f"Increase which attribute? (Points left: {attribute_points}) ",
                self
            ).upper()

            if choice not in valid_attributes:
                print("Invalid attribute choice.")
                continue

            current_value = getattr(self.attributes, choice)
            effective = self.attributes.apply_soft_cap(current_value, 1)

            # Soft cap warnings
            if current_value >= 80:
                print(f"⚠ {choice}: severe diminishing returns ({effective:.2f})")
            elif current_value >= 60:
                print(f"⚠ {choice}: strong diminishing returns ({effective:.2f})")
            elif current_value >= 30:
                print(f"⚠ {choice}: moderate diminishing returns ({effective:.2f})")

            confirm = get_input(
                f"Increase {choice} from {current_value} to {current_value + 1}? (yes/no): ",
                self
            )

            if confirm == "yes":
                setattr(self.attributes, choice, current_value + 1)
                attribute_points -= 1
                print(f"{choice} increased!\n{self.attributes}")
            else:
                print("Cancelled.")



# =========================================================
# ENEMY BASE CLASS
# =========================================================

class Enemy(Character):
    """
    Base enemy class with preset attributes.
    """

    def __init__(self, name, position, health, level=1):
        super().__init__(name, position, health, level=level, base_hp=30)

        self.inventory = []
        self.is_enemy = True

        # Default enemy stat spread
        self.attributes = Attributes(
            STR=5, CON=5, DEX=3, AGI=3, INT=1, WIS=1, CHA=1, LUCK=2
        )

        self.hp_max = self.base_hp + int(self.attributes.get_attribute_bonus("CON") * 2)
        self.hp = self.hp_max

        self.ap_max = 4 + int(self.attributes.get_attribute_bonus("AGI") // 15)
        self.ap = self.ap_max

        self.movement_per_ap = 1
        self.movement = 0

        self.max_carry_weight = 50 + self.attributes.STR * 2


# =========================================================
# GOBLIN (SPECIFIC ENEMY TYPE)
# =========================================================

class Goblin(Enemy):
    """
    Fast, weak enemy with randomized stat growth.
    """

    def describe(self):
        return (
            f"{self.name} is a sneaky goblin lurking in the shadows.\n"
            f"{self.hp}/{self.hp_max} HP | Damage: {self.damage}"
        )

    def level_up(self):
        super().level_up()

        # Weighted stat growth
        weights = {
            "STR": 3,
            "DEX": 3,
            "CON": 2,
            "LUCK": 2,
            "AGI": 1,
        }

        choices = []
        for attr, weight in weights.items():
            choices.extend([attr] * weight)

        increase = random.choice(choices)
        setattr(self.attributes, increase, getattr(self.attributes, increase) + 1)

        print(
            f"The {self.name} grew "
            f"{'stronger' if increase == 'STR' else 'more cunning' if increase == 'DEX' else 'tougher' if increase == 'CON' else 'luckier' if increase == 'LUCK' else 'faster'}! "
            f"It is now level {self.level}!"
        )