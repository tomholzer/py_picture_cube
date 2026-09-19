from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.cube_face import CubeFace, FaceName
from models.cube_sticker import CubeSticker


@dataclass(frozen=True)
class StickerPosition:
    face: FaceName
    row: int
    col: int


class CubeState:
    def __init__(self) -> None:
        self.faces: dict[FaceName, CubeFace] = {
            face_name: CubeFace(face_name)
            for face_name in FaceName
        }

    def sticker(self, position: StickerPosition) -> CubeSticker:
        return self.faces[position.face].sticker(
            position.row,
            position.col,
        )

    def set_number(
        self,
        position: StickerPosition,
        number: int,
    ) -> None:
        self.sticker(position).set_number(number)

    def rotate_left(self, position: StickerPosition) -> None:
        self.sticker(position).rotate_left()

    def rotate_right(self, position: StickerPosition) -> None:
        self.sticker(position).rotate_right()

    def clear_sticker(self, position: StickerPosition) -> None:
        self.sticker(position).clear()

    def clear_all(self) -> None:
        for face in self.faces.values():
            for row in face.stickers:
                for sticker in row:
                    sticker.clear()

    def assigned_count(self) -> int:
        count = 0

        for face in self.faces.values():
            for row in face.stickers:
                for sticker in row:
                    if sticker.number is not None:
                        count += 1

        return count

    def is_complete(self) -> bool:
        return self.assigned_count() == 54

    def to_dict(self) -> dict[str, Any]:
        stickers: list[dict[str, Any]] = []

        for face_name in FaceName:
            face = self.faces[face_name]

            for row in range(3):
                for col in range(3):
                    sticker = face.sticker(row, col)

                    stickers.append(
                        {
                            "face": face_name.value,
                            "row": row,
                            "col": col,
                            **sticker.to_dict(),
                        }
                    )

        return {
            "version": 1,
            "stickers": stickers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CubeState:
        state = cls()

        stickers_data = data.get("stickers", [])

        if not isinstance(stickers_data, list):
            raise ValueError(
                "Položka 'stickers' musí být seznam."
            )

        for item in stickers_data:
            if not isinstance(item, dict):
                continue

            face_value = item.get("face")
            row = item.get("row")
            col = item.get("col")

            if face_value is None:
                continue

            if row is None or col is None:
                continue

            face = FaceName(str(face_value))
            row = int(row)
            col = int(col)

            if not 0 <= row <= 2:
                continue

            if not 0 <= col <= 2:
                continue

            sticker = CubeSticker.from_dict(item)

            state.faces[face].stickers[row][col] = sticker

        return state