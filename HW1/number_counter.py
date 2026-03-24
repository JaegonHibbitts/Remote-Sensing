import math

def number_counter():
    count = 0
    entered_less_than_3 = False

    while True:
        num = int(input("Enter a number from 1 to 10 (enter 5 to stop): "))
        if num == 5:
            break
        count += 1
        if num < 3:
            entered_less_than_3 = True

    print(f"Total numbers entered: {count}")
    print(f"Did the user enter any numbers less than 3? {'Yes' if entered_less_than_3 else 'No'}")

if __name__ == "__main__":
    number_counter()
