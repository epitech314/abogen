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
    QPushButton
)
from PyQt5.QtCore import Qt

class VoiceMixer(QWidget):
    def __init__(self, voice_name, language_icon, update_formula_callback):
        super().__init__()

        self.voice_name = voice_name
        self.update_formula_callback = update_formula_callback

        # Main Layout
        layout = QVBoxLayout()

        # Checkbox and Voice Name
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.update_formula_callback)

        name_label = QLabel(f"{voice_name} {language_icon}")
        name_label.setStyleSheet("font-size: 16px;")
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.checkbox)
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # Input and Slider
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(0, 1)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.valueChanged.connect(self.update_formula_callback)

        self.slider = QSlider(Qt.Vertical)  # Set slider orientation to vertical
        self.slider.setRange(0, 100)
        self.slider.setValue(50)  # Default to 0.5
        self.slider.valueChanged.connect(
            lambda val: self.spin_box.setValue(val / 100)
        )
        self.spin_box.valueChanged.connect(
            lambda val: self.slider.setValue(int(val * 100))
        )

        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.spin_box)
        slider_layout.addWidget(QLabel("1", alignment=Qt.AlignCenter))
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(QLabel("0", alignment=Qt.AlignCenter))

        layout.addLayout(slider_layout)
        self.setLayout(layout)

    def get_formula_component(self):
        if self.checkbox.isChecked():
            weight = self.spin_box.value()
            return f"{weight:.3f} * {self.voice_name.lower().replace(' ', '_')}"
        return ""


class VoiceFormulaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Voice Mixer")
        self.voice_mixers = []

        # Main Layout
        main_layout = QVBoxLayout()

        # Scroll Area for Voice Panels
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.voice_list_widget = QWidget()
        self.voice_list_layout = QHBoxLayout()
        self.voice_list_widget.setLayout(self.voice_list_layout)
        self.scroll_area.setWidget(self.voice_list_widget)
        main_layout.addWidget(self.scroll_area)

        # Formula Label
        self.formula_label = QLabel("Voice Formula: ")
        self.formula_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.formula_label)


        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        # Connect buttons to appropriate slots
        ok_button.clicked.connect(self.accept)      # Close dialog and return QDialog.Accepted
        cancel_button.clicked.connect(self.reject)  # Close dialog and return QDialog.Rejected

        button_layout.addStretch()  # Push buttons to the right
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        
        # Initialize with fixed voices
        self.add_fixed_voices()


    def add_fixed_voices(self):
        voices = ['af_bella', 'af_sarah', 'am_eric']
        language_icon = '🇺🇸'
        for voice in voices:
            self.add_voice(voice, language_icon)

    def add_voice(self, voice_name, language_icon):
        voice_mixer = VoiceMixer(voice_name, language_icon, self.update_formula)
        self.voice_mixers.append(voice_mixer)
        self.voice_list_layout.addWidget(voice_mixer)
        self.update_formula()

    def update_formula(self):
        formula_components = [
            mixer.get_formula_component() for mixer in self.voice_mixers
        ]
        formula = " + ".join(filter(None, formula_components))
        self.formula_label.setText(f"Voice Formula: {formula}")
