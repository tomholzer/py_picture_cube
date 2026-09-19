from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from models.cube_sticker import CubeSticker


class FaceName(str, Enum):
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


@dataclass
class CubeFace:
    name: FaceName
    stickers: list[list[CubeSticker]] = field(
        default_factory=lambda: [
            [CubeSticker() for _ in range(3)]
            for _ in range(3)
        ]
    )

    def sticker(self, row: int, col: int) -> CubeSticker:
        if not 0 <= row <= 2:
            raise IndexError("Řádek musí být v rozsahu 0 až 2.")

        if not 0 <= col <= 2:
            raise IndexError("Sloupec musí být v rozsahu 0 až 2.")

        return self.stickers[row][col]