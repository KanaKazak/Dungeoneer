import random

from logic.damage import DamageType
from logic.entities import Character
from logic.input_handler import get_input
from logic.items import Weapon
from logic.attributes import Attributes
from logic.gamestate import log
from logic.messages import add_message


# =========================================================
# INITIATIVE SYSTEM
# =========================================================

def determine_initiative(entities):
    """
    Determines turn order based on d20 roll + AGI bonus.
    Dead entities are excluded.
    """
    rolls = []
    living = [e for e in entities if not e.is_dead]

    for entity in living:
        roll = random.randint(1, 20) + entity.attributes.get_attribute_bonus("AGI")
        rolls.append((entity, roll))

    rolls.sort(key=lambda x: x[1], reverse=True)
    return [entity for entity, roll in rolls]


# =========================================================
# ATTACK MODIFIERS
# =========================================================

def get_attack_bonus(attacker):
    """
    Determines attack stat bonus based on weapon type.
    """
    weapon = attacker.equipped_weapon

    if weapon is None:
        return max(
            attacker.attributes.get_attribute_bonus("STR"),
            attacker.attributes.get_attribute_bonus("DEX")
        )

    if weapon.tag == "light":
        return attacker.attributes.get_attribute_bonus("DEX")

    if weapon.tag == "heavy":
        return attacker.attributes.get_attribute_bonus("STR")

    # versatile or fallback
    return max(
        attacker.attributes.get_attribute_bonus("STR"),
        attacker.attributes.get_attribute_bonus("DEX")
    )


# =========================================================
# HIT / DAMAGE CALCULATION
# =========================================================

def calculate_hit(attacker, defender):
    """
    Determines hit outcome: crit / hit / miss / fumble.
    """
    roll = random.randint(1, 100)

    crit_threshold = 100 - int(attacker.attributes.get_attribute_bonus("LUCK") // 5)
    fumble_threshold = max(1, 2 - int(attacker.attributes.get_attribute_bonus("LUCK") // 30))

    # Critical hit
    if roll >= crit_threshold:
        return "crit", roll

    # Fumble check
    if roll <= fumble_threshold:
        luck_save = random.randint(1, 100)
        luck_bonus = attacker.attributes.get_attribute_bonus("LUCK")

        if luck_save <= luck_bonus:
            return "miss", roll  # lucky recovery
        return "fumble", roll

    # Normal hit calculation
    attack_bonus = get_attack_bonus(attacker)
    prof_bonus = attacker.level * 2

    total = roll + attack_bonus + prof_bonus + attacker.attack_bonus_temp
    ac = 50 + defender.attributes.get_attribute_bonus("AGI")

    return ("hit" if total >= ac else "miss"), roll


def calculate_damage(attacker, defender):
    prof_bonus = attacker.level * 2
    base_damage = attacker.damage  # DamageType object
    attr_bonus = get_attack_bonus(attacker) / 10
    
    if isinstance(base_damage, DamageType):
        total_damage = base_damage.total() + attr_bonus + prof_bonus
    else:
        total_damage = base_damage + attr_bonus + prof_bonus
    
    return int(total_damage)


# =========================================================
# MELEE RANGE CHECK
# =========================================================

def is_within_melee_range(attacker, target):
    """
    Checks if two entities are adjacent (1 tile range).
    """
    ax, ay = attacker.position
    tx, ty = target.position
    return abs(ax - tx) <= 1 and abs(ay - ty) <= 1


# =========================================================
# ATTACK FLOW (PLAYER/AI ENTRY POINT)
# =========================================================

def attack(attacker, current_room, time_sensitive=False, messages=None):
    if attacker.equipped_weapon and attacker.equipped_weapon.ranged:
        targets = [
            e for e in current_room.contents["entities"]
            if isinstance(e, Character) and e != attacker and not e.is_dead
        ]
        if not targets:
            log("There are no enemies to attack.", messages)
            return
        if len(targets) == 1:
            execute_attack(attacker, targets[0], current_room, time_sensitive, messages)
            return
        for i, e in enumerate(targets, 1):
            log(f"{i}. {e.name} at {e.position}", messages)
        choice = get_input("Who do you want to attack? ", attacker)
        if choice == "none":
            return
        if choice in [enemy.name.lower() for enemy in targets]:
            enemy = next(e for e in targets if e.name.lower() == choice)
            execute_attack(attacker, enemy, current_room, time_sensitive, messages)
        else:
            log("Invalid choice. No attack executed.", messages)
    else:
        """
        Handles selecting and executing an attack.
        """
        targets = [
            e for e in current_room.contents["entities"]
            if isinstance(e, Character) and e != attacker and not e.is_dead
        ]

        if not targets:
            log("There are no enemies to attack.", messages)
            return

        # Filter valid melee targets
        targets_in_range = [
            enemy for enemy in targets
            if is_within_melee_range(attacker, enemy)
        ]

        if not targets_in_range:
            log("There are no enemies within melee range to attack.", messages)
            return

        # Auto-attack if only one target
        if len(targets_in_range) == 1:
            execute_attack(attacker, targets_in_range[0], current_room, time_sensitive, messages)
            return

        # Player chooses target
        for i, e in enumerate(targets_in_range, 1):
            log(f"{i}. {e.name} at {e.position}", messages)

        choice = get_input("Who do you want to attack? ", attacker)

        if choice == "none":
            return

        if choice in [enemy.name.lower() for enemy in targets_in_range]:
            enemy = next(e for e in targets_in_range if e.name.lower() == choice)
            execute_attack(attacker, enemy, current_room, time_sensitive, messages)
        else:
            log("Invalid choice. No attack executed.", messages)


# =========================================================
# COMBAT RESOLUTION
# =========================================================


def execute_attack(attacker, target, current_room, time_sensitive=False, state = None):
    """
    Executes full attack resolution (hit, damage, death).
    """
    ap_cost = attacker.attack_ap_cost()

    # AP check (only in time-sensitive mode)
    if time_sensitive and attacker.ap < ap_cost:
        log("You don't have enough action points to attack.", state.messages)
        return

    add_message(f"{attacker.name} attacks {target.name}!", state.messages)

    if time_sensitive:
        attacker.ap -= ap_cost

    hit, roll = calculate_hit(attacker, target)

    # -------------------------
    # CRITICAL HIT
    # -------------------------
    if hit == "crit":
        damage = calculate_damage(attacker, target) * 2
        target.take_damage(damage)
        log(f"Critical hit! {attacker.name} hit {target.name} for {damage} damage! (Roll: {roll})", state.messages)

    # -------------------------
    # NORMAL HIT
    # -------------------------
    elif hit == "hit":
        damage = calculate_damage(attacker, target)
        target.take_damage(damage)
        log(f"{attacker.name} hit {target.name} for {damage} damage! (Roll: {roll})", state.messages)

    # -------------------------
    # MISS
    # -------------------------
    elif hit == "miss":
        log(f"{attacker.name} missed {target.name}! (Roll: {roll})", state.messages)

    # -------------------------
    # FUMBLE
    # -------------------------
    elif hit == "fumble":
        log("Critical miss!", state.messages)
        handle_fumble(attacker, target, current_room, state)

    # -------------------------
    # POST-ATTACK STATE CHECK
    # -------------------------
    if not target.is_alive():
        target.is_dead = True
        log(f"You have slain {target.name}!", state.messages)

        exp_gained = target.level * 10
        log(f"You gain {exp_gained} experience points.", state.messages)
        attacker.gain_exp(exp_gained, state)

    else:
        log(f"{target.name} has {target.health} HP left.", state.messages)


# =========================================================
# FUMBLE EFFECTS
# =========================================================

def handle_fumble(attacker, target, current_room, state):
    """
    Random negative consequence for critical failure.
    """
    effect = random.randint(1, 6)

    if effect == 1:
        log(f"{attacker.name} trips and falls! All AP lost.", state.messages)
        attacker.ap = 0

    elif effect == 2:
        damage = calculate_damage(attacker, attacker) // 2
        log(f"{attacker.name} hits themselves for {damage} damage!", state.messages)
        attacker.take_damage(damage)

    elif effect == 3:
        log(f"{attacker.name} drops their weapon!", state.messages)
        # TODO: implement weapon drop system

    elif effect == 4:
        log(f"{attacker.name} stumbles! {target.name} gets a free attack!", state.messages)
        execute_attack(target, attacker, current_room, time_sensitive=False, state=state)

    elif effect == 5:
        log(f"{attacker.name} pulls a muscle! Movement halved next turn.", state.messages)
        attacker.movement_multiplier = 0.5

    elif effect == 6:
        log(f"Embarrassing miss! {target.name} gains +10 to next attack.", state.messages)
        target.attack_bonus_temp = 10