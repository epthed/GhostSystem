from random import randint


def hits(dice: int) -> int:
    successes = 0
    ones = 0
    for die in range(dice):
        if randint(1, 6) >= 4:
            successes += 1

    return successes
