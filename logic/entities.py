from abc import ABC, abstractmethod
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.messages import add_message
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
        self.perks = set()  # e.g. {"war_hardened", "scholar", "thick_hide"}

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
    
    @property
    def hp_max(self):
        base = self.base_hp + int(self.attributes.get_attribute_bonus("CON") * 2)
        if "war_hardened" in self.perks:
            base += (self.attributes.STR // 10) * 5
        return base
    @property
    def int_bonus(self):
        base = 1 + self.attributes.get_attribute_bonus("INT") * 0.005
        if "scholar" in self.perks:
            return base + 0.2
        return base  
    @property
    def evasion(self):
        base = 50 + self.attributes.get_attribute_bonus("AGI")
        if "sidestep" in self.perks:
            base += 10
        return base
    @property
    def ac(self):
        base = 0
        if "thick_hide" in self.perks:
            base += 2
        return base

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
    def gain_exp(self, amount, state):
        self.total_exp += int(amount * self.int_bonus)
        if self.total_exp >= self.exp_threshold:
            state.events.emit("level_up", player=self)

    def level_up(self, messages):
        self.total_exp -= self.exp_threshold
        self.level += 1
        self.exp_threshold = self.level * 100

        add_message(
            f"{self.name} has leveled up! They are now level {self.level}!\n"
            "For now this does nothing, but later it will increase stats and unlock abilities.", messages
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

        self.total_exp, self.level, self.attributes, self.perks = load_progress()

        self.exp_threshold = self.level * 100

        # Recalculate derived stats after loading
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

        add_message(
            f"The {self.name} grew "
            f"{'stronger' if increase == 'STR' else 'more cunning' if increase == 'DEX' else 'tougher' if increase == 'CON' else 'luckier' if increase == 'LUCK' else 'faster'}! "
            f"It is now level {self.level}!"
        , messages=None)