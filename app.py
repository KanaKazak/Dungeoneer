from logic import game

while True:
    print("Welcome to Dungeoneer!")
    print("1. Start New Game")
    print("2. Upgrade Character")
    print("3. Options")
    print("4. Exit")
    choice = input("Enter your choice: ")
    if choice == '1':
        game.start_new_game()
    elif choice == '2':
        game.upgrade_character()
    elif choice == '3':
        game.options()
    elif choice == '4':
        print("Exiting game. Goodbye!")
        exit()
    else:
        print("Invalid choice. Please try again.")
