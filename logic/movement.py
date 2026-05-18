from logic.input_handler import get_input
from logic.gamestate import log

# =========================================================
# PLAYER MOVEMENT (TURN-BASED)
# =========================================================

def move_player(player, current_room, time_sensitive=False):
    """
    Handles player movement during a turn.
    """

    # -------------------------
    # AP COST
    # -------------------------
    if time_sensitive:
        player.ap -= 1

    # -------------------------
    # MOVEMENT GAIN
    # -------------------------
    player.movement += int(player.movement_per_ap * player.movement_multiplier)

    # -------------------------
    # MOVEMENT LOOP
    # -------------------------
    while player.movement > 0:

        choice = get_input(
            "Move (north/south/east/west, or 'stop'): ",
            player
        ).lower()

        if choice == "stop":
            print("You stop moving.")
            break

        direction, steps = parse_movement_input(choice)

        if not direction:
            print("Invalid input.")
            continue

        if direction not in ["north", "south", "east", "west"]:
            print("Invalid direction.")
            continue

        steps = min(steps, player.movement)

        destination, actual_steps, hit_wall = calculate_destination(
            player.position,
            direction,
            steps,
            current_room
        )

        # -------------------------
        # WALL COLLISION
        # -------------------------
        if hit_wall:
            player.position = destination
            player.movement -= 1
            print(f"You slam into the {direction} wall after {actual_steps} steps!")
            print(f"Position: {player.position}")
            continue

        # -------------------------
        # BLOCKED TILE CHECK
        # -------------------------
        if is_position_occupied(destination, current_room):
            print("Something is blocking your path.")
            player.movement -= steps
            continue

        # -------------------------
        # SUCCESSFUL MOVE
        # -------------------------
        player.position = destination
        player.movement -= steps

        print(f"You move {direction}. Position: {player.position}")


# =========================================================
# INPUT PARSING
# =========================================================

def parse_movement_input(choice):
    """
    Extracts direction + steps from player input.
    Supports:
      - "north"
      - "move north"
      - "north 3"
    """

    parts = choice.split()

    if not parts:
        return None, 0

    if parts[0] == "move":
        parts = parts[1:]

    direction = parts[0] if len(parts) >= 1 else None
    steps = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

    return direction, steps


# =========================================================
# DESTINATION CALCULATION
# =========================================================

def calculate_destination(position, direction, steps, room):
    """
    Returns:
        (new_position, actual_steps, hit_wall)
    """

    x, y = position

    if direction == "north":
        new_y = y + steps

        if new_y > room.height:
            return (x, room.height), y + steps - room.height, True

        return (x, new_y), steps, False

    if direction == "south":
        new_y = y - steps

        if new_y < 1:
            return (x, 1), y - 1, True

        return (x, new_y), steps, False

    if direction == "east":
        new_x = x + steps

        if new_x > room.width:
            return (room.width, y), x + steps - room.width, True

        return (new_x, y), steps, False

    if direction == "west":
        new_x = x - steps

        if new_x < 1:
            return (1, y), x - 1, True

        return (new_x, y), steps, False

    return position, 0, False

def get_adjacent_tile(target_pos, mover_pos, current_room):
    """Find the closest free tile adjacent to target."""
    tx, ty = target_pos
    candidates = [
        (tx + 1, ty), (tx - 1, ty),
        (tx, ty + 1), (tx, ty - 1),
        (tx + 1, ty + 1), (tx - 1, ty - 1),
        (tx + 1, ty - 1), (tx - 1, ty + 1)
    ]
    # filter valid tiles
    valid = [
        p for p in candidates
        if 1 <= p[0] <= 10 and 1 <= p[1] <= 10
        and not is_position_occupied(p, current_room)
    ]
    if not valid:
        return None
    # return closest to mover
    return min(valid, key=lambda p: abs(p[0]-mover_pos[0]) + abs(p[1]-mover_pos[1]))

def move_to_adjacent(mover, target, current_room, time_sensitive, messages=None):
    adjacent = get_adjacent_tile(target.position, mover.position, current_room)
    if not adjacent:
        log(f"{mover.name} cannot move adjacent to {target.name}; no free tiles.", messages)
        return False
    dx = abs(adjacent[0] - mover.position[0])
    dy = abs(adjacent[1] - mover.position[1])
    move_cost = dx + dy
    if time_sensitive:
        if mover.ap >= move_cost:
            mover.ap -= move_cost
            mover.position = adjacent
            log(f"{mover.name} moves adjacent to {target.name} at {adjacent}.", messages)
            return True
        else:
            log(f"{mover.name} cannot move adjacent to {target.name}; not enough AP.", messages)
            return False
    else:
        mover.position = adjacent
        log(f"{mover.name} moves adjacent to {target.name} at {adjacent}.", messages)
    return True

# =========================================================
# OCCUPANCY CHECK
# =========================================================

def is_position_occupied(position, current_room):
    """
    Checks if any entity is standing on the target tile.
    """
    return any(
        entity.position == position
        for entity in current_room.contents["entities"]
    )


# =========================================================
# SIMPLE MOVE (NON-TURN / AI USAGE)
# =========================================================

def move_character(player, direction, steps, current_room, messages=None):
    """
    Direct movement without AP system.
    """

    destination, _, _ = calculate_destination(
        player.position,
        direction,
        steps,
        current_room
    )

    if is_position_occupied(destination, current_room):
        if messages is not None:
            messages.append(f"{player.name} cannot move {direction}; blocked.")
        return

    player.position = destination
    log(f"{player.name} moves {direction} to {player.position}.")
    if messages is not None:
        messages.append(f"{player.name} moves {direction} to {player.position}.")


# =========================================================
# AI PATHING HELPER (GREEDY DIRECTION)
# =========================================================

def get_direction_toward(mover, target):
    """
    Returns a rough direction toward a target (no pathfinding).
    """

    ex, ey = mover.position
    px, py = target.position

    dx = px - ex
    dy = py - ey

    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    else:
        return "north" if dy > 0 else "south"