import properties


def create_group():
    pass


def save_group():
    pass


def load_group():
    pass


def run_group():
    pass


if __name__ == '__main__':
    while True:
        print(properties.group_menu)
        choice = input("\nPlease enter the number to select: ")
        if choice == '1':
            print("\nCreating group...")
            create_group()
        elif choice == '2':
            print("\nSaving group...")
            save_group()
        elif choice == '3':
            print("\nLoading group...")
            load_group()
        elif choice == '4':
            print("\nRunning group...")
            run_group()
        elif choice == '5':
            quit(0)
        else:
            print("\nNo such option available!")
