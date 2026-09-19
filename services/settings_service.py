from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsService:
    DEFAULT_SETTINGS: dict[str, Any] = {
        "version": 1,
        "window": {
            "width": 1050,
            "height": 760,
        },
        "camera": {
            "yaw": -35.0,
            "pitch": 25.0,
            "zoom": 1.0,
        },
    }

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent

        self.data_dir = project_root / "data"
        self.settings_file = self.data_dir / "settings.json"

    def load(self) -> dict[str, Any]:
        if not self.settings_file.exists():
            return self._default_copy()

        try:
            with self.settings_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                loaded = json.load(file)

            return self._merge_with_defaults(loaded)

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            return self._default_copy()

    def save(self, settings: dict[str, Any]) -> None:
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.settings_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                settings,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def _default_copy(self) -> dict[str, Any]:
        return {
            "version": 1,
            "window": {
                "width": 1050,
                "height": 760,
            },
            "camera": {
                "yaw": -35.0,
                "pitch": 25.0,
                "zoom": 1.0,
            },
        }

    def _merge_with_defaults(
        self,
        loaded: Any,
    ) -> dict[str, Any]:
        result = self._default_copy()

        if not isinstance(loaded, dict):
            return result

        window = loaded.get("window")

        if isinstance(window, dict):
            result["window"]["width"] = int(
                window.get(
                    "width",
                    result["window"]["width"],
                )
            )

            result["window"]["height"] = int(
                window.get(
                    "height",
                    result["window"]["height"],
                )
            )

        camera = loaded.get("camera")

        if isinstance(camera, dict):
            result["camera"]["yaw"] = float(
                camera.get(
                    "yaw",
                    result["camera"]["yaw"],
                )
            )

            result["camera"]["pitch"] = float(
                camera.get(
                    "pitch",
                    result["camera"]["pitch"],
                )
            )

            result["camera"]["zoom"] = float(
                camera.get(
                    "zoom",
                    result["camera"]["zoom"],
                )
            )

        return result