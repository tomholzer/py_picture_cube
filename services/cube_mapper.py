from __future__ import annotations

from dataclasses import dataclass

from models.cube_face import FaceName
from models.cube_state import CubeState, StickerPosition


Vector3 = tuple[int, int, int]


@dataclass(frozen=True)
class CubeMappingResult:
    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    facelet_string: str | None
    target_face_to_physical: dict[int, FaceName]
    target_face_to_letter: dict[int, str]


class CubeMapper:
    FACE_TO_LETTER: dict[FaceName, str] = {
        FaceName.UP: "U",
        FaceName.RIGHT: "R",
        FaceName.FRONT: "F",
        FaceName.DOWN: "D",
        FaceName.LEFT: "L",
        FaceName.BACK: "B",
    }

    KOCIEMBA_FACE_ORDER: tuple[FaceName, ...] = (
        FaceName.UP,
        FaceName.RIGHT,
        FaceName.FRONT,
        FaceName.DOWN,
        FaceName.LEFT,
        FaceName.BACK,
    )

    def _target_position_type(
        self,
        target_position: int,
    ) -> str:
        if target_position == 5:
            return "střed"

        if target_position in (
            2,
            4,
            6,
            8,
        ):
            return "hrana"

        if target_position in (
            1,
            3,
            7,
            9,
        ):
            return "roh"

        return "neznámý"

    def map(
        self,
        cube_state: CubeState,
    ) -> CubeMappingResult:
        errors: list[str] = []
        warnings: list[str] = []

        self._validate_basic_state(
            cube_state,
            errors,
        )

        if errors:
            return CubeMappingResult(
                is_valid=False,
                errors=tuple(errors),
                warnings=tuple(warnings),
                facelet_string=None,
                target_face_to_physical={},
                target_face_to_letter={},
            )

        target_face_to_physical = (
            self._build_center_mapping(
                cube_state,
                errors,
            )
        )

        if errors:
            return CubeMappingResult(
                is_valid=False,
                errors=tuple(errors),
                warnings=tuple(warnings),
                facelet_string=None,
                target_face_to_physical=target_face_to_physical,
                target_face_to_letter={},
            )

        target_face_to_letter = {
            target_face: self.FACE_TO_LETTER[
                physical_face
            ]
            for target_face, physical_face
            in target_face_to_physical.items()
        }

        self._validate_cubie_identity(
            cube_state=cube_state,
            target_face_to_physical=target_face_to_physical,
            errors=errors,
        )

        self._check_center_rotations(
            cube_state,
            warnings,
        )

        if errors:
            return CubeMappingResult(
                is_valid=False,
                errors=tuple(errors),
                warnings=tuple(warnings),
                facelet_string=None,
                target_face_to_physical=target_face_to_physical,
                target_face_to_letter=target_face_to_letter,
            )

        facelet_string = (
            self._build_facelet_string(
                cube_state=cube_state,
                target_face_to_letter=target_face_to_letter,
                errors=errors,
            )
        )

        return CubeMappingResult(
            is_valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
            facelet_string=(
                facelet_string
                if not errors
                else None
            ),
            target_face_to_physical=target_face_to_physical,
            target_face_to_letter=target_face_to_letter,
        )

    def _validate_basic_state(
        self,
        cube_state: CubeState,
        errors: list[str],
    ) -> None:
        if cube_state.defined_count() != 54:
            errors.append(
                "Kostka není kompletně zadaná. "
                f"Kompletních dílků: "
                f"{cube_state.defined_count()} / 54."
            )

        partial_count = (
            cube_state.partially_defined_count()
        )

        if partial_count:
            errors.append(
                "Kostka obsahuje "
                f"{partial_count} neúplně zadaných dílků."
            )

        duplicates = (
            cube_state.find_duplicates()
        )

        for duplicate in duplicates:
            errors.append(
                "Dílek "
                f"S{duplicate.target_face}/"
                f"{duplicate.target_position} "
                "je použit více než jednou."
            )

        missing = (
            cube_state.missing_targets()
        )

        if missing:
            preview = ", ".join(
                f"S{face}/{position}"
                for face, position
                in missing[:10]
            )

            if len(missing) > 10:
                preview += ", ..."

            errors.append(
                "Chybí cílové dílky: "
                f"{preview}"
            )

    def _build_center_mapping(
        self,
        cube_state: CubeState,
        errors: list[str],
    ) -> dict[int, FaceName]:
        result: dict[int, FaceName] = {}

        for physical_face in FaceName:
            center_position = StickerPosition(
                face=physical_face,
                row=1,
                col=1,
            )

            sticker = cube_state.sticker(
                center_position
            )

            if sticker.target_face is None:
                errors.append(
                    "Střed fyzické strany "
                    f"{physical_face.value} "
                    "nemá zadanou cílovou stranu."
                )
                continue

            if sticker.target_position != 5:
                errors.append(
                    "Střed fyzické strany "
                    f"{physical_face.value} "
                    "musí být pozice 5, "
                    "ale je zadán jako "
                    f"S{sticker.target_face}/"
                    f"{sticker.target_position}."
                )

            if sticker.target_face in result:
                old_face = result[
                    sticker.target_face
                ]

                errors.append(
                    f"Cílová strana "
                    f"{sticker.target_face} "
                    "je použita jako střed na "
                    f"{old_face.value} i "
                    f"{physical_face.value}."
                )
                continue

            result[
                sticker.target_face
            ] = physical_face

        expected = set(
            range(1, 7)
        )

        missing_faces = (
            expected - set(result)
        )

        if missing_faces:
            errors.append(
                "Ve středech chybí cílové strany: "
                + ", ".join(
                    str(value)
                    for value in sorted(
                        missing_faces
                    )
                )
            )

        return result

    def _validate_cubie_identity(
        self,
        cube_state: CubeState,
        target_face_to_physical: dict[
            int,
            FaceName,
        ],
        errors: list[str],
    ) -> None:
        current_groups: dict[
            Vector3,
            list[StickerPosition],
        ] = {}

        for position in cube_state.iter_positions():
            coordinate = self._cubie_coordinate(
                position.face,
                position.row,
                position.col,
            )

            current_groups.setdefault(
                coordinate,
                [],
            ).append(
                position
            )

        used_target_cubies: dict[
            Vector3,
            Vector3,
        ] = {}

        for (
            current_coordinate,
            positions,
        ) in current_groups.items():
            current_type = self._cubie_type(
                current_coordinate
            )

            expected_sticker_count = {
                "střed": 1,
                "hrana": 2,
                "roh": 3,
            }.get(
                current_type
            )

            if (
                expected_sticker_count is not None
                and len(positions)
                != expected_sticker_count
            ):
                errors.append(
                    f"Chybná geometrie fyzického kamene "
                    f"{current_coordinate}: "
                    f"{current_type} má "
                    f"{len(positions)} políček, "
                    f"očekáváno "
                    f"{expected_sticker_count}."
                )

                continue

            target_coordinates: list[
                Vector3
            ] = []

            labels: list[str] = []

            for position in positions:
                sticker = cube_state.sticker(
                    position
                )

                if (
                    sticker.target_face is None
                    or sticker.target_position is None
                ):
                    continue

                labels.append(
                    f"S{sticker.target_face}/"
                    f"{sticker.target_position}"
                )

                target_position_type = (
                    self._target_position_type(
                        sticker.target_position
                    )
                )

                if (
                    target_position_type
                    != current_type
                ):
                    errors.append(
                        f"Na fyzické pozici typu "
                        f"'{current_type}' je zadán dílek "
                        f"S{sticker.target_face}/"
                        f"{sticker.target_position}, "
                        f"který patří na pozici typu "
                        f"'{target_position_type}'."
                    )

                    continue

                target_physical_face = (
                    target_face_to_physical.get(
                        sticker.target_face
                    )
                )

                if target_physical_face is None:
                    errors.append(
                        f"Nelze určit cílovou stranu "
                        f"pro S{sticker.target_face}/"
                        f"{sticker.target_position}."
                    )

                    continue

                target_row = (
                    sticker.target_position - 1
                ) // 3

                target_col = (
                    sticker.target_position - 1
                ) % 3

                target_coordinate = (
                    self._cubie_coordinate(
                        target_physical_face,
                        target_row,
                        target_col,
                    )
                )

                target_coordinates.append(
                    target_coordinate
                )

            if not target_coordinates:
                continue

            unique_targets = set(
                target_coordinates
            )

            if len(unique_targets) != 1:
                errors.append(
                    f"Fyzický {current_type} obsahuje "
                    "dílky, které k sobě nepatří:\n"
                    + ", ".join(
                        labels
                    )
                )

                continue

            target_coordinate = (
                target_coordinates[0]
            )

            target_type = self._cubie_type(
                target_coordinate
            )

            if target_type != current_type:
                errors.append(
                    f"Kámen {', '.join(labels)} "
                    f"je fyzicky '{current_type}', "
                    f"ale cílově vychází jako "
                    f"'{target_type}'."
                )

                continue

            old_current = (
                used_target_cubies.get(
                    target_coordinate
                )
            )

            if (
                old_current is not None
                and old_current
                != current_coordinate
            ):
                errors.append(
                    "Stejný cílový kámen je použit "
                    "na více fyzických místech: "
                    + ", ".join(
                        labels
                    )
                )

                continue

            used_target_cubies[
                target_coordinate
            ] = current_coordinate

    def _build_facelet_string(
        self,
        cube_state: CubeState,
        target_face_to_letter: dict[
            int,
            str,
        ],
        errors: list[str],
    ) -> str:
        facelets: list[str] = []

        for physical_face in (
            self.KOCIEMBA_FACE_ORDER
        ):
            for row in range(3):
                for col in range(3):
                    position = StickerPosition(
                        face=physical_face,
                        row=row,
                        col=col,
                    )

                    sticker = (
                        cube_state.sticker(
                            position
                        )
                    )

                    if sticker.target_face is None:
                        errors.append(
                            "Chybí cílová strana na "
                            f"{physical_face.value}, "
                            f"řádek {row + 1}, "
                            f"sloupec {col + 1}."
                        )
                        continue

                    letter = (
                        target_face_to_letter.get(
                            sticker.target_face
                        )
                    )

                    if letter is None:
                        errors.append(
                            "Nelze namapovat cílovou "
                            f"stranu {sticker.target_face}."
                        )
                        continue

                    facelets.append(
                        letter
                    )

        return "".join(
            facelets
        )

    def _check_center_rotations(
        self,
        cube_state: CubeState,
        warnings: list[str],
    ) -> None:
        rotated_centers: list[str] = []

        for face in FaceName:
            sticker = cube_state.sticker(
                StickerPosition(
                    face=face,
                    row=1,
                    col=1,
                )
            )

            if sticker.rotation != 0:
                rotated_centers.append(
                    f"{face.value}: "
                    f"{sticker.rotation_degrees}°"
                )

        if rotated_centers:
            warnings.append(
                "Některé středy obrázků jsou otočené: "
                + ", ".join(rotated_centers)
                + ". Standardní 3×3 solver nejprve "
                "vyřeší rozmístění kamenů; orientaci "
                "středů budeme řešit v samostatné fázi."
            )

    def _rotate_target_grid(
        self,
        row: int,
        col: int,
        rotation: int,
    ) -> tuple[int, int]:
        rotation %= 4

        for _ in range(rotation):
            row, col = (
                col,
                2 - row,
            )

        return (
            row,
            col,
        )

    def _cubie_coordinate(
        self,
        face: FaceName,
        row: int,
        col: int,
    ) -> Vector3:
        normal, right, down = (
            self._face_basis(
                face
            )
        )

        horizontal = col - 1
        vertical = row - 1

        return (
            normal[0]
            + right[0] * horizontal
            + down[0] * vertical,

            normal[1]
            + right[1] * horizontal
            + down[1] * vertical,

            normal[2]
            + right[2] * horizontal
            + down[2] * vertical,
        )

    def _cubie_type(
        self,
        coordinate: Vector3,
    ) -> str:
        fixed_axes = sum(
            1
            for value in coordinate
            if abs(value) == 1
        )

        if fixed_axes == 3:
            return "roh"

        if fixed_axes == 2:
            return "hrana"

        if fixed_axes == 1:
            return "střed"

        return "neznámý"

    def _face_basis(
        self,
        face: FaceName,
    ) -> tuple[
        Vector3,
        Vector3,
        Vector3,
    ]:
        if face == FaceName.FRONT:
            return (
                (0, 0, 1),
                (1, 0, 0),
                (0, -1, 0),
            )

        if face == FaceName.BACK:
            return (
                (0, 0, -1),
                (-1, 0, 0),
                (0, -1, 0),
            )

        if face == FaceName.RIGHT:
            return (
                (1, 0, 0),
                (0, 0, -1),
                (0, -1, 0),
            )

        if face == FaceName.LEFT:
            return (
                (-1, 0, 0),
                (0, 0, 1),
                (0, -1, 0),
            )

        if face == FaceName.UP:
            return (
                (0, 1, 0),
                (1, 0, 0),
                (0, 0, 1),
            )

        return (
            (0, -1, 0),
            (1, 0, 0),
            (0, 0, -1),
        )