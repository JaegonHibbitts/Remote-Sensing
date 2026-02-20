import math

def ten_numbers():
    """
    Write a program that asks the user to enter 10 numbers. Once the 10 numbers have been entered,
    evaluate and print out the two smallest numbers entered (hint: they may have the same value). Your
    code should exclude duplicates – for example, if the user entered [ 1, 2, 4, 3, 1, 1, 6, 8, 9, 5] the output
    should be [1, 2].
    """

    numbers = []
    for i in range(10):
        num = float(input(f"Enter number {i+1}: "))
        numbers.append(num)

    numbers.sort()
    smallest_two = numbers[:2]
    print(f"The two smallest numbers entered are: {smallest_two}")

if __name__ == "__main__":
    ten_numbers()

