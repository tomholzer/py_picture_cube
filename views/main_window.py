from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.cube_state import StickerPosition
from services.session_service import SessionService
from services.settings_service import SettingsService
from widgets.cube_3d_widget import Cube3DWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Picture Cube")

        self.session_service = SessionService()
        self.settings_service = SettingsService()

        self.settings = self.settings_service.load()
        self.cube_state = self.session_service.load()

        self.cube_widget = Cube3DWidget(
            self.cube_state
        )

        self._build_ui()
        self._restore_settings()
        self._connect_signals()

        self._refresh_status()
        self._selection_changed(None)

    def _build_ui(self) -> None:
        central = QWidget()

        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        root_layout.setSpacing(12)

        root_layout.addWidget(
            self.cube_widget,
            stretch=1,
        )

        side_panel = self._build_side_panel()

        root_layout.addWidget(
            side_panel
        )

    def _build_side_panel(self) -> QWidget:
        panel = QFrame()

        panel.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        panel.setFixedWidth(300)

        layout = QVBoxLayout(panel)

        title = QLabel(
            "Aktuální políčko"
        )

        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(12)

        title.setFont(title_font)

        layout.addWidget(title)

        self.selection_label = QLabel()
        self.selection_label.setWordWrap(True)

        layout.addWidget(
            self.selection_label
        )

        self.value_label = QLabel()
        self.value_label.setWordWrap(True)

        layout.addWidget(
            self.value_label
        )

        layout.addSpacing(18)

        controls_title = QLabel(
            "Ovládání"
        )

        controls_title.setFont(
            title_font
        )

        layout.addWidget(
            controls_title
        )

        controls = QLabel(
            "LMB: vybrat políčko\n"
            "RMB + pohyb: otočit pohled\n"
            "Kolečko: zoom\n\n"
            "1–6: nastavit číslo\n"
            "Q: otočit číslo doleva\n"
            "E: otočit číslo doprava\n"
            "Delete: vymazat políčko\n"
            "Esc: zrušit výběr\n\n"
            "Num 5: přední pohled\n"
            "Num 0: zadní pohled\n"
            "Num 4: levý pohled\n"
            "Num 6: pravý pohled\n"
            "Num 8: horní pohled\n"
            "Num 2: spodní pohled\n"
            "Home: izometrický pohled"
        )

        controls.setWordWrap(True)

        layout.addWidget(
            controls
        )

        layout.addSpacing(18)

        status_title = QLabel(
            "Stav kostky"
        )

        status_title.setFont(
            title_font
        )

        layout.addWidget(
            status_title
        )

        self.progress_label = QLabel()

        layout.addWidget(
            self.progress_label
        )

        save_info = QLabel(
            "Změny se ukládají automaticky."
        )

        save_info.setWordWrap(True)

        layout.addWidget(
            save_info
        )

        self.clear_button = QPushButton(
            "Vymazat celou kostku"
        )

        self.clear_button.clicked.connect(
            self._clear_cube
        )

        layout.addWidget(
            self.clear_button
        )

        layout.addStretch(1)

        return panel

    def _connect_signals(self) -> None:
        self.cube_widget.state_changed.connect(
            self._cube_state_changed
        )

        self.cube_widget.selection_changed.connect(
            self._selection_changed
        )

        self.cube_widget.camera_changed.connect(
            self._camera_changed
        )

    def _restore_settings(self) -> None:
        window = self.settings["window"]

        self.resize(
            window["width"],
            window["height"],
        )

        self.cube_widget.set_camera_state(
            self.settings["camera"]
        )

    def _selection_changed(
        self,
        position: StickerPosition | None,
    ) -> None:
        if position is None:
            self.selection_label.setText(
                "Není vybráno žádné políčko."
            )

            self.value_label.setText("")

            return

        sticker = self.cube_state.sticker(
            position
        )

        self.selection_label.setText(
            f"Strana: {position.face.value}\n"
            f"Řádek: {position.row + 1}\n"
            f"Sloupec: {position.col + 1}"
        )

        if sticker.number is None:
            number_text = "nenastaveno"
        else:
            number_text = str(
                sticker.number
            )

        self.value_label.setText(
            f"Číslo: {number_text}\n"
            f"Otočení: "
            f"{sticker.rotation_degrees}°"
        )

    def _refresh_status(self) -> None:
        assigned = (
            self.cube_state.assigned_count()
        )

        self.progress_label.setText(
            f"Vyplněno: {assigned} / 54"
        )

        self._selection_changed(
            self.cube_widget.selected
        )

    def _cube_state_changed(self) -> None:
        self.session_service.save(
            self.cube_state
        )

        self._refresh_status()

    def _camera_changed(self) -> None:
        self._save_settings()

    def _save_settings(self) -> None:
        settings = {
            "version": 1,
            "window": {
                "width": self.width(),
                "height": self.height(),
            },
            "camera": (
                self.cube_widget.get_camera_state()
            ),
        }

        self.settings_service.save(
            settings
        )

        self.settings = settings

    def _clear_cube(self) -> None:
        self.cube_state.clear_all()

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self.session_service.save(
            self.cube_state
        )

        self.cube_widget.update()

        self._refresh_status()
        self._selection_changed(None)

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        self.session_service.save(
            self.cube_state
        )

        self._save_settings()

        super().closeEvent(event)