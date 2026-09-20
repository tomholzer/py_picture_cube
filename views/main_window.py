from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QCloseEvent,
    QFont,
    QPainter,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.cube_state import StickerPosition
from services.session_service import SessionService
from services.settings_service import SettingsService
from services.solver_service import SolverService
from widgets.cube_3d_widget import Cube3DWidget


class RotationPreview(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._position: int | None = None
        self._rotation = 0

        self.setFixedSize(
            80,
            80,
        )

    def set_value(
        self,
        position: int | None,
        rotation: int,
    ) -> None:
        self._position = position
        self._rotation = rotation % 4

        self.update()

    def paintEvent(
        self,
        event,
    ) -> None:
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.fillRect(
            self.rect(),
            QColor(
                245,
                245,
                245,
            ),
        )

        painter.setPen(
            QColor(
                80,
                80,
                80,
            )
        )

        painter.drawRect(
            self.rect().adjusted(
                0,
                0,
                -1,
                -1,
            )
        )

        if self._position is None:
            painter.setPen(
                QColor(
                    150,
                    150,
                    150,
                )
            )

            font = QFont()
            font.setPointSize(18)
            font.setBold(True)

            painter.setFont(font)

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "-",
            )

            return

        painter.save()

        painter.translate(
            self.width() / 2,
            self.height() / 2,
        )

        painter.rotate(
            self._rotation * 90
        )

        font = QFont()
        font.setBold(True)
        font.setPointSize(28)

        painter.setFont(font)

        painter.setPen(
            QColor(
                20,
                20,
                20,
            )
        )

        text = str(
            self._position
        )

        metrics = painter.fontMetrics()
        rect = metrics.boundingRect(
            text
        )

        baseline_y = (
            rect.height() // 2
            - metrics.descent()
        )

        painter.drawText(
            -rect.width() // 2,
            baseline_y,
            text,
        )

        if self._position in (6, 9):
            underline_y = (
                baseline_y
                + metrics.descent()
                + 4
            )

            painter.drawLine(
                -rect.width() // 2 - 2,
                underline_y,
                rect.width() // 2 + 2,
                underline_y,
            )

        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "Picture Cube"
        )

        self.session_service = (
            SessionService()
        )

        self.settings_service = (
            SettingsService()
        )

        self.solver_service = SolverService()

        self.settings = (
            self.settings_service.load()
        )

        self.current_cube_id = (
            self._resolve_initial_cube()
        )

        self.cube_state = (
            self.session_service.load(
                self.current_cube_id
            )
        )

        self.cube_widget = (
            Cube3DWidget(
                self.cube_state
            )
        )

        self.face_buttons: dict[
            int,
            QPushButton,
        ] = {}

        self.position_buttons: dict[
            int,
            QPushButton,
        ] = {}

        self._build_ui()
        self._restore_settings()
        self._connect_signals()

        self._refresh_status()
        self._selection_changed(
            None
        )

    def _build_ui(
        self,
    ) -> None:
        central = QWidget()

        self.setCentralWidget(
            central
        )

        root_layout = QHBoxLayout(
            central
        )

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        root_layout.setSpacing(
            12
        )

        root_layout.addWidget(
            self.cube_widget,
            stretch=1,
        )

        side_panel = self._build_side_panel()

        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        side_scroll.setWidget(side_panel)

        side_scroll.setFixedWidth(350)

        root_layout.addWidget(
            side_scroll
        )

    def _build_side_panel(
        self,
    ) -> QWidget:
        panel = QFrame()

        panel.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        panel.setMinimumWidth(
            320
        )

        layout = QVBoxLayout(
            panel
        )

        cube_title = QLabel(
            "Uložená kostka"
        )

        cube_title_font = (
            cube_title.font()
        )

        cube_title_font.setBold(
            True
        )

        cube_title_font.setPointSize(
            12
        )

        cube_title.setFont(
            cube_title_font
        )

        layout.addWidget(
            cube_title
        )

        self.cube_combo = QComboBox()

        self.cube_combo.currentIndexChanged.connect(
            self._cube_combo_changed
        )

        layout.addWidget(
            self.cube_combo
        )

        cube_buttons = QGridLayout()

        self.new_cube_button = QPushButton(
            "Nová"
        )

        self.new_cube_button.clicked.connect(
            self._new_cube
        )

        cube_buttons.addWidget(
            self.new_cube_button,
            0,
            0,
        )

        self.rename_cube_button = QPushButton(
            "Přejmenovat"
        )

        self.rename_cube_button.clicked.connect(
            self._rename_cube
        )

        cube_buttons.addWidget(
            self.rename_cube_button,
            0,
            1,
        )

        self.duplicate_cube_button = QPushButton(
            "Duplikovat"
        )

        self.duplicate_cube_button.clicked.connect(
            self._duplicate_cube
        )

        cube_buttons.addWidget(
            self.duplicate_cube_button,
            1,
            0,
        )

        self.delete_cube_button = QPushButton(
            "Smazat"
        )

        self.delete_cube_button.clicked.connect(
            self._delete_cube
        )

        cube_buttons.addWidget(
            self.delete_cube_button,
            1,
            1,
        )

        layout.addLayout(
            cube_buttons
        )

        layout.addSpacing(
            18
        )

        self._refresh_cube_combo()


        title = QLabel(
            "Vybraný dílek"
        )

        title_font = (
            title.font()
        )

        title_font.setBold(
            True
        )

        title_font.setPointSize(
            12
        )

        title.setFont(
            title_font
        )

        layout.addWidget(
            title
        )

        self.selection_label = QLabel()

        self.selection_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.selection_label
        )

        self.value_label = QLabel()

        self.value_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.value_label
        )

        layout.addSpacing(
            16
        )

        face_title = QLabel(
            "1. Strana / barva"
        )

        face_title.setFont(
            title_font
        )

        layout.addWidget(
            face_title
        )

        face_layout = QHBoxLayout()

        face_layout.setSpacing(
            4
        )

        for target_face in range(
            1,
            7,
        ):
            button = QPushButton(
                str(
                    target_face
                )
            )

            button.setCheckable(
                True
            )

            button.setFixedSize(
                40,
                40,
            )

            button.clicked.connect(
                partial(
                    self._set_target_face,
                    target_face,
                )
            )

            self.face_buttons[
                target_face
            ] = button

            face_layout.addWidget(
                button
            )

        self.clear_face_button = (
            QPushButton(
                "X"
            )
        )

        self.clear_face_button.setToolTip(
            "Vymazat pouze stranu"
        )

        self.clear_face_button.setFixedSize(
            34,
            40,
        )

        self.clear_face_button.clicked.connect(
            self._clear_target_face
        )

        face_layout.addWidget(
            self.clear_face_button
        )

        layout.addLayout(
            face_layout
        )

        layout.addSpacing(
            14
        )

        position_title = QLabel(
            "2. Pozice obrázku"
        )

        position_title.setFont(
            title_font
        )

        layout.addWidget(
            position_title
        )

        position_info = QLabel(
            "Pozice je vždy určena při pohledu "
            "přímo na správně složenou stranu."
        )

        position_info.setWordWrap(
            True
        )

        layout.addWidget(
            position_info
        )

        position_area = QHBoxLayout()

        position_grid = QGridLayout()

        position_grid.setSpacing(
            5
        )

        for target_position in range(
            1,
            10,
        ):
            row = (
                target_position - 1
            ) // 3

            col = (
                target_position - 1
            ) % 3

            button = QPushButton(
                str(
                    target_position
                )
            )

            button.setCheckable(
                True
            )

            button.setFixedSize(
                52,
                46,
            )

            button.clicked.connect(
                partial(
                    self._set_target_position,
                    target_position,
                )
            )

            self.position_buttons[
                target_position
            ] = button

            position_grid.addWidget(
                button,
                row,
                col,
            )

        position_area.addLayout(
            position_grid
        )

        clear_position_layout = (
            QVBoxLayout()
        )

        self.clear_position_button = (
            QPushButton(
                "X"
            )
        )

        self.clear_position_button.setToolTip(
            "Vymazat pouze pozici a natočení"
        )

        self.clear_position_button.setFixedSize(
            40,
            46,
        )

        self.clear_position_button.clicked.connect(
            self._clear_target_position
        )

        clear_position_layout.addWidget(
            self.clear_position_button
        )

        clear_position_layout.addStretch(
            1
        )

        position_area.addLayout(
            clear_position_layout
        )

        layout.addLayout(
            position_area
        )

        layout.addSpacing(
            14
        )

        rotation_title = QLabel(
            "Natočení obrázku"
        )

        rotation_title.setFont(
            title_font
        )

        layout.addWidget(
            rotation_title
        )

        rotation_layout = QHBoxLayout()

        self.rotate_left_button = (
            QPushButton(
                "↺"
            )
        )

        self.rotate_left_button.setFixedSize(
            52,
            52,
        )

        self.rotate_left_button.clicked.connect(
            self._rotate_left
        )

        rotation_layout.addWidget(
            self.rotate_left_button
        )

        rotation_layout.addStretch(
            1
        )

        self.rotation_preview = (
            RotationPreview()
        )

        rotation_layout.addWidget(
            self.rotation_preview
        )

        rotation_layout.addStretch(
            1
        )

        self.rotate_right_button = (
            QPushButton(
                "↻"
            )
        )

        self.rotate_right_button.setFixedSize(
            52,
            52,
        )

        self.rotate_right_button.clicked.connect(
            self._rotate_right
        )

        rotation_layout.addWidget(
            self.rotate_right_button
        )

        layout.addLayout(
            rotation_layout
        )

        self.rotation_label = QLabel(
            "Natočení: 0°"
        )

        self.rotation_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.rotation_label
        )

        layout.addSpacing(
            18
        )

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
            "1–6: změnit stranu / barvu\n"
            "Q: otočit obrázek doleva\n"
            "E: otočit obrázek doprava\n"
            "Delete: vymazat celý dílek\n"
            "Esc: zrušit výběr\n\n"
            "Num 5: přední pohled\n"
            "Num 0: zadní pohled\n"
            "Num 4: levý pohled\n"
            "Num 6: pravý pohled\n"
            "Num 8: horní pohled\n"
            "Num 2: spodní pohled\n"
            "Home: izometrický pohled"
        )

        controls.setWordWrap(
            True
        )

        layout.addWidget(
            controls
        )

        layout.addSpacing(
            18
        )

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

        self.progress_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.progress_label
        )

        self.validation_label = QLabel()

        self.validation_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.validation_label
        )

        save_info = QLabel(
            "Změny se ukládají automaticky."
        )

        save_info.setWordWrap(
            True
        )

        layout.addWidget(
            save_info
        )

        solver_title = QLabel(
            "Solver"
        )

        solver_title.setFont(
            title_font
        )

        layout.addWidget(
            solver_title
        )

        self.validate_cube_button = QPushButton(
            "Zkontrolovat kostku"
        )

        self.validate_cube_button.clicked.connect(
            self._validate_cube
        )

        layout.addWidget(
            self.validate_cube_button
        )

        self.solve_cube_button = QPushButton(
            "Spočítat řešení"
        )

        self.solve_cube_button.clicked.connect(
            self._solve_cube
        )

        layout.addWidget(
            self.solve_cube_button
        )

        layout.addSpacing(
            12
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

        layout.addStretch(
            1
        )

        return panel


    def _resolve_initial_cube(
        self,
    ) -> str:
        last_cube = self.settings.get(
            "last_cube"
        )

        if (
            isinstance(
                last_cube,
                str,
            )
            and self.session_service.cube_exists(
                last_cube
            )
        ):
            return last_cube

        return (
            self.session_service
            .ensure_at_least_one_cube()
        )

    def _refresh_cube_combo(
        self,
    ) -> None:
        if not hasattr(
            self,
            "cube_combo",
        ):
            return

        cubes = (
            self.session_service.list_cubes()
        )

        self.cube_combo.blockSignals(
            True
        )

        self.cube_combo.clear()

        current_index = -1

        for index, cube in enumerate(
            cubes
        ):
            self.cube_combo.addItem(
                cube.name,
                cube.cube_id,
            )

            if (
                cube.cube_id
                == self.current_cube_id
            ):
                current_index = index

        if current_index >= 0:
            self.cube_combo.setCurrentIndex(
                current_index
            )

        self.cube_combo.blockSignals(
            False
        )

    def _cube_combo_changed(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        cube_id = (
            self.cube_combo.itemData(
                index
            )
        )

        if not cube_id:
            return

        cube_id = str(
            cube_id
        )

        if (
            cube_id
            == self.current_cube_id
        ):
            return

        self._save_current_cube()

        self.current_cube_id = cube_id

        self.cube_state = (
            self.session_service.load(
                cube_id
            )
        )

        self.cube_widget.cube_state = (
            self.cube_state
        )

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self.cube_widget.update()

        self._selection_changed(
            None
        )

        self._refresh_status()

        self._save_settings()

    def _new_cube(
        self,
    ) -> None:
        name, accepted = (
            QInputDialog.getText(
                self,
                "Nová kostka",
                "Název kostky:",
            )
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        self._save_current_cube()

        cube_id = (
            self.session_service.create(
                name
            )
        )

        self.current_cube_id = cube_id

        self.cube_state = (
            self.session_service.load(
                cube_id
            )
        )

        self.cube_widget.cube_state = (
            self.cube_state
        )

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self._refresh_cube_combo()
        self.cube_widget.update()
        self._selection_changed(None)
        self._refresh_status()
        self._save_settings()

    def _rename_cube(
        self,
    ) -> None:
        old_name = (
            self.session_service.get_name(
                self.current_cube_id
            )
        )

        new_name, accepted = (
            QInputDialog.getText(
                self,
                "Přejmenovat kostku",
                "Nový název:",
                text=old_name,
            )
        )

        if not accepted:
            return

        new_name = new_name.strip()

        if not new_name:
            return

        self.session_service.rename(
            self.current_cube_id,
            new_name,
        )

        self._refresh_cube_combo()

    def _duplicate_cube(
        self,
    ) -> None:
        old_name = (
            self.session_service.get_name(
                self.current_cube_id
            )
        )

        new_name, accepted = (
            QInputDialog.getText(
                self,
                "Duplikovat kostku",
                "Název kopie:",
                text=f"{old_name} - kopie",
            )
        )

        if not accepted:
            return

        new_name = new_name.strip()

        if not new_name:
            return

        self._save_current_cube()

        cube_id = (
            self.session_service.duplicate(
                self.current_cube_id,
                new_name,
            )
        )

        self.current_cube_id = cube_id

        self.cube_state = (
            self.session_service.load(
                cube_id
            )
        )

        self.cube_widget.cube_state = (
            self.cube_state
        )

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self._refresh_cube_combo()
        self.cube_widget.update()
        self._selection_changed(None)
        self._refresh_status()
        self._save_settings()

    def _delete_cube(
        self,
    ) -> None:
        cubes = (
            self.session_service.list_cubes()
        )

        if len(cubes) <= 1:
            QMessageBox.information(
                self,
                "Smazat kostku",
                "Poslední kostku nelze smazat.",
            )

            return

        name = (
            self.session_service.get_name(
                self.current_cube_id
            )
        )

        answer = QMessageBox.question(
            self,
            "Smazat kostku",
            (
                f'Opravdu smazat kostku '
                f'"{name}"?'
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        old_cube_id = (
            self.current_cube_id
        )

        self.session_service.delete(
            old_cube_id
        )

        cubes = (
            self.session_service.list_cubes()
        )

        self.current_cube_id = (
            cubes[0].cube_id
        )

        self.cube_state = (
            self.session_service.load(
                self.current_cube_id
            )
        )

        self.cube_widget.cube_state = (
            self.cube_state
        )

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self._refresh_cube_combo()
        self.cube_widget.update()
        self._selection_changed(None)
        self._refresh_status()
        self._save_settings()

    def _save_current_cube(
        self,
    ) -> None:
        self.session_service.save(
            self.current_cube_id,
            self.cube_state,
        )

    def _connect_signals(
        self,
    ) -> None:
        self.cube_widget.state_changed.connect(
            self._cube_state_changed
        )

        self.cube_widget.selection_changed.connect(
            self._selection_changed
        )

        self.cube_widget.camera_changed.connect(
            self._camera_changed
        )

    def _restore_settings(
        self,
    ) -> None:
        window = self.settings[
            "window"
        ]

        self.resize(
            window["width"],
            window["height"],
        )

        self.cube_widget.set_camera_state(
            self.settings[
                "camera"
            ]
        )

    def _selection_changed(
        self,
        position: StickerPosition | None,
    ) -> None:
        if position is None:
            self.selection_label.setText(
                "Není vybráno žádné políčko."
            )

            self.value_label.setText(
                ""
            )

            self.rotation_label.setText(
                "Natočení: -"
            )

            self.rotation_preview.set_value(
                None,
                0,
            )

            self._refresh_editor_controls()

            return

        sticker = self.cube_state.sticker(
            position
        )

        self.selection_label.setText(
            f"Strana kostky: {position.face.value}\n"
            f"Řádek: {position.row + 1}\n"
            f"Sloupec: {position.col + 1}"
        )

        if sticker.target_face is None:
            face_text = "-"
        else:
            face_text = str(
                sticker.target_face
            )

        if sticker.target_position is None:
            position_text = "-"
        else:
            position_text = str(
                sticker.target_position
            )

        self.value_label.setText(
            f"Cílová strana: {face_text}\n"
            f"Pozice obrázku: {position_text}"
        )

        if sticker.target_position is None:
            self.rotation_label.setText(
                "Natočení: -"
            )
        else:
            self.rotation_label.setText(
                "Natočení: "
                f"{sticker.rotation_degrees}°"
            )

        self.rotation_preview.set_value(
            sticker.target_position,
            sticker.rotation,
        )

        self._refresh_editor_controls()

    def _refresh_editor_controls(
        self,
    ) -> None:
        selected = self.cube_widget.selected

        has_selection = (
            selected is not None
        )

        if selected is None:
            sticker = None
        else:
            sticker = self.cube_state.sticker(
                selected
            )

        # -------------------------------------------------
        # Strany 1–6
        # -------------------------------------------------

        for (
            target_face,
            button,
        ) in self.face_buttons.items():
            button.setEnabled(
                has_selection
            )

            button.setChecked(
                sticker is not None
                and sticker.target_face
                == target_face
            )

        # -------------------------------------------------
        # Pozice 1–9
        # -------------------------------------------------

        for (
            target_position,
            button,
        ) in self.position_buttons.items():
            button.setEnabled(
                has_selection
            )

            button.setChecked(
                sticker is not None
                and sticker.target_position
                == target_position
            )

            # Výchozí vzhled.
            button.setStyleSheet(
                ""
            )

            if (
                sticker is None
                or sticker.target_face is None
            ):
                continue

            owner = (
                self.cube_state.find_target_owner(
                    target_face=sticker.target_face,
                    target_position=target_position,
                    exclude=selected,
                )
            )

            if owner is not None:
                # Pozice už je použitá někde jinde.
                # Tlačítko ale zůstává klikatelné.
                button.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #777777;
                        color: #d0d0d0;
                    }

                    QPushButton:hover {
                        background-color: #888888;
                        color: white;
                    }
                    """
                )

        # -------------------------------------------------
        # Mazání jednotlivých hodnot
        # -------------------------------------------------

        self.clear_face_button.setEnabled(
            sticker is not None
            and sticker.target_face
            is not None
        )

        self.clear_position_button.setEnabled(
            sticker is not None
            and sticker.target_position
            is not None
        )

        # -------------------------------------------------
        # Rotace
        # -------------------------------------------------

        can_rotate = (
            sticker is not None
            and sticker.can_rotate
        )

        self.rotate_left_button.setEnabled(
            can_rotate
        )

        self.rotate_right_button.setEnabled(
            can_rotate
        )

    def _confirm_target_assignment(
        self,
        target_face: int,
        target_position: int,
    ) -> bool:
        selected = self.cube_widget.selected

        if selected is None:
            return False

        owner = self.cube_state.find_target_owner(
            target_face=target_face,
            target_position=target_position,
            exclude=selected,
        )

        if owner is None:
            return True

        answer = QMessageBox.question(
            self,
            "Pozice už je použitá",
            (
                f"Dílek strany {target_face}, "
                f"pozice {target_position} "
                "už je použitý na jiném místě.\n\n"
                "Chceš ho přesunout sem?\n\n"
                "Původní přiřazení bude vymazáno."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return False

        self.cube_state.clear_sticker(
            owner
        )

        return True


    def _set_target_face(
        self,
        target_face: int,
    ) -> None:
        selected = self.cube_widget.selected

        if selected is None:
            return

        sticker = self.cube_state.sticker(
            selected
        )

        if sticker.target_position is not None:
            allowed = self._confirm_target_assignment(
                target_face=target_face,
                target_position=sticker.target_position,
            )

            if not allowed:
                self._refresh_editor_controls()
                return

        self.cube_state.set_target_face(
            selected,
            target_face,
        )

        self._state_edited()

    def _set_target_position(
        self,
        target_position: int,
    ) -> None:
        selected = self.cube_widget.selected

        if selected is None:
            return

        sticker = self.cube_state.sticker(
            selected
        )

        if sticker.target_face is not None:
            allowed = self._confirm_target_assignment(
                target_face=sticker.target_face,
                target_position=target_position,
            )

            if not allowed:
                self._refresh_editor_controls()
                return

        self.cube_state.set_target_position(
            selected,
            target_position,
        )

        self._state_edited()

    def _clear_target_face(
        self,
    ) -> None:
        selected = (
            self.cube_widget.selected
        )

        if selected is None:
            return

        self.cube_state.clear_target_face(
            selected
        )

        self._state_edited()

    def _clear_target_position(
        self,
    ) -> None:
        selected = (
            self.cube_widget.selected
        )

        if selected is None:
            return

        self.cube_state.clear_target_position(
            selected
        )

        self._state_edited()

    def _rotate_left(
        self,
    ) -> None:
        selected = (
            self.cube_widget.selected
        )

        if selected is None:
            return

        sticker = self.cube_state.sticker(
            selected
        )

        if not sticker.can_rotate:
            return

        self.cube_state.rotate_left(
            selected
        )

        self._state_edited()

    def _rotate_right(
        self,
    ) -> None:
        selected = (
            self.cube_widget.selected
        )

        if selected is None:
            return

        sticker = self.cube_state.sticker(
            selected
        )

        if not sticker.can_rotate:
            return

        self.cube_state.rotate_right(
            selected
        )

        self._state_edited()

    def _state_edited(
        self,
    ) -> None:
        self._save_current_cube()

        self.cube_widget.update()

        self._refresh_status()

    def _refresh_status(
        self,
    ) -> None:
        defined = (
            self.cube_state.defined_count()
        )

        partial = (
            self.cube_state
            .partially_defined_count()
        )

        self.progress_label.setText(
            f"Kompletní dílky: {defined} / 54\n"
            f"Rozpracované dílky: {partial}"
        )

        messages = (
            self.cube_state
            .validation_messages()
        )

        if self.cube_state.is_complete():
            self.validation_label.setText(
                "Kostka je kompletně zadaná."
            )

        elif messages:
            self.validation_label.setText(
                "\n".join(
                    messages[:5]
                )
            )

        else:
            self.validation_label.setText(
                ""
            )

        self._selection_changed(
            self.cube_widget.selected
        )

    def _cube_state_changed(
        self,
    ) -> None:
        self._save_current_cube()

        self._refresh_status()

    def _camera_changed(
        self,
    ) -> None:
        self._save_settings()

    def _save_settings(
        self,
    ) -> None:
        settings = {
            "version": 2,
            "last_cube": self.current_cube_id,
            "window": {
                "width": self.width(),
                "height": self.height(),
            },
            "camera": (
                self.cube_widget
                .get_camera_state()
            ),
        }

        self.settings_service.save(
            settings
        )

        self.settings = settings


    def _validate_cube(
        self,
    ) -> None:
        self._save_current_cube()

        result = self.solver_service.validate(
            self.cube_state
        )

        if not result.is_valid:
            text = "\n\n".join(
                result.errors
            )

            QMessageBox.warning(
                self,
                "Kostka není platná",
                text,
            )

            return

        mapping_lines = []

        for target_face in sorted(
            result.target_face_to_physical
        ):
            physical_face = (
                result.target_face_to_physical[
                    target_face
                ]
            )

            letter = (
                result.target_face_to_letter[
                    target_face
                ]
            )

            mapping_lines.append(
                f"Strana {target_face} "
                f"= {letter} "
                f"({physical_face.value})"
            )

        text = (
            "Kostka je fyzicky platná.\n\n"
            + "\n".join(
                mapping_lines
            )
        )

        if result.warnings:
            text += (
                "\n\nUpozornění:\n"
                + "\n".join(
                    result.warnings
                )
            )

        QMessageBox.information(
            self,
            "Kontrola kostky",
            text,
        )

    def _solve_cube(
        self,
    ) -> None:
        self._save_current_cube()

        QMessageBox.information(
            self,
            "Výpočet řešení",
            (
                "Spouštím solver.\n\n"
                "Při prvním spuštění může příprava "
                "solveru trvat desítky sekund."
            ),
        )

        result = self.solver_service.solve(
            self.cube_state
        )

        if not result.success:
            text = "\n\n".join(
                result.errors
            )

            QMessageBox.warning(
                self,
                "Řešení nelze vytvořit",
                text,
            )

            return

        if not result.moves:
            text = (
                "Rozmístění kamenů je už vyřešené."
            )

        else:
            text = (
                f"Počet tahů: {len(result.moves)}\n\n"
                + " ".join(
                    result.moves
                )
            )

        if result.warnings:
            text += (
                "\n\nUpozornění:\n"
                + "\n".join(
                    result.warnings
                )
            )

        QMessageBox.information(
            self,
            "Řešení kostky",
            text,
        )

    def _clear_cube(
        self,
    ) -> None:
        self.cube_state.clear_all()

        self.cube_widget.selected = None
        self.cube_widget.hovered = None

        self._save_current_cube()

        self.cube_widget.update()

        self._refresh_status()
        self._selection_changed(
            None
        )

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        self._save_current_cube()

        self._save_settings()

        super().closeEvent(
            event
        )