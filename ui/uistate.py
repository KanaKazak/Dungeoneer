class UIState:
    def __init__(self):
        self.show_loot_popup = False
        self.loot_target = None
        self.show_traverse_popup = False
        self.show_inventory = False
        self.selected_item = None
        self.show_item_submenu = False
        self.submenu_pos = None
        self.loot_dual_panel = False
        self.show_levelup_popup = False
        self.attribute_points = 0
        self.available_perks = []
        self.levelup_phase = 1
        show_win_screen = False