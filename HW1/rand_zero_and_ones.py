import math

def rand_zero_and_ones():
    """
    Write a program that generates and prints a series of 10 random
    zeroes and ones all on the same line, with no spaces between them.
    Then, on the next line, perform the same operation with 11 random
    zeroes and ones. On the next line do the same but with 12 random
    zeroes and ones. Continue this process for a total of 50 lines, each
    with one more random value (zero or one) than the previous line.
    """

    import random

    for i in range(10, 60):
        line = ''.join(str(random.randint(0, 1)) for _ in range(i))
        print(line)
    
if __name__ == "__main__":
    rand_zero_and_ones()

