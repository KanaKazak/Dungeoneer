import pygame
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.gamestate import GameState
from logic.game import initialize_game, starting_point
from logic.combat import is_within_melee_range, execute_attack
from logic.enemy_ai import enemy_turn
from logic.movement import get_adjacent_tile, move_to_adjacent

# =============================================================================
# CONSTANTS — all layout values defined here so they're easy to tweak
# =============================================================================

# Window
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Grid (game world)
GRID_X = 10
GRID_Y = 10
GRID_COLS = 10
GRID_ROWS = 10
TILE_SIZE = 50              # each tile is 50x50 pixels
GRID_WIDTH = GRID_COLS * TILE_SIZE   # 500px total
GRID_HEIGHT = GRID_ROWS * TILE_SIZE  # 500px total

# Status bar (below the grid, same width)
STATUS_X = GRID_X
STATUS_Y = GRID_Y + GRID_HEIGHT + 10
STATUS_WIDTH = GRID_WIDTH
STATUS_HEIGHT = SCREEN_HEIGHT - STATUS_Y - 10

# Right panel (full height, right of grid)
PANEL_X = GRID_X + GRID_WIDTH + 10
PANEL_Y = 10
PANEL_WIDTH = SCREEN_WIDTH - PANEL_X - 10
PANEL_HEIGHT = SCREEN_HEIGHT - 20

# Room info (top portion of right panel)
ROOM_INFO_HEIGHT = 200

# Message log (bottom portion of right panel)
LOG_X = PANEL_X
LOG_Y = PANEL_Y + ROOM_INFO_HEIGHT + 10
LOG_WIDTH = PANEL_WIDTH
LOG_HEIGHT = PANEL_HEIGHT - ROOM_INFO_HEIGHT - 10

# =============================================================================
# HELPER FUNCTIONS — defined before main() so they're available when called
# =============================================================================

def game_to_pixel(position):
    """Convert game grid coordinates (1-10) to screen pixel coordinates."""
    col = position[0] - 1  # game coords start at 1, grid indices start at 0
    row = GRID_ROWS - position[1] # flip: game Y=1 → bottom row, Y=10 → top row
    x = GRID_X + col * TILE_SIZE
    y = GRID_Y + row * TILE_SIZE
    return x, y

def pixel_to_game(mouse_pos):
    mx, my = mouse_pos
    # check if click is inside the grid at all
    if mx < GRID_X or mx > GRID_X + GRID_WIDTH:
        return None
    if my < GRID_Y or my > GRID_Y + GRID_HEIGHT:
        return None
    col = (mx - GRID_X) // TILE_SIZE
    row = (my - GRID_Y) // TILE_SIZE
    # flip Y back to game coordinates
    game_x = col + 1
    game_y = GRID_ROWS - row
    return (game_x, game_y)

def load_frames(sheet, frame_width, frame_height):
    """Slice a spritesheet into individual animation frames."""
    frames = []
    sheet_width = sheet.get_width()
    for i in range(sheet_width // frame_width):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
        frames.append(frame)
    return frames

def add_message(text, messages):
    """Add a message to the log, keeping only the last 25."""
    messages.append(text)
    if len(messages) > 25:
        messages.pop(0)

def get_tile_contents(position, state):
    if position is None:
        return None
    entities = [e for e in state.current_room.contents["entities"] 
                if e.position == position]
    items = [i for i in state.current_room.contents["items"] 
             if i.position == position]
    return entities, items

def draw_tooltip(screen, font, mouse_pos, text):
    label = font.render(text, True, (255, 255, 255))
    w, h = label.get_size()
    rect = pygame.Rect(mouse_pos[0] + 10, mouse_pos[1] + 10, w + 10, h + 10)
    pygame.draw.rect(screen, (30, 30, 30), rect)
    pygame.draw.rect(screen, (150, 150, 150), rect, 1)  # border
    screen.blit(label, (rect.x + 5, rect.y + 5))


# =============================================================================
# BUTTON CLASS
# =============================================================================

class Button:
    def __init__(self, text, rect):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.hovered = False

    def draw(self, screen, font, active=False):
        """Draw the button, with different colors for active/hovered/normal states."""
        if active:
            color = (140, 140, 200)
        elif self.hovered:
            color = (100, 100, 160)
        else:
            color = (70, 70, 120)

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (20, 20, 20), self.rect, 2)  # dark border
        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=self.rect.center))

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# =============================================================================
# MAIN — setup and game loop
# =============================================================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeoneer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    show_traverse_popup = False
    show_loot_popup = False
    # --- Action buttons ---
    actions = ["move", "look", "attack", "loot", "inventory", "traverse", "end turn"]
    buttons = []
    btn_width = STATUS_WIDTH // len(actions)
    btn_height = 40
    for i, action in enumerate(actions):
        rect = (
            STATUS_X + i * btn_width,
            STATUS_Y + 10,
            btn_width - 5,
            btn_height
        )
        buttons.append(Button(action, rect))

    # --- Player sprite and animation ---
    player_sprite_sheet = pygame.image.load(
        os.path.join(os.path.dirname(__file__), 'sprites/Knight/Spritesheet/Hero-idle-Sheet.png')
    ).convert_alpha()
    player_FRAME_W = player_sprite_sheet.get_width() // 2
    player_FRAME_H = player_sprite_sheet.get_height()
    player_frames = load_frames(player_sprite_sheet, player_FRAME_W, player_FRAME_H)
    player_anim_index = 0
    player_anim_timer = 0
    player_anim_speed = 400  # milliseconds per frame

    facing_left = False

    # --- Enemy sprite and animation
    enemy_sprite_sheet = pygame.image.load(
        os.path.join(os.path.dirname(__file__), 'sprites\goblin-idle.png')
    ).convert_alpha()
    enemy_FRAME_W = enemy_sprite_sheet.get_width() // 3
    enemy_FRAME_H = enemy_sprite_sheet.get_height()
    enemy_frames = load_frames(enemy_sprite_sheet, enemy_FRAME_W, enemy_FRAME_H)
    enemy_anim_index = 0
    enemy_anim_timer = 0
    enemy_anim_speed = 400  # milliseconds per frame

    # ==========================================================================
    # GAME LOOP
    # ==========================================================================
    state = GameState()
    initialize_game(state)
    running = True
    loot_target = None
    time_sensitive = False  # whether there are active enemies in the room
    previous_time_sensitive = False # track previous state to detect when combat starts/ends
    while running:
        dt = clock.tick(FPS)  # time since last frame in ms
        previous_time_sensitive = time_sensitive
        time_sensitive = any(e for e in state.current_room.contents["entities"] if not e.is_dead and e.is_enemy)

        if previous_time_sensitive and not time_sensitive:
            state.player.reset_ap()
            add_message("Combat over. You catch your breath.", state.messages)

        # --- INPUT ---
        mouse_pos = pygame.mouse.get_pos()
        hovered_tile = pixel_to_game(mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if show_traverse_popup:
                    exits = list(state.current_room.exits.keys())
                    for i, direction in enumerate(exits):
                        btn_rect = pygame.Rect(320, 290 + i * 40, 160, 30)
                        if btn_rect.collidepoint(event.pos):
                            state.current_room = state.current_room.exits[direction]
                            state.current_room.is_visited = True
                            state.player.position = starting_point
                            add_message(f"You move {direction}.", state.messages)
                            show_traverse_popup = False
                    continue  # ignore clicks on main screen when popup is active
                if show_loot_popup and loot_target:
                    for i, item in enumerate(loot_target.inventory):
                        btn_rect = pygame.Rect(320, 290 + i * 35, 160, 28)
                        if btn_rect.collidepoint(event.pos):
                            state.player.inventory.append(item)
                            loot_target.inventory.remove(item)
                            add_message(f"You take the {item.name}.", state.messages)
                            if not loot_target.inventory:
                                show_loot_popup = False
                    continue
            
                button_clicked = False
                for button in buttons:
                    if button.clicked(event.pos):
                        button_clicked = True
                        if button.text == "attack":
                            # TODO: implement attack mode
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "loot":
                            # TODO: implement loot mode
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "move":
                            # TODO: implement move mode
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "look":
                            # TODO: implement look mode
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "inventory":
                            # TODO: implement inventory screen
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "traverse":

                            exits = list(state.current_room.exits.keys())
                            if len(exits) == 1:
                                # only one exit, traverse automatically
                                direction = exits[0]
                                state.current_room = state.current_room.exits[direction]
                                state.current_room.is_visited = True
                                state.player.position = starting_point
                                add_message(f"You move {direction}.", state.messages)
                            else:
                                # multiple exits — need to ask player
                                show_traverse_popup = True
                                add_message(f"Which way? {', '.join(exits)}", state.messages)
                                # TODO: show direction buttons
                        elif button.text == "end turn":
                            state.player.reset_ap()
                            add_message(f"You selected: {button.text}", state.messages)
                            # enemy turns
                            for entity in state.current_room.contents["entities"]:
                                if entity.is_enemy and not entity.is_dead:
                                    enemy_turn(entity, state.player, state.current_room, state.messages)
                            add_message("Turn ended.", state.messages)
                if not button_clicked and not show_traverse_popup:
                    time_sensitive = any(e for e in state.current_room.contents["entities"] if not e.is_dead and e.is_enemy)
                    clicked_tile = pixel_to_game(event.pos)
                    if clicked_tile is not None:
                        entities, items = get_tile_contents(clicked_tile, state)
                        if clicked_tile == state.player.position:
                            pass  # clicking yourself does nothing
                        elif items:
                            if is_within_melee_range(state.player, items[0]):
                                state.player.inventory.append(items[0])
                                state.current_room.contents["items"].remove(items[0])
                                if time_sensitive:
                                    state.player.ap -= 1  # looting costs 1 AP if there are active enemies
                                add_message(f"You pick up the {items[0].name}.", state.messages)
                            else:
                                adjacent = get_adjacent_tile(clicked_tile, state.player.position, state.current_room)
                                if move_to_adjacent(state.player, items[0], state.current_room, time_sensitive, state.messages):
                                    if time_sensitive:
                                        state.player.ap -= 1  # looting costs 1 AP if there are active enemies
                                    state.player.inventory.append(items[0])
                                    state.current_room.contents["items"].remove(items[0])
                                    add_message(f"You move next to the {items[0].name} and pick it up.", state.messages)

                                
                        elif entities and entities[0].is_dead:
                            if is_within_melee_range(state.player, entities[0]):
                                loot_target = entities[0]
                                show_loot_popup = True
                                add_message(f"What item do you want to loot from the {entities[0].name}'s corpse?", state.messages)
                            else:
                                adjacent = get_adjacent_tile(clicked_tile, state.player.position, state.current_room)
                                if move_to_adjacent(state.player, entities[0], state.current_room, time_sensitive, state.messages):
                                    show_loot_popup = True
                                    loot_target = entities[0]
                                    add_message(f"What item do you want to loot?", state.messages)
                                    if time_sensitive:
                                        if state.player.ap >= 1:
                                            state.player.ap -= 1  # looting costs 1 AP if there are active enemies
                                        else:                                            
                                            add_message("Not enough AP to loot.", state.messages)
                                            show_loot_popup = False
                        elif entities and not entities[0].is_dead:
                            if is_within_melee_range(state.player, entities[0]):
                                ap_cost = state.player.attack_ap_cost()
                                if state.player.ap >= ap_cost:
                                    execute_attack(state.player, entities[0], state.current_room, time_sensitive=True, messages=state.messages)
                                else:
                                    add_message("Not enough AP to attack.", state.messages)

                            else:
                                adjacent = get_adjacent_tile(clicked_tile, state.player.position, state.current_room)
                                if move_to_adjacent(state.player, entities[0], state.current_room, time_sensitive, state.messages):
                                    if time_sensitive:
                                        ap_cost = state.player.attack_ap_cost()
                                        if state.player.ap >= ap_cost:
                                            state.player.ap -= ap_cost
                                            execute_attack(state.player, entities[0], state.current_room, time_sensitive=True, messages=state.messages)
                                        else:
                                            add_message("Not enough AP to attack after moving.", state.messages)

                        elif items or (entities and entities[0].is_dead):
                            # loot
                            pass
                        else:
                            dx = abs(clicked_tile[0] - state.player.position[0])
                            dy = abs(clicked_tile[1] - state.player.position[1])
                            distance = dx + dy
                            if distance <= state.player.ap:
                                state.player.ap -= distance
                                state.player.position = clicked_tile
                            else:
                                add_message("Not enough AP to move there.", state.messages)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    show_traverse_popup = False
                    show_loot_popup = False

        # --- UPDATE ---
        # Advance player animation timer
        player_anim_timer += dt
        if player_anim_timer >= player_anim_speed:
            player_anim_timer = 0
            player_anim_index = (player_anim_index + 1) % len(player_frames)

        # Advance enemy animation timer
        enemy_anim_timer += dt
        if enemy_anim_timer >= enemy_anim_speed:
            enemy_anim_timer = 0
            enemy_anim_index = (enemy_anim_index + 1) % len(enemy_frames)

        # Prepare current animation frames
        player_frame = pygame.transform.scale(player_frames[player_anim_index], (TILE_SIZE - 4, TILE_SIZE - 4))
        if facing_left:
            player_frame = pygame.transform.flip(player_frame, True, False)

        enemy_frame = pygame.transform.scale(enemy_frames[enemy_anim_index], (TILE_SIZE - 4, TILE_SIZE - 4))

        # Update button hover states
        for button in buttons:
            button.update_hover(mouse_pos)


        # --- DRAW (order matters — things drawn later appear on top) ---

        # 1. Clear screen
        screen.fill((20, 20, 20))

        # 2. Grid background, with red tint in combat
        pygame.draw.rect(screen, (40, 40, 80), (GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT))
        if time_sensitive:
            overlay = pygame.Surface((GRID_WIDTH, GRID_HEIGHT), pygame.SRCALPHA)
            overlay.fill((100, 0, 0, 50))  # semi-transparent red
            screen.blit(overlay, (GRID_X, GRID_Y))

        # 3. Individual tiles
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_X + col * TILE_SIZE
                y = GRID_Y + row * TILE_SIZE
                pygame.draw.rect(screen, (50, 50, 90), (x, y, TILE_SIZE - 2, TILE_SIZE - 2))

        # 4. Character sprites (on top of tiles)

        # 4.1 Player sprite
        px, py = game_to_pixel(state.player.position)
        screen.blit(player_frame, (px + 2, py + 2))

        #4.2 Enemy sprites
        for entity in state.current_room.contents["entities"]:
            px, py = game_to_pixel(entity.position)
            screen.blit(enemy_frame, (px + 2, py + 2))

        #4.3 Item sprites
        for item in state.current_room.contents["items"]:
            ix, iy = game_to_pixel(item.position)
            pygame.draw.rect(screen, (200, 180, 50), (ix + 10, iy + 10, 30, 30))  # gold square placeholder

        # 5. Status bar
        pygame.draw.rect(screen, (60, 40, 40), (STATUS_X, STATUS_Y, STATUS_WIDTH, STATUS_HEIGHT))
        screen.blit(font.render(f"HP: {state.player.hp}/{state.player.hp_max}", True, (255, 255, 255)), (STATUS_X + 10, STATUS_Y + 60))
        if time_sensitive:
            screen.blit(font.render(f"AP: {state.player.ap}/{state.player.ap_max}", True, (255, 255, 255)), (STATUS_X + 120, STATUS_Y + 60))
        else:
            screen.blit(font.render("AP: --", True, (100, 100, 100)), (STATUS_X + 120, STATUS_Y + 60))

        # 6. Action buttons
        for button in buttons:
            button.draw(screen, font)

        # 7. Dungeon minimap panel (top right)
        pygame.draw.rect(screen, (40, 60, 40), (PANEL_X, PANEL_Y, PANEL_WIDTH, ROOM_INFO_HEIGHT))
        rooms = state.dungeon.rooms
        rooms_display = list(reversed(rooms))  # north at top, south at bottom
        spacing = ROOM_INFO_HEIGHT // len(rooms_display)
        box_w = 60
        box_h = 25
        box_x = PANEL_X + (PANEL_WIDTH - box_w) // 2  # centered
        for i, room in enumerate(rooms_display):
            box_y = PANEL_Y + i * spacing + spacing // 2
            if not room.is_visited:
                color = (30, 40, 30)  # dark for unvisited
            elif room == state.current_room:
                color = (150, 255, 150)  # bright green for current room
            else:
                color = (70, 150, 70)
            pygame.draw.rect(screen, color, (box_x, box_y - box_h // 2, box_w, box_h))
            has_enemies = any(e for e in room.contents["entities"] if not e.is_dead)


            if has_enemies and room.is_visited:
                pygame.draw.circle(screen, (220, 50, 50), (box_x + box_w - 10, box_y), 5) ###TO BE REPLACED WITH ENEMY ICON

        # 8. Message log (bottom right)
        pygame.draw.rect(screen, (50, 50, 70), (LOG_X, LOG_Y, LOG_WIDTH, LOG_HEIGHT))
        log_y = LOG_Y + 10
        for msg in state.messages:
            label = font.render(msg, True, (220, 220, 220))
            screen.blit(label, (LOG_X + 10, log_y))
            log_y += 20

        # 9. Traverse popup
        if show_traverse_popup:
            # draw dark overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))  # semi-transparent black
            screen.blit(overlay, (0, 0))
            
            # draw popup box
            popup_rect = pygame.Rect(300, 250, 200, 150)
            pygame.draw.rect(screen, (50, 50, 80), popup_rect)
            pygame.draw.rect(screen, (150, 150, 200), popup_rect, 2)
            
            # title
            title = font.render("Which way?", True, (255, 255, 255))
            screen.blit(title, (popup_rect.x + 10, popup_rect.y + 10))
            
            # direction buttons
            exits = list(state.current_room.exits.keys())
            popup_buttons = []
            for i, direction in enumerate(exits):
                direction_labels = {
                    "north": ">> Forward (North)",
                    "south": "<< Back (South)",
                    "east": ">> East",
                    "west": "<< West"
                }
                label_text = direction_labels.get(direction, direction)
                btn_rect = pygame.Rect(popup_rect.x + 20, popup_rect.y + 40 + i * 40, 160, 30)
                popup_buttons.append((direction, btn_rect))
                color = (100, 100, 160) if btn_rect.collidepoint(mouse_pos) else (70, 70, 120)
                pygame.draw.rect(screen, color, btn_rect)
                label = font.render(label_text, True, (255, 255, 255))
                screen.blit(label, label.get_rect(center=btn_rect.center))

        # 10. Loot popup
        if show_loot_popup and loot_target:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            
            popup_rect = pygame.Rect(300, 250, 200, 150)
            pygame.draw.rect(screen, (50, 50, 80), popup_rect)
            pygame.draw.rect(screen, (150, 150, 200), popup_rect, 2)
            title = font.render(f"Loot {loot_target.name}", True, (255, 255, 255))
            screen.blit(title, (popup_rect.x + 10, popup_rect.y + 10))
            
            if loot_target.inventory:
                for i, item in enumerate(loot_target.inventory):
                    btn_rect = pygame.Rect(popup_rect.x + 20, popup_rect.y + 40 + i * 35, 160, 28)
                    color = (100, 100, 160) if btn_rect.collidepoint(mouse_pos) else (70, 70, 120)
                    pygame.draw.rect(screen, color, btn_rect)
                    label = font.render(item.name, True, (255, 255, 255))
                    screen.blit(label, label.get_rect(center=btn_rect.center))
            else:
                screen.blit(font.render("Nothing left.", True, (180, 180, 180)), 
                        (popup_rect.x + 10, popup_rect.y + 40))


        # 11. Drawing a tooltip when mouse hovers over a tile
        if hovered_tile is not None:
            entities, items = get_tile_contents(hovered_tile, state)
            if hovered_tile == state.player.position:
                tooltip_text = f"{state.player.name} (you)"
            elif entities and not entities[0].is_dead:
                ap_cost = state.player.attack_ap_cost()
                if is_within_melee_range(state.player, entities[0]):
                    tooltip_text = f"Attack {entities[0].name} — {ap_cost} AP"
                else:
                    dx = abs(hovered_tile[0] - state.player.position[0])
                    dy = abs(hovered_tile[1] - state.player.position[1])
                    move_cost = max(0, dx + dy - 1)
                    tooltip_text = f"Attack {entities[0].name} — move ({move_cost}) + attack ({ap_cost}) AP"
            elif entities and entities[0].is_dead:
                entity = entities[0]
                status = "(dead)"
                tooltip_text = f"{entity.name} {status}"
            elif items:
                tooltip_text = f"{items[0].name}"
            else:
                dx = abs(hovered_tile[0] - state.player.position[0])
                dy = abs(hovered_tile[1] - state.player.position[1])
                distance = dx + dy
                tooltip_text = f"Move here (distance: {distance})"
            draw_tooltip(screen, font, mouse_pos, tooltip_text)

        # 12. Flip to display
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()