from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPolygonF,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from models.cube_face import FaceName
from models.cube_state import CubeState, StickerPosition


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __mul__(self, value: float) -> Vec3:
        return Vec3(
            self.x * value,
            self.y * value,
            self.z * value,
        )


@dataclass
class ProjectedSticker:
    position: StickerPosition
    polygon: QPolygonF
    center: QPointF
    depth: float


class Cube3DWidget(QWidget):
    state_changed = Signal()
    selection_changed = Signal(object)
    camera_changed = Signal()

    def __init__(
        self,
        cube_state: CubeState,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.cube_state = cube_state

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(620, 620)

        self.yaw = math.radians(-35.0)
        self.pitch = math.radians(25.0)
        self.zoom = 1.0

        self.selected: StickerPosition | None = None
        self.hovered: StickerPosition | None = None

        self._projected_stickers: list[ProjectedSticker] = []

        self._rotating_camera = False
        self._last_mouse_position: QPoint | None = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.fillRect(
            self.rect(),
            QColor(32, 34, 37),
        )

        projected = self._build_projected_stickers()
        projected.sort(key=lambda item: item.depth)

        self._projected_stickers = projected

        for item in projected:
            self._draw_sticker(
                painter,
                item,
            )

    def _build_projected_stickers(
        self,
    ) -> list[ProjectedSticker]:
        result: list[ProjectedSticker] = []

        for face in FaceName:
            normal, right, down = self._face_basis(face)

            rotated_normal = self._rotate(normal)

            if rotated_normal.z <= 0.01:
                continue

            for row in range(3):
                for col in range(3):
                    corners = self._sticker_corners(
                        normal=normal,
                        right=right,
                        down=down,
                        row=row,
                        col=col,
                    )

                    rotated = [
                        self._rotate(point)
                        for point in corners
                    ]

                    polygon = QPolygonF(
                        [
                            self._project(point)
                            for point in rotated
                        ]
                    )

                    center_3d = Vec3(
                        sum(
                            point.x
                            for point in rotated
                        )
                        / 4.0,
                        sum(
                            point.y
                            for point in rotated
                        )
                        / 4.0,
                        sum(
                            point.z
                            for point in rotated
                        )
                        / 4.0,
                    )

                    result.append(
                        ProjectedSticker(
                            position=StickerPosition(
                                face=face,
                                row=row,
                                col=col,
                            ),
                            polygon=polygon,
                            center=self._project(
                                center_3d
                            ),
                            depth=center_3d.z,
                        )
                    )

        return result

    def _face_basis(
        self,
        face: FaceName,
    ) -> tuple[Vec3, Vec3, Vec3]:
        if face == FaceName.FRONT:
            return (
                Vec3(0, 0, 1),
                Vec3(1, 0, 0),
                Vec3(0, -1, 0),
            )

        if face == FaceName.BACK:
            return (
                Vec3(0, 0, -1),
                Vec3(-1, 0, 0),
                Vec3(0, -1, 0),
            )

        if face == FaceName.RIGHT:
            return (
                Vec3(1, 0, 0),
                Vec3(0, 0, -1),
                Vec3(0, -1, 0),
            )

        if face == FaceName.LEFT:
            return (
                Vec3(-1, 0, 0),
                Vec3(0, 0, 1),
                Vec3(0, -1, 0),
            )

        if face == FaceName.UP:
            return (
                Vec3(0, 1, 0),
                Vec3(1, 0, 0),
                Vec3(0, 0, 1),
            )

        return (
            Vec3(0, -1, 0),
            Vec3(1, 0, 0),
            Vec3(0, 0, -1),
        )

    def _sticker_corners(
        self,
        normal: Vec3,
        right: Vec3,
        down: Vec3,
        row: int,
        col: int,
    ) -> list[Vec3]:
        cell_size = 2.0 / 3.0

        x1 = -1.0 + col * cell_size
        x2 = x1 + cell_size

        y1 = -1.0 + row * cell_size
        y2 = y1 + cell_size

        inset = 0.018

        x1 += inset
        x2 -= inset
        y1 += inset
        y2 -= inset

        center = normal * 1.0

        return [
            center + right * x1 + down * y1,
            center + right * x2 + down * y1,
            center + right * x2 + down * y2,
            center + right * x1 + down * y2,
        ]

    def _rotate(self, point: Vec3) -> Vec3:
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)

        x1 = (
            point.x * cos_yaw
            + point.z * sin_yaw
        )

        z1 = (
            -point.x * sin_yaw
            + point.z * cos_yaw
        )

        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)

        y2 = (
            point.y * cos_pitch
            - z1 * sin_pitch
        )

        z2 = (
            point.y * sin_pitch
            + z1 * cos_pitch
        )

        return Vec3(
            x=x1,
            y=y2,
            z=z2,
        )

    def _project(self, point: Vec3) -> QPointF:
        size = min(
            self.width(),
            self.height(),
        )

        base_scale = size * 0.29 * self.zoom
        camera_distance = 6.0

        perspective = (
            camera_distance
            / (camera_distance - point.z)
        )

        x = (
            self.width() / 2
            + point.x
            * base_scale
            * perspective
        )

        y = (
            self.height() / 2
            - point.y
            * base_scale
            * perspective
        )

        return QPointF(
            x,
            y,
        )

    def _draw_sticker(
        self,
        painter: QPainter,
        item: ProjectedSticker,
    ) -> None:
        position = item.position
        sticker = self.cube_state.sticker(position)

        is_selected = position == self.selected
        is_hovered = position == self.hovered

        if (
            self.selected is not None
            and not is_selected
        ):
            fill_color = QColor(
                88,
                88,
                88,
            )

            text_color = QColor(
                135,
                135,
                135,
            )
        else:
            fill_color = QColor(
                235,
                235,
                235,
            )

            text_color = QColor(
                20,
                20,
                20,
            )

        painter.setBrush(fill_color)

        if is_selected:
            pen = QPen(
                QColor(
                    255,
                    190,
                    50,
                )
            )

            pen.setWidthF(4.0)

        elif is_hovered:
            pen = QPen(
                QColor(
                    100,
                    190,
                    255,
                )
            )

            pen.setWidthF(3.0)

        else:
            pen = QPen(
                QColor(
                    45,
                    45,
                    45,
                )
            )

            pen.setWidthF(1.5)

        painter.setPen(pen)
        painter.drawPolygon(item.polygon)

        if sticker.number is None:
            return

        self._draw_number(
            painter=painter,
            center=item.center,
            number=sticker.number,
            rotation=sticker.rotation,
            color=text_color,
        )

    def _draw_number(
        self,
        painter: QPainter,
        center: QPointF,
        number: int,
        rotation: int,
        color: QColor,
    ) -> None:
        painter.save()

        painter.translate(center)
        painter.rotate(rotation * 90)

        font = QFont()
        font.setBold(True)

        font.setPixelSize(
            max(
                18,
                int(
                    min(
                        self.width(),
                        self.height(),
                    )
                    * 0.045
                ),
            )
        )

        painter.setFont(font)
        painter.setPen(color)

        text = str(number)

        metrics = painter.fontMetrics()
        rect = metrics.boundingRect(text)

        painter.drawText(
            QPointF(
                -rect.width() / 2,
                rect.height() / 2
                - metrics.descent(),
            ),
            text,
        )

        painter.restore()

    def mouseMoveEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        if self._rotating_camera:
            if self._last_mouse_position is None:
                self._last_mouse_position = (
                    event.position().toPoint()
                )
                return

            current = event.position().toPoint()

            dx = (
                current.x()
                - self._last_mouse_position.x()
            )

            dy = (
                current.y()
                - self._last_mouse_position.y()
            )

            self.yaw += dx * 0.01
            self.pitch += dy * 0.01

            max_pitch = math.radians(89)

            self.pitch = max(
                -max_pitch,
                min(
                    max_pitch,
                    self.pitch,
                ),
            )

            self._last_mouse_position = current
            self.hovered = None

            self.update()
            return

        new_hover = self._find_sticker_at(
            event.position()
        )

        if new_hover != self.hovered:
            self.hovered = new_hover
            self.update()

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        self.setFocus()

        if (
            event.button()
            == Qt.MouseButton.RightButton
        ):
            self._rotating_camera = True

            self._last_mouse_position = (
                event.position().toPoint()
            )

            self.hovered = None

            self.update()
            return

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            clicked = self._find_sticker_at(
                event.position()
            )

            if clicked is None:
                return

            self.selected = clicked

            self.selection_changed.emit(
                self.selected
            )

            self.update()

    def mouseReleaseEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        if (
            event.button()
            == Qt.MouseButton.RightButton
        ):
            self._rotating_camera = False
            self._last_mouse_position = None

            self.hovered = self._find_sticker_at(
                event.position()
            )

            self.camera_changed.emit()

            self.update()

    def leaveEvent(self, event) -> None:
        if not self._rotating_camera:
            self.hovered = None
            self.update()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom *= 1.1

        elif delta < 0:
            self.zoom /= 1.1

        self.zoom = max(
            0.55,
            min(
                2.0,
                self.zoom,
            ),
        )

        self.camera_changed.emit()

        self.update()

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ) -> None:
        key = event.key()

        if (
            event.modifiers()
            & Qt.KeyboardModifier.KeypadModifier
        ):
            if self._handle_numpad_view(key):
                event.accept()
                return

        if key == Qt.Key.Key_Escape:
            if self.selected is not None:
                self.selected = None

                self.selection_changed.emit(
                    None
                )

                self.update()

            event.accept()
            return

        if key == Qt.Key.Key_Home:
            self.set_isometric_view()

            event.accept()
            return

        if self.selected is None:
            super().keyPressEvent(event)
            return

        number_keys = {
            Qt.Key.Key_1: 1,
            Qt.Key.Key_2: 2,
            Qt.Key.Key_3: 3,
            Qt.Key.Key_4: 4,
            Qt.Key.Key_5: 5,
            Qt.Key.Key_6: 6,
        }

        if key in number_keys:
            self.cube_state.set_number(
                self.selected,
                number_keys[key],
            )

            self.state_changed.emit()

            self.update()

            event.accept()
            return

        if key == Qt.Key.Key_Q:
            self.cube_state.rotate_left(
                self.selected
            )

            self.state_changed.emit()

            self.update()

            event.accept()
            return

        if key == Qt.Key.Key_E:
            self.cube_state.rotate_right(
                self.selected
            )

            self.state_changed.emit()

            self.update()

            event.accept()
            return

        if key in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        ):
            self.cube_state.clear_sticker(
                self.selected
            )

            self.state_changed.emit()

            self.update()

            event.accept()
            return

        super().keyPressEvent(event)

    def _handle_numpad_view(
        self,
        key: int,
    ) -> bool:
        if key == Qt.Key.Key_5:
            self.set_front_view()
            return True

        if key == Qt.Key.Key_0:
            self.set_back_view()
            return True

        if key == Qt.Key.Key_4:
            self.set_left_view()
            return True

        if key == Qt.Key.Key_6:
            self.set_right_view()
            return True

        if key == Qt.Key.Key_8:
            self.set_top_view()
            return True

        if key == Qt.Key.Key_2:
            self.set_bottom_view()
            return True

        return False

    def _find_sticker_at(
        self,
        point: QPointF,
    ) -> StickerPosition | None:
        matches = [
            item
            for item in self._projected_stickers
            if item.polygon.containsPoint(
                point,
                Qt.FillRule.WindingFill,
            )
        ]

        if not matches:
            return None

        closest = max(
            matches,
            key=lambda item: item.depth,
        )

        return closest.position

    def get_camera_state(
        self,
    ) -> dict[str, float]:
        return {
            "yaw": math.degrees(self.yaw),
            "pitch": math.degrees(self.pitch),
            "zoom": self.zoom,
        }

    def set_camera_state(
        self,
        camera: dict[str, Any],
    ) -> None:
        yaw = float(
            camera.get(
                "yaw",
                -35.0,
            )
        )

        pitch = float(
            camera.get(
                "pitch",
                25.0,
            )
        )

        zoom = float(
            camera.get(
                "zoom",
                1.0,
            )
        )

        self.yaw = math.radians(yaw)
        self.pitch = math.radians(pitch)

        self.zoom = max(
            0.55,
            min(
                2.0,
                zoom,
            ),
        )

        self.update()

    def set_isometric_view(self) -> None:
        self.yaw = math.radians(-35.0)
        self.pitch = math.radians(25.0)

        self.camera_changed.emit()

        self.update()

    def set_front_view(self) -> None:
        self.yaw = 0.0
        self.pitch = 0.0

        self.camera_changed.emit()

        self.update()

    def set_back_view(self) -> None:
        self.yaw = math.radians(180.0)
        self.pitch = 0.0

        self.camera_changed.emit()

        self.update()

    def set_left_view(self) -> None:
        self.yaw = math.radians(90.0)
        self.pitch = 0.0

        self.camera_changed.emit()

        self.update()

    def set_right_view(self) -> None:
        self.yaw = math.radians(-90.0)
        self.pitch = 0.0

        self.camera_changed.emit()

        self.update()

    def set_top_view(self) -> None:
        self.yaw = 0.0
        self.pitch = math.radians(90.0)

        self.camera_changed.emit()

        self.update()

    def set_bottom_view(self) -> None:
        self.yaw = 0.0
        self.pitch = math.radians(-90.0)

        self.camera_changed.emit()

        self.update()