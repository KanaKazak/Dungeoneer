import pygame
import sys
import os




sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.perks import get_available_perks
from logic import attributes
from ui.uistate import UIState
from logic.gamestate import GameState
from logic.game import initialize_game, starting_point
from logic.combat import is_within_melee_range, execute_attack
from logic.enemy_ai import enemy_turn
from logic.movement import get_adjacent_tile, move_to_adjacent
from logic.items import GoldMedal
from logic.progress import save_progress
from logic.loot import loot, execute_loot
from logic.messages import add_message

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

def move_and_act(state, target, time_sensitive, action_ap_cost, lambda_action):
    """Move player to target_pos and then perform lambda_action (like attack or loot)."""
    if move_to_adjacent(state.player, target, state.current_room, time_sensitive, messages=state.messages):
        if time_sensitive:
            if state.player.ap >= action_ap_cost:
                state.player.ap -= action_ap_cost
                lambda_action()
            else:
                add_message("Not enough AP to perform action after moving.", state.messages)
        else:
            lambda_action()

def open_loot_popup(entity, ui, state):
    ui.show_loot_popup = True
    ui.loot_target = entity
    add_message(f"What item do you want to loot from the {entity.name}'s corpse?", state.messages)

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
    ui = UIState()

    # --- Action buttons ---
    actions = ["look", "attack","inventory", "traverse", "end turn"]
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
    time_sensitive = False  # whether there are active enemies in the room
    previous_time_sensitive = False # track previous state to detect when combat starts/ends

    dungeon_map = pygame.image.load(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'maps', 'dungeon1.png')
    ).convert()
    dungeon_map = pygame.transform.scale(dungeon_map, (GRID_WIDTH, GRID_HEIGHT))
    while running:
        dt = clock.tick(FPS)  # time since last frame in ms
        previous_time_sensitive = time_sensitive
        time_sensitive = any(e for e in state.current_room.contents["entities"] if not e.is_dead and e.is_enemy)

        if previous_time_sensitive and not time_sensitive:
            state.player.reset_ap()
            ratio = state.player.carry_weight / state.player.max_carry_weight
            if ratio >= 1.5:
                state.player.ap = max(0, state.player.ap - 3)
            elif ratio >= 1.25:
                state.player.ap = max(0, state.player.ap - 2)
            elif ratio >= 1.0:
                state.player.ap = max(0, state.player.ap - 1)
            add_message("Combat over. You catch your breath.", state.messages)

        # --- INPUT ---
        mouse_pos = pygame.mouse.get_pos()
        hovered_tile = pixel_to_game(mouse_pos)
        for event in pygame.event.get():
            if event.type == "win":
                ui.show_win_screen = True
                continue
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ui.show_levelup_popup:
                    if ui.levelup_phase == 1:
                        y_offset = 150 # levelup_rect.y + 150
                        attributes = ["STR", "CON", "DEX", "AGI", "INT", "WIS", "CHA", "LUCK"]
                        for attr in attributes:
                            btn_rect = pygame.Rect(300, y_offset - 2, 40, 22)
                            if btn_rect.collidepoint(event.pos) and ui.attribute_points > 0:
                                current_value = getattr(state.player.attributes, attr)
                                setattr(state.player.attributes, attr, current_value + 1)
                                ui.attribute_points -= 1
                            y_offset += 35
                        if ui.attribute_points == 0 and pygame.Rect(120, 450, 120, 35).collidepoint(event.pos):
                            save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                            ui.levelup_phase = 2
                            ui.available_perks = get_available_perks(state.player)
                    elif ui.levelup_phase == 2:
                        if not ui.available_perks:
                            skip_rect = pygame.Rect(120, perk_rect.y + 90, 120, 35)
                            if skip_rect.collidepoint(event.pos):
                                save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                                ui.show_levelup_popup = False
                                ui.levelup_phase = 1
                        # handle perk buttons
                        for i, (perk_key, perk_data) in enumerate(ui.available_perks):
                            btn_rect = pygame.Rect(120, 100 + i * 40, 600, 30)
                            if btn_rect.collidepoint(event.pos):
                                state.player.perks.add(perk_key)
                                save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                                ui.show_levelup_popup = False
                                ui.levelup_phase = 1
                    continue  # ignore other clicks when level up popup is active
                if ui.show_inventory:
                # rebuild item_rects for click detection
                    categories = ["weapon", "consumable", "misc", "quest"]
                    y_offset = 150  # inv_rect.y + 100
                    inv_item_rects = []
                    for category in categories:
                        cat_items = [i for i in state.player.inventory if i.category == category]
                        if not cat_items:
                            continue
                        y_offset += 22
                        for item in cat_items:
                            item_rect = pygame.Rect(120, y_offset, 780, 22)
                            inv_item_rects.append((item, item_rect))
                            y_offset += 24
                        y_offset += 8
                    
                    if ui.show_item_submenu:
                        # handle submenu clicks
                        from logic.items import Weapon, Consumable
                        sub_options = []
                        if isinstance(ui.selected_item, Weapon):
                            sub_options = ["Equip", "Drop", "Examine"]
                        elif isinstance(ui.selected_item, Consumable):
                            sub_options = ["Use", "Drop", "Examine"]
                        else:
                            sub_options = ["Drop", "Examine"]
                        sx, sy = ui.submenu_pos
                        for i, opt in enumerate(sub_options):
                            opt_rect = pygame.Rect(sx + 5, sy + 5 + i * 28, 120, 24)
                            if opt_rect.collidepoint(event.pos):
                                if opt == "Equip":
                                    state.player.equipped_weapon = ui.selected_item
                                    add_message(f"Equipped {ui.selected_item.name}.", state.messages)
                                elif opt == "Use":
                                    from logic.items import Consumable, HealthPotion
                                    if isinstance(ui.selected_item, HealthPotion):
                                        state.player.hp = min(state.player.hp_max, state.player.hp + ui.selected_item.effect)
                                        state.player.inventory.remove(ui.selected_item)
                                        add_message(f"Used {ui.selected_item.name}. Restored {ui.selected_item.effect} HP.", state.messages)
                                elif opt == "Drop":
                                    state.player.inventory.remove(ui.selected_item)
                                    ui.selected_item.position = state.player.position
                                    state.current_room.contents["items"].append(ui.selected_item)
                                    add_message(f"Dropped {ui.selected_item.name}.", state.messages)
                                elif opt == "Examine":
                                    add_message(ui.selected_item.describe(), state.messages)
                                ui.show_item_submenu = False
                                ui.selected_item = None
                        continue
                    
                    # click on item
                    clicked_item = None
                    for item, rect in inv_item_rects:
                        if rect.collidepoint(event.pos):
                            clicked_item = item
                            break
                    if clicked_item:
                        ui.selected_item = clicked_item
                        ui.show_item_submenu = True
                        ui.submenu_pos = event.pos
                    else:
                        ui.show_item_submenu = False
                        ui.selected_item = None
                    continue
                if ui.show_traverse_popup:
                    exits = list(state.current_room.exits.keys())
                    for i, direction in enumerate(exits):
                        btn_rect = pygame.Rect(320, 290 + i * 40, 160, 30)
                        if btn_rect.collidepoint(event.pos):
                            state.current_room = state.current_room.exits[direction]
                            state.current_room.is_visited = True
                            state.player.position = starting_point
                            add_message(f"You move {direction}.", state.messages)
                            ui.show_traverse_popup = False
                    continue  # ignore clicks on main screen when popup is active
                if ui.show_loot_popup and ui.loot_target:
                    if ui.loot_dual_panel:
                        # click left panel — move to player
                        for i, item in enumerate(ui.loot_target.inventory):
                            btn_rect = pygame.Rect(172, 219 + i * 30, 330, 25)
                            if btn_rect.collidepoint(event.pos):
                                state.player.inventory.append(item)
                                ui.loot_target.inventory.remove(item)
                                add_message(f"You take the {item.name}.", state.messages)
                                if isinstance(item, GoldMedal):
                                    add_message("You win!", state.messages)
                                    save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                                break
                        # click right panel — drop to target
                        for i, item in enumerate(state.player.inventory):
                            btn_rect = pygame.Rect(522, 219 + i * 30, 330, 25)
                            if btn_rect.collidepoint(event.pos):
                                state.player.inventory.remove(item)
                                ui.loot_target.inventory.append(item)
                                add_message(f"You put {item.name} in the corpse.", state.messages)
                                break
                    else:
                        for i, item in enumerate(ui.loot_target.inventory):
                            btn_rect = pygame.Rect(347, 219 + i * 30, 330, 25)
                            if btn_rect.collidepoint(event.pos):
                                state.player.inventory.append(item)
                                ui.loot_target.inventory.remove(item)
                                add_message(f"You take the {item.name}.", state.messages)
                                if isinstance(item, GoldMedal):
                                    add_message("You win!", state.messages)
                                    save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                                if not ui.loot_target.inventory:
                                    ui.show_loot_popup = False
                                break
                    continue
            
                button_clicked = False
                for button in buttons:
                    if button.clicked(event.pos):
                        button_clicked = True
                        if button.text == "attack":
                            # TODO: implement attack mode
                            add_message(f"You selected: {button.text}", state.messages)
                        elif button.text == "look":
                            add_message(f"You selected: {button.text}", state.messages)
                            add_message(state.current_room.describe(), state.messages)
                        elif button.text == "inventory":
                            add_message(f"You selected: {button.text}", state.messages)
                            ui.show_inventory = not ui.show_inventory
                            ui.show_item_submenu = False
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
                                ui.show_traverse_popup = True
                                add_message(f"Which way? {', '.join(exits)}", state.messages)
                                # TODO: show direction buttons
                        elif button.text == "end turn":
                            state.player.reset_ap()
                            add_message(f"You selected: {button.text}", state.messages)
                            # enemy turns
                            for entity in state.current_room.contents["entities"]:
                                if entity.is_enemy and not entity.is_dead:
                                    enemy_turn(entity, state.player, state.current_room, state)
                            add_message("Turn ended.", state.messages)
                if not button_clicked and not ui.show_traverse_popup:
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
                                if isinstance(items[0], GoldMedal):
                                    add_message("Congratulations! You found the Gold Medal and won the game!", state.messages)
                                    save_progress(state.player.total_exp, state.player.level, state.player.attributes, state.player.perks)
                                    ####SHOW WIN SCREEN HERE INSTEAD OF EXITING IMMEDIATELY
                            else:
                                move_and_act(state, items[0], time_sensitive, state.player.loot_ap_cost(), lambda: execute_loot(state.player, items[0], state.current_room.contents["items"], time_sensitive, state))

                                
                        elif entities and entities[0].is_dead:
                            if is_within_melee_range(state.player, entities[0]):
                                ui.loot_target = entities[0]
                                ui.show_loot_popup = True
                                add_message(f"What item do you want to loot from the {entities[0].name}'s corpse?", state.messages)
                            else:
                                move_and_act(state, entities[0], time_sensitive, state.player.loot_ap_cost(), lambda: open_loot_popup(entities[0], ui, state))
                        elif entities and not entities[0].is_dead:
                            if state.player.equipped_weapon is not None and state.player.equipped_weapon.ranged:
                                if state.player.ap >= state.player.attack_ap_cost():
                                    execute_attack(state.player, entities[0], state.current_room, time_sensitive=True, state=state)
                                else:
                                    add_message("Not enough AP to attack.", state.messages)
                            else:
                                if is_within_melee_range(state.player, entities[0]):
                                    ap_cost = state.player.attack_ap_cost()
                                    if state.player.ap >= ap_cost:
                                        execute_attack(state.player, entities[0], state.current_room, time_sensitive=True, state=state)
                                    else:
                                        add_message("Not enough AP to attack.", state.messages)

                                else:
                                    move_and_act(state, entities[0], time_sensitive, state.player.attack_ap_cost(), lambda: execute_attack(state.player, entities[0], state.current_room, time_sensitive=True, state=state))
                        else:
                            if time_sensitive:
                                dx = abs(clicked_tile[0] - state.player.position[0])
                                dy = abs(clicked_tile[1] - state.player.position[1])
                                distance = dx + dy
                                if distance <= state.player.ap:
                                    state.player.ap -= distance
                                    state.player.position = clicked_tile
                                else:
                                    add_message("Not enough AP to move there.", state.messages)
                            else:
                                state.player.position = clicked_tile
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    ui.show_inventory = not ui.show_inventory
                    ui.show_item_submenu = False
                if event.key == pygame.K_ESCAPE:
                    ui.show_traverse_popup = False
                    ui.show_loot_popup = False
                if event.key == pygame.K_TAB and ui.show_loot_popup:
                    ui.loot_dual_panel = not ui.loot_dual_panel
                if event.key == pygame.K_ESCAPE:
                    if ui.show_item_submenu:
                        ui.show_item_submenu = False
                    elif ui.show_inventory:
                        ui.show_inventory = False
                    else:
                        ui.show_traverse_popup = False
                        ui.show_loot_popup = False
                        ui.loot_dual_panel = False

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


        # --- PROCESS EVENTS ---
        for event in state.events.flush():
            if event["type"] == "level_up":
                ui.show_levelup_popup = True
                ui.attribute_points = 5
                ui.available_perks = get_available_perks(state.player)
                add_message(f"You leveled up! You are now level {state.player.level}!", state.messages)

        # --- DRAW (order matters — things drawn later appear on top) ---

        # 1. Clear screen
        screen.fill((20, 20, 20))

        # 2. Grid background, with red tint in combat
        pygame.draw.rect(screen, (40, 40, 80), (GRID_X, GRID_Y, GRID_WIDTH, GRID_HEIGHT))
        screen.blit(dungeon_map, (GRID_X, GRID_Y))
        if time_sensitive:
            overlay = pygame.Surface((GRID_WIDTH, GRID_HEIGHT), pygame.SRCALPHA)
            overlay.fill((100, 0, 0, 50))  # semi-transparent red
            screen.blit(overlay, (GRID_X, GRID_Y))

        # 3. Grid lines
        for row in range(GRID_ROWS + 1):
            y = GRID_Y + row * TILE_SIZE
            pygame.draw.line(screen, (30, 30, 50), (GRID_X, y), (GRID_X + GRID_WIDTH, y), 1)
        for col in range(GRID_COLS + 1):
            x = GRID_X + col * TILE_SIZE
            pygame.draw.line(screen, (30, 30, 50), (x, GRID_Y), (x, GRID_Y + GRID_HEIGHT), 1)

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
        if ui.show_traverse_popup:
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
        
        if ui.show_loot_popup and ui.loot_target:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            
            popup_rect = pygame.Rect(300, 250, 200, 150)
            pygame.draw.rect(screen, (50, 50, 80), popup_rect)
            pygame.draw.rect(screen, (150, 150, 200), popup_rect, 2)
            title = font.render(f"Loot {ui.loot_target.name}", True, (255, 255, 255))
            screen.blit(title, (popup_rect.x + 10, popup_rect.y + 10))
            
            if ui.loot_dual_panel:
                # LEFT — target inventory
                left_rect = pygame.Rect(162, 184, 350, 400)
                pygame.draw.rect(screen, (40, 30, 30), left_rect)
                pygame.draw.rect(screen, (150, 100, 100), left_rect, 2)
                screen.blit(font.render(f"{ui.loot_target.name} (Tab to close)", True, (255, 200, 200)), (left_rect.x + 10, left_rect.y + 8))
                loot_item_rects = []
                for i, item in enumerate(ui.loot_target.inventory):
                    btn_rect = pygame.Rect(left_rect.x + 10, left_rect.y + 35 + i * 30, 330, 25)
                    loot_item_rects.append((item, btn_rect))
                    color = (100, 70, 70) if btn_rect.collidepoint(mouse_pos) else (60, 40, 40)
                    pygame.draw.rect(screen, color, btn_rect)
                    screen.blit(font.render(f"{item.name} [{item.weight}kg]", True, (255, 255, 255)), (btn_rect.x + 5, btn_rect.y + 4))
                if not ui.loot_target.inventory:
                    screen.blit(font.render("Empty.", True, (150, 150, 150)), (left_rect.x + 10, left_rect.y + 35))
                
                # RIGHT — player inventory
                right_rect = pygame.Rect(512, 184, 350, 400)
                pygame.draw.rect(screen, (30, 30, 40), right_rect)
                pygame.draw.rect(screen, (100, 100, 150), right_rect, 2)
                screen.blit(font.render("Your inventory", True, (200, 200, 255)), (right_rect.x + 10, right_rect.y + 8))
                player_loot_rects = []
                for i, item in enumerate(state.player.inventory):
                    btn_rect = pygame.Rect(right_rect.x + 10, right_rect.y + 35 + i * 30, 330, 25)
                    player_loot_rects.append((item, btn_rect))
                    color = (70, 70, 100) if btn_rect.collidepoint(mouse_pos) else (40, 40, 60)
                    pygame.draw.rect(screen, color, btn_rect)
                    screen.blit(font.render(f"{item.name} [{item.weight}kg]", True, (255, 255, 255)), (btn_rect.x + 5, btn_rect.y + 4))
                cw = state.player.carry_weight
                mcw = state.player.max_carry_weight
                screen.blit(font.render(f"Weight: {cw:.1f}/{mcw:.1f}kg", True, (200, 200, 200)), (right_rect.x + 10, right_rect.y + 370))
            
            else:
                # single panel
                popup_rect = pygame.Rect(337, 184, 350, 400)
                pygame.draw.rect(screen, (40, 30, 30), popup_rect)
                pygame.draw.rect(screen, (150, 100, 100), popup_rect, 2)
                screen.blit(font.render(f"Loot {ui.loot_target.name} (Tab for inventory)", True, (255, 255, 255)), (popup_rect.x + 10, popup_rect.y + 8))
                loot_item_rects = []
                if ui.loot_target.inventory:
                    for i, item in enumerate(ui.loot_target.inventory):
                        btn_rect = pygame.Rect(popup_rect.x + 10, popup_rect.y + 35 + i * 30, 330, 25)
                        loot_item_rects.append((item, btn_rect))
                        color = (100, 70, 70) if btn_rect.collidepoint(mouse_pos) else (60, 40, 40)
                        pygame.draw.rect(screen, color, btn_rect)
                        screen.blit(font.render(f"{item.name} [{item.weight}kg]", True, (255, 255, 255)), (btn_rect.x + 5, btn_rect.y + 4))
                else:
                    screen.blit(font.render("Nothing left.", True, (150, 150, 150)), (popup_rect.x + 10, popup_rect.y + 35))

        # 11. Inventory panel
        if ui.show_inventory:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            inv_rect = pygame.Rect(100, 50, 824, 668)
            pygame.draw.rect(screen, (30, 30, 50), inv_rect)
            pygame.draw.rect(screen, (100, 100, 150), inv_rect, 2)
            
            # title
            title = font.render("INVENTORY", True, (255, 255, 200))
            screen.blit(title, (inv_rect.x + 20, inv_rect.y + 10))
            
            # equipped weapon
            equipped_text = f"Equipped: {state.player.equipped_weapon.name}" if state.player.equipped_weapon else "Equipped: Unarmed"
            screen.blit(font.render(equipped_text, True, (200, 200, 100)), (inv_rect.x + 20, inv_rect.y + 35))
            
            # carry weight bar
            cw = state.player.carry_weight
            mcw = state.player.max_carry_weight
            weight_text = f"Weight: {cw:.1f} / {mcw:.1f} kg"
            screen.blit(font.render(weight_text, True, (255, 255, 255)), (inv_rect.x + 20, inv_rect.y + 55))
            bar_rect = pygame.Rect(inv_rect.x + 20, inv_rect.y + 75, 400, 12)
            pygame.draw.rect(screen, (60, 60, 60), bar_rect)
            fill_ratio = min(cw / mcw, 1.5)
            bar_color = (220, 50, 50) if cw > mcw else (80, 200, 80)
            pygame.draw.rect(screen, bar_color, pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * fill_ratio / 1.5), bar_rect.height))
            pygame.draw.rect(screen, (150, 150, 150), bar_rect, 1)
            
            # items by category
            categories = ["weapon", "consumable", "misc", "quest"]
            item_rects = []  # store (item, rect) for click detection
            y_offset = inv_rect.y + 100
            for category in categories:
                cat_items = [i for i in state.player.inventory if i.category == category]
                if not cat_items:
                    continue
                # category header
                header = font.render(f"-- {category.upper()} --", True, (180, 180, 100))
                screen.blit(header, (inv_rect.x + 20, y_offset))
                y_offset += 22
                for item in cat_items:
                    item_rect = pygame.Rect(inv_rect.x + 20, y_offset, 780, 22)
                    item_rects.append((item, item_rect))
                    color = (100, 100, 160) if item == ui.selected_item else (0, 0, 0, 0)
                    if item_rect.collidepoint(mouse_pos):
                        color = (70, 70, 120)
                    if color != (0, 0, 0, 0):
                        pygame.draw.rect(screen, color, item_rect)
                    item_text = f"{item.name}  [{item.weight}kg]  {item.describe()[:40]}"
                    screen.blit(font.render(item_text, True, (220, 220, 220)), (item_rect.x + 5, item_rect.y + 2))
                    y_offset += 24
                y_offset += 8

            # item submenu
            if ui.show_item_submenu and ui.selected_item:
                sx, sy = ui.submenu_pos
                sub_rect = pygame.Rect(sx, sy, 130, 90)
                pygame.draw.rect(screen, (40, 40, 60), sub_rect)
                pygame.draw.rect(screen, (150, 150, 200), sub_rect, 1)
                
                from logic.items import Weapon, Consumable
                sub_options = []
                if isinstance(ui.selected_item, Weapon):
                    sub_options = ["Equip", "Drop", "Examine"]
                elif isinstance(ui.selected_item, Consumable):
                    sub_options = ["Use", "Drop", "Examine"]
                else:
                    sub_options = ["Drop", "Examine"]
                
                for i, opt in enumerate(sub_options):
                    opt_rect = pygame.Rect(sx + 5, sy + 5 + i * 28, 120, 24)
                    color = (80, 80, 140) if opt_rect.collidepoint(mouse_pos) else (50, 50, 80)
                    pygame.draw.rect(screen, color, opt_rect)
                    screen.blit(font.render(opt, True, (255, 255, 255)), (opt_rect.x + 5, opt_rect.y + 4))
        # 12. Drawing a tooltip when mouse hovers over a tile
        if hovered_tile is not None:
            entities, items = get_tile_contents(hovered_tile, state)
            if hovered_tile == state.player.position:
                tooltip_text = f"{state.player.name} (you)"
            elif entities and not entities[0].is_dead:
                ap_cost = state.player.attack_ap_cost()
                if state.player.equipped_weapon is not None and state.player.equipped_weapon.ranged:
                    tooltip_text = f"Ranged attack {entities[0].name} — {ap_cost} AP"
                else:
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
        # 13. Level up popup
        if ui.show_levelup_popup and ui.levelup_phase == 1:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            levelup_rect = pygame.Rect(100, 50, 824, 668)
            pygame.draw.rect(screen, (30, 30, 50), levelup_rect)
            pygame.draw.rect(screen, (100, 100, 150), levelup_rect, 2)
            
            # title
            title = font.render("LEVEL UP", True, (255, 255, 200))
            screen.blit(title, (levelup_rect.x + 20, levelup_rect.y + 10))
            points_text = font.render(f"Attribute points to spend: {ui.attribute_points}", True, (255, 255, 255))
            screen.blit(points_text, (levelup_rect.x + 20, levelup_rect.y + 50))
            attributes = ["STR", "CON", "DEX", "AGI", "INT", "WIS", "CHA", "LUCK"]
            y_offset = levelup_rect.y + 100
            for attr in attributes:
                value = getattr(state.player.attributes, attr)
                attr_text = font.render(f"{attr}: {value}", True, (220, 220, 220))
                screen.blit(attr_text, (levelup_rect.x + 20, y_offset))
                
                btn_rect = pygame.Rect(levelup_rect.x + 200, y_offset - 2, 40, 22)
                color = (80, 80, 140) if btn_rect.collidepoint(mouse_pos) else (50, 50, 80)
                pygame.draw.rect(screen, color, btn_rect)
                screen.blit(font.render("+", True, (255, 255, 255)), (btn_rect.x + 14, btn_rect.y + 3))
                
                y_offset += 35
            if ui.attribute_points == 0:
                confirm_rect = pygame.Rect(levelup_rect.x + 20, levelup_rect.y + 400, 120, 35)
                color = (80, 140, 80) if confirm_rect.collidepoint(mouse_pos) else (50, 100, 50)
                pygame.draw.rect(screen, color, confirm_rect)
                screen.blit(font.render("Confirm", True, (255, 255, 255)), (confirm_rect.x + 20, confirm_rect.y + 8))
        if ui.show_levelup_popup and ui.levelup_phase == 2:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            perk_rect = pygame.Rect(100, 50, 824, 668)
            pygame.draw.rect(screen, (30, 30, 50), perk_rect)
            pygame.draw.rect(screen, (100, 100, 150), perk_rect, 2)
            
            title = font.render("Choose a Perk", True, (255, 255, 200))
            screen.blit(title, (perk_rect.x + 20, perk_rect.y + 10))
            
            if not ui.available_perks:
                screen.blit(font.render("No perks available yet.", True, (150, 150, 150)), (perk_rect.x + 20, perk_rect.y + 50))
                skip_rect = pygame.Rect(perk_rect.x + 20, perk_rect.y + 90, 120, 35)
                color = (80, 140, 80) if skip_rect.collidepoint(mouse_pos) else (50, 100, 50)
                pygame.draw.rect(screen, color, skip_rect)
                screen.blit(font.render("Skip", True, (255, 255, 255)), (skip_rect.x + 35, skip_rect.y + 8))
            
            for i, (perk_key, perk_data) in enumerate(ui.available_perks):
                btn_rect = pygame.Rect(perk_rect.x + 20, perk_rect.y + 50 + i * 40, 600, 30)
                color = (80, 80, 140) if btn_rect.collidepoint(mouse_pos) else (50, 50, 80)
                pygame.draw.rect(screen, color, btn_rect)
                screen.blit(font.render(f"{perk_data['name']} — {perk_data['description']}", True, (255, 255, 255)), (btn_rect.x + 5, btn_rect.y + 8))



        # 14. Flip to display
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()