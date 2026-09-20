from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.cube_face import (
    CubeFace,
    FaceName,
)
from models.cube_sticker import CubeSticker


@dataclass(frozen=True)
class StickerPosition:
    face: FaceName
    row: int
    col: int


@dataclass(frozen=True)
class DuplicateTarget:
    target_face: int
    target_position: int
    positions: tuple[
        StickerPosition,
        ...,
    ]


class CubeState:
    def __init__(self) -> None:
        self.faces: dict[
            FaceName,
            CubeFace,
        ] = {
            face_name: CubeFace(
                face_name
            )
            for face_name in FaceName
        }

    def sticker(
        self,
        position: StickerPosition,
    ) -> CubeSticker:
        return self.faces[
            position.face
        ].sticker(
            position.row,
            position.col,
        )

    def set_target_face(
        self,
        position: StickerPosition,
        target_face: int,
    ) -> None:
        self.sticker(
            position
        ).set_target_face(
            target_face
        )

    def set_target_position(
        self,
        position: StickerPosition,
        target_position: int,
    ) -> None:
        self.sticker(
            position
        ).set_target_position(
            target_position
        )

    def clear_target_face(
        self,
        position: StickerPosition,
    ) -> None:
        self.sticker(
            position
        ).clear_target_face()

    def clear_target_position(
        self,
        position: StickerPosition,
    ) -> None:
        self.sticker(
            position
        ).clear_target_position()

    def rotate_left(
        self,
        position: StickerPosition,
    ) -> None:
        self.sticker(
            position
        ).rotate_left()

    def rotate_right(
        self,
        position: StickerPosition,
    ) -> None:
        self.sticker(
            position
        ).rotate_right()

    def clear_sticker(
        self,
        position: StickerPosition,
    ) -> None:
        self.sticker(
            position
        ).clear()

    def clear_all(self) -> None:
        for face in self.faces.values():
            for row in face.stickers:
                for sticker in row:
                    sticker.clear()

    def iter_positions(
        self,
    ) -> list[StickerPosition]:
        result: list[
            StickerPosition
        ] = []

        for face in FaceName:
            for row in range(3):
                for col in range(3):
                    result.append(
                        StickerPosition(
                            face=face,
                            row=row,
                            col=col,
                        )
                    )

        return result

    def defined_count(self) -> int:
        return sum(
            1
            for position
            in self.iter_positions()
            if self.sticker(
                position
            ).is_defined
        )

    def partially_defined_count(
        self,
    ) -> int:
        return sum(
            1
            for position
            in self.iter_positions()
            if self.sticker(
                position
            ).is_partial
        )

    def find_target_owner(
        self,
        target_face: int,
        target_position: int,
        exclude: StickerPosition | None = None,
    ) -> StickerPosition | None:
        for position in self.iter_positions():
            if (
                exclude is not None
                and position == exclude
            ):
                continue

            sticker = self.sticker(
                position
            )

            if (
                sticker.target_face == target_face
                and sticker.target_position == target_position
            ):
                return position

        return None


    def find_duplicates(
        self,
    ) -> list[DuplicateTarget]:
        target_positions: dict[
            tuple[int, int],
            list[StickerPosition],
        ] = {}

        for position in self.iter_positions():
            sticker = self.sticker(
                position
            )

            target_key = (
                sticker.target_key
            )

            if target_key is None:
                continue

            target_positions.setdefault(
                target_key,
                [],
            ).append(
                position
            )

        duplicates: list[
            DuplicateTarget
        ] = []

        for (
            target_face,
            target_position,
        ), positions in (
            target_positions.items()
        ):
            if len(positions) <= 1:
                continue

            duplicates.append(
                DuplicateTarget(
                    target_face=(
                        target_face
                    ),
                    target_position=(
                        target_position
                    ),
                    positions=tuple(
                        positions
                    ),
                )
            )

        return duplicates

    def missing_targets(
        self,
    ) -> list[
        tuple[int, int]
    ]:
        expected = {
            (
                target_face,
                target_position,
            )
            for target_face
            in range(1, 7)
            for target_position
            in range(1, 10)
        }

        used: set[
            tuple[int, int]
        ] = set()

        for position in self.iter_positions():
            target_key = (
                self.sticker(
                    position
                ).target_key
            )

            if target_key is not None:
                used.add(
                    target_key
                )

        return sorted(
            expected - used
        )

    def is_complete(self) -> bool:
        return (
            self.defined_count() == 54
            and not self.find_duplicates()
            and not self.missing_targets()
        )

    def validation_messages(
        self,
    ) -> list[str]:
        messages: list[str] = []

        partial_count = (
            self.partially_defined_count()
        )

        if partial_count > 0:
            messages.append(
                "Neúplně zadaných políček: "
                f"{partial_count}"
            )

        duplicates = (
            self.find_duplicates()
        )

        for duplicate in duplicates:
            messages.append(
                "Duplicitní dílek: "
                f"strana "
                f"{duplicate.target_face}, "
                f"pozice "
                f"{duplicate.target_position}"
            )

        missing = (
            self.missing_targets()
        )

        if missing:
            messages.append(
                "Chybějících dílků: "
                f"{len(missing)}"
            )

        return messages

    def to_dict(
        self,
    ) -> dict[str, Any]:
        stickers: list[
            dict[str, Any]
        ] = []

        for face_name in FaceName:
            face = self.faces[
                face_name
            ]

            for row in range(3):
                for col in range(3):
                    sticker = (
                        face.sticker(
                            row,
                            col,
                        )
                    )

                    stickers.append(
                        {
                            "face": (
                                face_name.value
                            ),
                            "row": row,
                            "col": col,
                            **sticker.to_dict(),
                        }
                    )

        return {
            "version": 2,
            "stickers": stickers,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> CubeState:
        state = cls()

        stickers_data = data.get(
            "stickers",
            [],
        )

        if not isinstance(
            stickers_data,
            list,
        ):
            raise ValueError(
                "Položka 'stickers' musí být seznam."
            )

        for item in stickers_data:
            if not isinstance(
                item,
                dict,
            ):
                continue

            face_value = item.get(
                "face"
            )

            row_raw = item.get(
                "row"
            )

            col_raw = item.get(
                "col"
            )

            if face_value is None:
                continue

            if (
                row_raw is None
                or col_raw is None
            ):
                continue

            face = FaceName(
                str(
                    face_value
                )
            )

            row = int(
                row_raw
            )

            col = int(
                col_raw
            )

            if not 0 <= row <= 2:
                continue

            if not 0 <= col <= 2:
                continue

            sticker = (
                CubeSticker.from_dict(
                    item
                )
            )

            state.faces[
                face
            ].stickers[
                row
            ][
                col
            ] = sticker

        return state