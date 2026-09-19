from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CubeSticker:
    number: int | None = None
    rotation: int = 0

    def set_number(self, number: int) -> None:
        if number < 1 or number > 6:
            raise ValueError("Číslo políčka musí být v rozsahu 1 až 6.")

        self.number = number

    def rotate_left(self) -> None:
        self.rotation = (self.rotation - 1) % 4

    def rotate_right(self) -> None:
        self.rotation = (self.rotation + 1) % 4

    def clear(self) -> None:
        self.number = None
        self.rotation = 0

    @property
    def rotation_degrees(self) -> int:
        return self.rotation * 90

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CubeSticker:
        number = data.get("number")
        rotation = int(data.get("rotation", 0)) % 4

        if number is not None:
            number = int(number)

            if number < 1 or number > 6:
                raise ValueError(
                    "Číslo políčka v JSON musí být v rozsahu 1 až 6."
                )

        return cls(
            number=number,
            rotation=rotation,
        )