from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QHBoxLayout,
    QDoubleSpinBox,
    QSlider,
    QScrollArea,
    QWidget,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QFrame,
    QLayout,
    QStyle,
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QSize
from constants import VOICES_INTERNAL, FLAGS

# Constants
VOICE_MIXER_WIDTH = 160
SLIDER_WIDTH = 32
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 400
INITIAL_WINDOW_WIDTH = 1000
INITIAL_WINDOW_HEIGHT = 500
FEMALE, MALE = "👩‍🦰", "👨"


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def sizeHint(self):
        return self.minimumSize()

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only):
        x, y = rect.x(), rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = self.parentWidget().style() if self.parentWidget() else QStyle()
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
            )
            space_x = spacing if spacing >= 0 else layout_spacing_x
            space_y = spacing if spacing >= 0 else layout_spacing_y

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class VoiceMixer(QWidget):
    def __init__(
        self, voice_name, language_icon, initial_status=False, initial_weight=0.0
    ):
        super().__init__()
        self.voice_name = voice_name
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # TODO Set CSS for rounded corners
        # self.setObjectName("VoiceMixer")
        # self.setStyleSheet(self.ROUNDED_CSS)

        layout = QVBoxLayout()

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(initial_status)
        self.checkbox.stateChanged.connect(self.toggle_inputs)
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)

        # Voice name label
        voice_gender = (
            FEMALE
            if self.voice_name in VOICES_INTERNAL and self.voice_name[1] == "f"
            else MALE
        )
        name = voice_name[3:].capitalize()
        name_layout = QHBoxLayout()
        name_layout.addWidget(
            QLabel(f"{language_icon} {voice_gender} {name}"), alignment=Qt.AlignCenter
        )
        layout.addLayout(name_layout)

        # Spinbox and slider
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(0, 1)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.setValue(initial_weight)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_weight * 100))
        self.slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.slider.setFixedWidth(SLIDER_WIDTH)

        # Connect controls
        self.slider.valueChanged.connect(lambda val: self.spin_box.setValue(val / 100))
        self.spin_box.valueChanged.connect(
            lambda val: self.slider.setValue(int(val * 100))
        )

        # Layout for slider and labels
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.spin_box)
        slider_layout.addWidget(QLabel("1", alignment=Qt.AlignCenter))

        slider_center_layout = QHBoxLayout()
        slider_center_layout.addWidget(self.slider, alignment=Qt.AlignHCenter)
        slider_center_layout.setContentsMargins(0, 0, 0, 0)

        slider_center_widget = QWidget()
        slider_center_widget.setLayout(slider_center_layout)

        slider_layout.addWidget(slider_center_widget, stretch=1)
        slider_layout.addWidget(QLabel("0", alignment=Qt.AlignCenter))
        slider_layout.setStretch(2, 1)

        layout.addLayout(slider_layout, stretch=1)
        self.setLayout(layout)
        self.toggle_inputs()

    def toggle_inputs(self):
        is_enabled = self.checkbox.isChecked()
        self.spin_box.setEnabled(is_enabled)
        self.slider.setEnabled(is_enabled)

    def get_voice_weight(self):
        if self.checkbox.isChecked():
            return self.voice_name, self.spin_box.value()
        return None


class HoverLabel(QLabel):
    def __init__(self, text, voice_name, parent=None):
        super().__init__(text, parent)
        self.voice_name = voice_name
        self.setMouseTracking(True)
        self.setStyleSheet(
            "background-color: #e0e0e0; border-radius: 4px; padding: 3px 6px 3px 6px; margin: 2px;"
        )

        # Create delete button
        self.delete_button = QPushButton("×", self)
        self.delete_button.setFixedSize(16, 16)
        self.delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: red;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                border: none;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """
        )
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.delete_button.move(self.width() - 16, 0)

    def enterEvent(self, event):
        self.delete_button.show()

    def leaveEvent(self, event):
        self.delete_button.hide()


class VoiceFormulaDialog(QDialog):
    def __init__(self, parent=None, initial_state=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Mixer")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT)
        self.voice_mixers = []
        self.last_enabled_voice = None

        # Main Layout
        main_layout = QVBoxLayout()

        # Header
        self.header_label = QLabel(
            "Adjust voice weights to create your preferred voice mix."
        )
        self.header_label.setStyleSheet("font-size: 13px;")
        self.header_label.setWordWrap(True)
        main_layout.addWidget(self.header_label)

        # Error message
        self.error_label = QLabel(
            "No voices selected or all weights are 0. Please select at least one voice and set its weight above 0."
        )
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        # Voice weights display
        self.weighted_sums_container = QWidget()
        self.weighted_sums_layout = FlowLayout(self.weighted_sums_container)
        self.weighted_sums_layout.setSpacing(5)
        self.weighted_sums_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.weighted_sums_container)

        # Separator
        separator = QFrame()
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Voice list scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.viewport().installEventFilter(self)

        self.voice_list_widget = QWidget()
        self.voice_list_layout = QHBoxLayout()
        self.voice_list_widget.setLayout(self.voice_list_layout)
        self.voice_list_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.scroll_area.setWidget(self.voice_list_widget)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Buttons
        button_layout = QHBoxLayout()
        clear_all_button = QPushButton("Clear all")
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        # Set OK button as default
        ok_button.setDefault(True)
        ok_button.setFocus()

        # Connect buttons
        clear_all_button.clicked.connect(self.clear_all_voices)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(clear_all_button)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Setup voices and display
        self.add_voices(initial_state or [])
        self.update_weighted_sums()

    def add_voices(self, initial_state):
        first_enabled_voice = None
        for voice in VOICES_INTERNAL:
            flag = FLAGS.get(voice[0], "")
            matching_voice = next(
                (item for item in initial_state if item[0] == voice), None
            )
            initial_status = matching_voice is not None
            initial_weight = matching_voice[1] if matching_voice else 1.0
            voice_mixer = self.add_voice(voice, flag, initial_status, initial_weight)
            if initial_status and first_enabled_voice is None:
                first_enabled_voice = voice_mixer

        if first_enabled_voice:
            QTimer.singleShot(
                0, lambda: self.scroll_area.ensureWidgetVisible(first_enabled_voice)
            )

    def add_voice(
        self, voice_name, language_icon, initial_status=False, initial_weight=1.0
    ):
        voice_mixer = VoiceMixer(
            voice_name, language_icon, initial_status, initial_weight
        )
        self.voice_mixers.append(voice_mixer)
        self.voice_list_layout.addWidget(voice_mixer)
        voice_mixer.checkbox.stateChanged.connect(
            lambda state, vm=voice_mixer: self.handle_voice_checkbox(vm, state)
        )
        voice_mixer.spin_box.valueChanged.connect(self.update_weighted_sums)
        return voice_mixer

    def handle_voice_checkbox(self, voice_mixer, state):
        if state == Qt.Checked:
            self.last_enabled_voice = voice_mixer.voice_name
        self.update_weighted_sums()

    def get_selected_voices(self):
        return [
            v
            for v in (m.get_voice_weight() for m in self.voice_mixers)
            if v and v[1] > 0
        ]

    def update_weighted_sums(self):
        # Clear previous labels
        while self.weighted_sums_layout.count():
            item = self.weighted_sums_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Get selected voices
        selected = [
            (m.voice_name, m.spin_box.value())
            for m in self.voice_mixers
            if m.checkbox.isChecked() and m.spin_box.value() > 0
        ]

        total = sum(w for _, w in selected)

        if total > 0:
            self.error_label.hide()
            self.weighted_sums_container.show()

            # Reorder so last enabled voice is at the end
            if self.last_enabled_voice and any(
                name == self.last_enabled_voice for name, _ in selected
            ):
                others = [(n, w) for n, w in selected if n != self.last_enabled_voice]
                last = [(n, w) for n, w in selected if n == self.last_enabled_voice]
                selected = others + last

            # Add voice labels
            for name, weight in selected:
                percentage = weight / total * 100
                voice_label = HoverLabel(f"{name}: {percentage:.1f}%", name)
                voice_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                voice_label.delete_button.clicked.connect(
                    lambda _, vn=name: self.disable_voice_by_name(vn)
                )
                self.weighted_sums_layout.addWidget(voice_label)
        else:
            self.error_label.show()
            self.weighted_sums_container.hide()

    def disable_voice_by_name(self, voice_name):
        for mixer in self.voice_mixers:
            if mixer.voice_name == voice_name:
                mixer.checkbox.setChecked(False)
                break

    def clear_all_voices(self):
        for mixer in self.voice_mixers:
            mixer.checkbox.setChecked(False)

    def eventFilter(self, source, event):
        if source is self.scroll_area.viewport() and event.type() == event.Wheel:
            # Skip if over an enabled slider
            if any(
                mixer.slider.underMouse() and mixer.slider.isEnabled()
                for mixer in self.voice_mixers
            ):
                return False

            # Horizontal scrolling
            horiz_bar = self.scroll_area.horizontalScrollBar()
            delta = -120 if event.angleDelta().y() > 0 else 120
            horiz_bar.setValue(horiz_bar.value() + delta)
            return True
        return super().eventFilter(source, event)

    def accept(self):
        selected_voices = self.get_selected_voices()
        total_weight = sum(weight for _, weight in selected_voices)
        if total_weight == 0:
            QMessageBox.warning(
                self,
                "Invalid Weights",
                "The total weight of selected voices cannot be zero. Please select at least one voice or adjust the weights.",
            )
            return
        super().accept()
