import math

def user_pint_A():
    """
    Write a program that asks the user to enter a number and then prints out the letter A that many times,
    all on the same line.
    """
    num = int(input("Enter a number: "))
    print("A" * num)

if __name__ == "__main__":
    user_pint_A()