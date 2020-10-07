from typing import Tuple


class Entity:
    """
    A generic object to represent players and enemies and items etc
    """

    def __init__(self, x: int, y: int, char: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx: int, dy: int) -> None:
        # move by applying delta x+y to entity
        self.x += dx
        self.y += dy
