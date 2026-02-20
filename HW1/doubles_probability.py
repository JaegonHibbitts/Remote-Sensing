import math

def probability_of_doubles(num_sides):
    """
    Recall our study of probabilities in ENME 392. Here we estimate the probability of rolling doubles with
    two dice (“doubles” is defined here as the event where both dice land on the same value on a particular
    roll). Create a program that runs a loop 10,000 times in which random numbers are generated
    representing the dice (one unique random number per dice) and a count is recorded of how many times
    doubles appear. Print out the final percentage of rolls that are doubles after the 10,000 rolls are
    complete, i.e. how many out of the 10,000 rolls resulted in doubles?
    """

    # Your code here
    import random

    num_trials = 10000
    doubles_count = 0

    for _ in range(num_trials):
        die1 = random.randint(1, num_sides)
        die2 = random.randint(1, num_sides)

        if die1 == die2:
            doubles_count += 1

    probability = (doubles_count / num_trials) * 100
    print(f"Probability of rolling doubles with {num_sides}-sided dice: {probability:.2f}%")

if __name__ == "__main__":
    num_sides = int(input("Enter the number of sides on the dice: "))
    probability_of_doubles(num_sides)

