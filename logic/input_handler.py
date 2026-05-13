from logic.progress import save_progress

def get_input(prompt, player):
    command = input(prompt).lower()
    if command == "quit game" and player is not None:
        print("Quitting game...")
        save_progress(player.total_exp, player.level, player.attributes)
        exit()
    return command