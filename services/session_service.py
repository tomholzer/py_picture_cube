from __future__ import annotations

import json
from pathlib import Path

from models.cube_state import CubeState


class SessionService:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent

        self.data_dir = project_root / "data"
        self.session_file = self.data_dir / "current_session.json"

    def load(self) -> CubeState:
        if not self.session_file.exists():
            return CubeState()

        try:
            with self.session_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return CubeState.from_dict(data)

        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ):
            return CubeState()

    def save(self, cube_state: CubeState) -> None:
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.session_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                cube_state.to_dict(),
                file,
                indent=2,
                ensure_ascii=False,
            )