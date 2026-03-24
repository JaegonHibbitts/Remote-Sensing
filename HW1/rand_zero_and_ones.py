import math
import random

def rand_zero_and_ones():

    for i in range(10, 60):
        line = ''.join(str(random.randint(0, 1)) for _ in range(i))
        print(line)
    
if __name__ == "__main__":
    rand_zero_and_ones()

