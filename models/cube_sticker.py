from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CubeSticker:
    target_face: int | None = None
    target_position: int | None = None
    rotation: int = 0

    def set_target_face(
        self,
        target_face: int,
    ) -> None:
        if not 1 <= target_face <= 6:
            raise ValueError(
                "Cílová strana musí být v rozsahu 1 až 6."
            )

        self.target_face = target_face

    def set_target_position(
        self,
        target_position: int,
    ) -> None:
        if not 1 <= target_position <= 9:
            raise ValueError(
                "Pozice obrázku musí být v rozsahu 1 až 9."
            )

        self.target_position = target_position

    def rotate_left(self) -> None:
        if self.target_position is None:
            return

        self.rotation = (
            self.rotation - 1
        ) % 4

    def rotate_right(self) -> None:
        if self.target_position is None:
            return

        self.rotation = (
            self.rotation + 1
        ) % 4

    def clear_target_face(self) -> None:
        self.target_face = None

    def clear_target_position(self) -> None:
        self.target_position = None

        # Natočení bez pozice obrázku nemá význam.
        self.rotation = 0

    def clear(self) -> None:
        self.target_face = None
        self.target_position = None
        self.rotation = 0

    @property
    def rotation_degrees(self) -> int:
        return self.rotation * 90

    @property
    def is_defined(self) -> bool:
        return (
            self.target_face is not None
            and self.target_position is not None
        )

    @property
    def is_partial(self) -> bool:
        return (
            self.target_face is not None
            or self.target_position is not None
        ) and not self.is_defined

    @property
    def can_rotate(self) -> bool:
        return self.target_position is not None

    @property
    def target_key(
        self,
    ) -> tuple[int, int] | None:
        if not self.is_defined:
            return None

        assert self.target_face is not None
        assert self.target_position is not None

        return (
            self.target_face,
            self.target_position,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_face": self.target_face,
            "target_position": self.target_position,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> CubeSticker:
        # Kompatibilita se starší verzí,
        # kde byla strana uložená jako "number".
        target_face_raw = data.get(
            "target_face",
            data.get("number"),
        )

        target_position_raw = data.get(
            "target_position"
        )

        target_face: int | None = None
        target_position: int | None = None

        if target_face_raw is not None:
            target_face = int(
                target_face_raw
            )

            if not 1 <= target_face <= 6:
                raise ValueError(
                    "Cílová strana v JSON musí být 1 až 6."
                )

        if target_position_raw is not None:
            target_position = int(
                target_position_raw
            )

            if not 1 <= target_position <= 9:
                raise ValueError(
                    "Pozice obrázku v JSON musí být 1 až 9."
                )

        rotation = int(
            data.get(
                "rotation",
                0,
            )
        ) % 4

        # Bez zadané pozice obrázku
        # nemá natočení význam.
        if target_position is None:
            rotation = 0

        return cls(
            target_face=target_face,
            target_position=target_position,
            rotation=rotation,
        )