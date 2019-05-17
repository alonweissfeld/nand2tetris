import random

LEVELS_AMOUNT = 40;

text_directions = ['UP', 'RIGHT', 'DOWN', 'LEFT']

for i in range(LEVELS_AMOUNT):
    # As advancing levels, make the delay time lower which means
    # faster response from the user, i.e., harder levels.
    delay = None
    if i < 0.2 * LEVELS_AMOUNT:
        delay = random.randint(20, 30)
    elif i >= 0.2 * LEVELS_AMOUNT and i < 0.4 * LEVELS_AMOUNT:
        delay = random.randint(10, 20)
    elif i >= 0.4 * LEVELS_AMOUNT and i < 0.6 * LEVELS_AMOUNT:
        delay = random.randint(5, 10)
    elif i >= 0.6 * LEVELS_AMOUNT and i < 0.8 * LEVELS_AMOUNT:
        delay = random.randint(3, 7)
    else: # Last levels are a mix of difficulties.
        delay = random.randint(3, 15)

    # Shuffle directions every 5 iterations for more "randomness".
    if i % 5 == 0:
        random.shuffle(text_directions)

    square_direction = random.randint(1, 4)
    text_direction = random.choice(text_directions)
    line = 'let levels[{}] = Level.new({}, {}, "{}");'.format(
        i, square_direction, delay, text_direction
    )

    print line
