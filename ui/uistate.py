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