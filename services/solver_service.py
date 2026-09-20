from __future__ import annotations

from dataclasses import dataclass

from models.cube_state import CubeState
from services.cube_mapper import (
    CubeMapper,
    CubeMappingResult,
)


@dataclass(frozen=True)
class SolveResult:
    success: bool
    moves: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    facelet_string: str | None
    mapping: CubeMappingResult


class SolverService:
    def __init__(self) -> None:
        self.mapper = CubeMapper()

    def validate(
        self,
        cube_state: CubeState,
    ) -> CubeMappingResult:
        mapping = self.mapper.map(
            cube_state
        )

        if not mapping.is_valid:
            return mapping

        if mapping.facelet_string is None:
            return CubeMappingResult(
                is_valid=False,
                errors=(
                    "Mapper nevytvořil stav kostky.",
                ),
                warnings=mapping.warnings,
                facelet_string=None,
                target_face_to_physical=(
                    mapping.target_face_to_physical
                ),
                target_face_to_letter=(
                    mapping.target_face_to_letter
                ),
            )

        try:
            from rubik_solver import Cube
        except ImportError:
            return CubeMappingResult(
                is_valid=False,
                errors=(
                    "Chybí knihovna rubik-solver-py. "
                    "Spusť pip install -r requirements.txt.",
                ),
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                target_face_to_physical=(
                    mapping.target_face_to_physical
                ),
                target_face_to_letter=(
                    mapping.target_face_to_letter
                ),
            )

        try:
            cube = Cube.from_string(
                mapping.facelet_string
            )

            verification = cube.verify()

        except Exception as error:
            return CubeMappingResult(
                is_valid=False,
                errors=(
                    "Solver nedokázal načíst stav kostky: "
                    f"{error}",
                ),
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                target_face_to_physical=(
                    mapping.target_face_to_physical
                ),
                target_face_to_letter=(
                    mapping.target_face_to_letter
                ),
            )

        if verification is not True:
            return CubeMappingResult(
                is_valid=False,
                errors=(
                    "Zadaný stav není fyzicky dosažitelný: "
                    f"{verification}",
                ),
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                target_face_to_physical=(
                    mapping.target_face_to_physical
                ),
                target_face_to_letter=(
                    mapping.target_face_to_letter
                ),
            )

        return mapping

    def solve(
        self,
        cube_state: CubeState,
    ) -> SolveResult:
        mapping = self.validate(
            cube_state
        )

        if (
            not mapping.is_valid
            or mapping.facelet_string is None
        ):
            return SolveResult(
                success=False,
                moves=(),
                errors=mapping.errors,
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                mapping=mapping,
            )

        try:
            from rubik_solver import (
                Cube,
                init_solver,
                solve,
            )

            cube = Cube.from_string(
                mapping.facelet_string
            )

            if cube.is_solved():
                moves: tuple[str, ...] = ()

            else:
                init_solver()

                solution = solve(
                    cube
                )

                if solution is None:
                    return SolveResult(
                        success=False,
                        moves=(),
                        errors=(
                            "Solver nenašel řešení "
                            "v povolené hloubce.",
                        ),
                        warnings=mapping.warnings,
                        facelet_string=(
                            mapping.facelet_string
                        ),
                        mapping=mapping,
                    )

                moves = tuple(
                    move
                    for move in solution.split()
                    if move
                )

            return SolveResult(
                success=True,
                moves=moves,
                errors=(),
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                mapping=mapping,
            )

        except Exception as error:
            return SolveResult(
                success=False,
                moves=(),
                errors=(
                    "Při výpočtu řešení nastala chyba: "
                    f"{error}",
                ),
                warnings=mapping.warnings,
                facelet_string=(
                    mapping.facelet_string
                ),
                mapping=mapping,
            )