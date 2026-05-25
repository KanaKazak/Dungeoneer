from logic.gamestate import log
from logic.combat import execute_attack, is_within_melee_range
from logic.movement import get_direction_toward, move_character


def enemy_turn(enemy, player, current_room, state=None):
    enemy.reset_ap()
    while enemy.ap > 0:
        if not player.is_alive():
            break
        if is_within_melee_range(enemy, player):
            execute_attack(enemy, player, current_room, state=state)
            enemy.ap -= 1
        else:
            direction = get_direction_toward(enemy, player)
            move_character(enemy, direction, enemy.movement_per_ap, current_room)
            enemy.ap -= 1