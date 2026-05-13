import pygame
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.gamestate import GameState
from logic.game import initialize_game
from logic.combat import is_within_melee_range

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
    """Add a message to the log, keeping only the last 6."""
    messages.append(text)
    if len(messages) > 6:
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

    # --- Message log ---



    # --- Action buttons ---
    actions = ["move", "look", "attack", "loot", "inventory", "traverse"]
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
        "C:/kanagat/Dungeoneer/ui/sprites/Knight/Spritesheet/Hero-idle-Sheet.png"
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
        "C:/kanagat/Dungeoneer/ui/sprites/goblin idle.png"
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
    while running:
        dt = clock.tick(FPS)  # time since last frame in ms

        # --- INPUT ---
        mouse_pos = pygame.mouse.get_pos()
        hovered_tile = pixel_to_game(mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.clicked(event.pos):
                        add_message(f"You selected: {button.text}", state.messages)

        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_tile = pixel_to_game(event.pos)
            if clicked_tile is not None:
                entities, items = get_tile_contents(clicked_tile, state)
                if clicked_tile == state.player.position:
                    pass  # clicking yourself does nothing
                elif entities and not entities[0].is_dead:
                    # attack
                    pass
                elif items or (entities and entities[0].is_dead):
                    # loot
                    pass
                else:
                    # move
                    state.player.position = clicked_tile
                    pass


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

        # 2. Grid background
        pygame.draw.rect(screen, (40, 40, 80), (GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT))

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

        # 5. Status bar
        pygame.draw.rect(screen, (60, 40, 40), (STATUS_X, STATUS_Y, STATUS_WIDTH, STATUS_HEIGHT))
        screen.blit(font.render("HP: 100", True, (255, 255, 255)), (STATUS_X + 10, STATUS_Y + 60))
        screen.blit(font.render("AP: 4", True, (255, 255, 255)), (STATUS_X + 120, STATUS_Y + 60))

        # 6. Action buttons
        for button in buttons:
            button.draw(screen, font)

        # 7. Room info panel (top right)
        pygame.draw.rect(screen, (40, 60, 40), (PANEL_X, PANEL_Y, PANEL_WIDTH, ROOM_INFO_HEIGHT))
        room_name_text = state.current_room.name
        room_exits_text = "Exits: " + ", " .join(state.current_room.exits.keys())
        items_in_room_text = "Items: " + ", ".join(item.name for item in state.current_room.contents["items"]) or "None"
        screen.blit(font.render(room_name_text, True, (255, 255, 255)), (PANEL_X + 10, PANEL_Y + 10))
        screen.blit(font.render(room_exits_text, True, (255, 255, 255)), (PANEL_X + 10, PANEL_Y + 30))
        screen.blit(font.render(items_in_room_text, True, (255, 255, 255)), (PANEL_X + 10, PANEL_Y + 50))

        # 8. Message log (bottom right)
        pygame.draw.rect(screen, (50, 50, 70), (LOG_X, LOG_Y, LOG_WIDTH, LOG_HEIGHT))
        log_y = LOG_Y + 10
        for msg in state.messages:
            label = font.render(msg, True, (220, 220, 220))
            screen.blit(label, (LOG_X + 10, log_y))
            log_y += 20

        # 9. Drawing a tooltip when mouse hovers over a tile
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

        # 10. Flip to display
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()