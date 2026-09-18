"""Core bingo game logic shared by the API - 75-ball classic bingo."""

import random
from typing import Optional

COLUMN_RANGES = {
    "B": (1, 15),
    "I": (16, 30),
    "N": (31, 45),
    "G": (46, 60),
    "O": (61, 75),
}


def generate_card() -> list:
    """Returns a 5x5 card as a flat list of 25 ints (row-major), None for FREE."""
    columns = []
    for letter, (low, high) in COLUMN_RANGES.items():
        columns.append(random.sample(range(low, high + 1), 5))
    card = []
    for r in range(5):
        for c in range(5):
            card.append(columns[c][r])
    card[12] = None  # center FREE space
    return card


def check_win(card: list, marked: set) -> bool:
    def is_marked(v):
        return v is None or v in marked

    grid = [card[i * 5:(i + 1) * 5] for i in range(5)]

    for row in grid:
        if all(is_marked(v) for v in row):
            return True
    for c in range(5):
        if all(is_marked(grid[r][c]) for r in range(5)):
            return True
    if all(is_marked(grid[i][i]) for i in range(5)):
        return True
    if all(is_marked(grid[i][4 - i]) for i in range(5)):
        return True
    return False


def letter_for_number(n: int) -> str:
    for letter, (low, high) in COLUMN_RANGES.items():
        if low <= n <= high:
            return letter
    return "?"
