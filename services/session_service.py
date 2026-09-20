from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from models.cube_state import CubeState


@dataclass(frozen=True)
class SavedCube:
    cube_id: str
    name: str


class SessionService:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent

        self.data_dir = project_root / "data"
        self.cubes_dir = self.data_dir / "cubes"

        # Původní soubor z verze, která podporovala pouze jednu kostku.
        self.legacy_session_file = (
            self.data_dir / "current_session.json"
        )

        self.cubes_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._migrate_legacy_session()

    def list_cubes(self) -> list[SavedCube]:
        cubes: list[SavedCube] = []

        for file_path in self.cubes_dir.glob("*.json"):
            try:
                with file_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    data = json.load(file)

                cube_id = str(
                    data.get(
                        "cube_id",
                        file_path.stem,
                    )
                )

                name = str(
                    data.get(
                        "name",
                        cube_id,
                    )
                )

                cubes.append(
                    SavedCube(
                        cube_id=cube_id,
                        name=name,
                    )
                )

            except (
                OSError,
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ):
                continue

        cubes.sort(
            key=lambda cube: cube.name.lower()
        )

        return cubes

    def cube_exists(
        self,
        cube_id: str,
    ) -> bool:
        return self._cube_file(
            cube_id
        ).exists()

    def get_name(
        self,
        cube_id: str,
    ) -> str:
        data = self._load_raw(
            cube_id
        )

        if data is None:
            return cube_id

        return str(
            data.get(
                "name",
                cube_id,
            )
        )

    def create(
        self,
        name: str,
        cube_state: CubeState | None = None,
    ) -> str:
        clean_name = name.strip()

        if not clean_name:
            clean_name = "Nová kostka"

        cube_id = uuid.uuid4().hex[:12]

        if cube_state is None:
            cube_state = CubeState()

        self.save(
            cube_id=cube_id,
            cube_state=cube_state,
            name=clean_name,
        )

        return cube_id

    def load(
        self,
        cube_id: str,
    ) -> CubeState:
        data = self._load_raw(
            cube_id
        )

        if data is None:
            return CubeState()

        try:
            return CubeState.from_dict(
                data
            )

        except (
            ValueError,
            TypeError,
        ):
            return CubeState()

    def save(
        self,
        cube_id: str,
        cube_state: CubeState,
        name: str | None = None,
    ) -> None:
        self.cubes_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if name is None:
            old_data = self._load_raw(
                cube_id
            )

            if old_data is None:
                name = cube_id
            else:
                name = str(
                    old_data.get(
                        "name",
                        cube_id,
                    )
                )

        data = cube_state.to_dict()

        data["cube_id"] = cube_id
        data["name"] = name

        with self._cube_file(
            cube_id
        ).open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def rename(
        self,
        cube_id: str,
        new_name: str,
    ) -> None:
        clean_name = new_name.strip()

        if not clean_name:
            return

        cube_state = self.load(
            cube_id
        )

        self.save(
            cube_id=cube_id,
            cube_state=cube_state,
            name=clean_name,
        )

    def duplicate(
        self,
        cube_id: str,
        new_name: str,
    ) -> str:
        cube_state = self.load(
            cube_id
        )

        return self.create(
            name=new_name,
            cube_state=cube_state,
        )

    def delete(
        self,
        cube_id: str,
    ) -> None:
        file_path = self._cube_file(
            cube_id
        )

        if not file_path.exists():
            return

        try:
            file_path.unlink()
        except OSError:
            pass

    def ensure_at_least_one_cube(
        self,
    ) -> str:
        cubes = self.list_cubes()

        if cubes:
            return cubes[0].cube_id

        return self.create(
            "Kostka 1"
        )

    def _cube_file(
        self,
        cube_id: str,
    ) -> Path:
        safe_id = "".join(
            character
            for character in cube_id
            if (
                character.isalnum()
                or character in ("-", "_")
            )
        )

        return (
            self.cubes_dir
            / f"{safe_id}.json"
        )

    def _load_raw(
        self,
        cube_id: str,
    ) -> dict | None:
        file_path = self._cube_file(
            cube_id
        )

        if not file_path.exists():
            return None

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(
                data,
                dict,
            ):
                return None

            return data

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            return None

    def _migrate_legacy_session(
        self,
    ) -> None:
        if not self.legacy_session_file.exists():
            return

        if self.list_cubes():
            return

        try:
            with self.legacy_session_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            cube_state = CubeState.from_dict(
                data
            )

            self.create(
                name="Kostka 1",
                cube_state=cube_state,
            )

            backup_file = (
                self.data_dir
                / "current_session_backup.json"
            )

            if not backup_file.exists():
                shutil.copy2(
                    self.legacy_session_file,
                    backup_file,
                )

        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ):
            pass