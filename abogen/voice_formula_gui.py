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
    QSizePolicy
)
from PyQt5.QtCore import Qt
from constants import (
    VOICES_INTERNAL, 
    FLAGS
)

# Constants for voice names and flags
voice_mixer_width = 160
FEMALE = "👩‍🦰"
MALE = "👨"

class VoiceMixer(QWidget):
    def __init__(self, voice_name, language_icon, update_formula_callback, initial_status=False, initial_weight=0.0):
        super().__init__()

        self.voice_name = voice_name
        self.update_formula_callback = update_formula_callback

        # Set fixed width for this widget
        self.setFixedWidth(voice_mixer_width)
        # TODO Set CSS for rounded corners
        # self.setObjectName("VoiceMixer")
        # self.setStyleSheet(self.ROUNDED_CSS)

        # Main Layout
        layout = QVBoxLayout()

        # Checkbox at the top
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(initial_status)
        self.checkbox.stateChanged.connect(self.toggle_inputs)
        self.checkbox.stateChanged.connect(self.update_formula_callback)
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)

        voice_gender = self.get_voice_gender()
        name = voice_name[3:].capitalize()
        name_label = QLabel(f"{language_icon} {voice_gender} {name}")
        name_label.setStyleSheet("font-size: 16px;")
        name_layout = QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # Input and Slider
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(0, 1)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.setValue(initial_weight)
        self.spin_box.valueChanged.connect(self.update_formula_callback)

        self.slider = QSlider(Qt.Vertical)  # Set slider orientation to vertical
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_weight * 100))
        self.slider.setFixedHeight(180)
        self.slider.valueChanged.connect(
            lambda val: self.spin_box.setValue(val / 100)
        )
        self.spin_box.valueChanged.connect(
            lambda val: self.slider.setValue(int(val * 100))
        )

        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.spin_box)
        slider_layout.addWidget(QLabel("1", alignment=Qt.AlignCenter))
        slider_layout.addWidget(self.slider, alignment=Qt.AlignCenter)
        slider_layout.addWidget(QLabel("0", alignment=Qt.AlignCenter))

        layout.addLayout(slider_layout)
        self.setLayout(layout)

        # Disable inputs initially if the checkbox is unchecked
        self.toggle_inputs()
        
    def toggle_inputs(self):
        """Enable or disable inputs based on the checkbox state."""
        is_enabled = self.checkbox.isChecked()
        self.spin_box.setEnabled(is_enabled)
        self.slider.setEnabled(is_enabled)

    def get_voice_gender(self):
        if self.voice_name in VOICES_INTERNAL:
            gender = self.voice_name[1]
            return FEMALE if gender == "f" else MALE
        return ""

    def get_formula_component(self):
        if self.checkbox.isChecked():
            weight = self.spin_box.value()
            return f"{weight:.3f} * {self.voice_name.lower().replace(' ', '_')}"
        return ""


    def get_voice_weight(self):
        """Return the voice and its weight if selected."""
        if self.checkbox.isChecked():
            return self.voice_name, self.spin_box.value()
        return None

class VoiceFormulaDialog(QDialog):
    def __init__(self, parent=None, initial_state=None):
        super().__init__(parent)

        self.setWindowTitle("Voice Mixer")
        self.setFixedSize(1000, 500)
        self.voice_mixers = []

        # Main Layout
        main_layout = QVBoxLayout()

        # Scroll Area for Voice Panels
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(1000, 400)  # Keep scroll area height within 500
        self.voice_list_widget = QWidget()
        self.voice_list_layout = QHBoxLayout()  
        self.voice_list_widget.setLayout(self.voice_list_layout)
        self.voice_list_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_area.setWidget(self.voice_list_widget)
        main_layout.addWidget(self.scroll_area)

        # Formula Label
        self.formula_label = QLabel("Voice Combination Formula: ")
        self.formula_label.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.formula_label)


        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        # Connect buttons to appropriate slots
        ok_button.clicked.connect(self.accept)      
        cancel_button.clicked.connect(self.reject)  

        button_layout.addStretch()  # Push buttons to the right
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        
        # Initialize with fixed voices
        for voice in VOICES_INTERNAL:
            flag = FLAGS.get(voice[0], "")
            matching_voice = next((item for item in initial_state if item[0] == voice), None)
            initial_status = matching_voice is not None
            initial_weight = matching_voice[1] if matching_voice else 1.0
            self.add_voice(voice, flag, initial_status, initial_weight)
        
    def add_voice(self, voice_name, language_icon, initial_status=False, initial_weight=1.0):
        voice_mixer = VoiceMixer(voice_name, language_icon, self.update_formula, initial_status, initial_weight)
        self.voice_mixers.append(voice_mixer)
        self.voice_list_layout.addWidget(voice_mixer)
        self.update_formula()

    def update_scroll_area_width(self):
        # Calculate the width of the scrollable area based on the number of VoiceMixers
        width = len(self.voice_mixers) * voice_mixer_width
        self.voice_list_widget.setFixedWidth(width)

    def update_formula(self):
        formula_components = [
            mixer.get_formula_component() for mixer in self.voice_mixers
        ]
        formula = " + ".join(filter(None, formula_components))
        self.formula_label.setText(f"Voice Formula: {formula}")

    def get_selected_voices(self):
        """Return the list of selected voices and their weights."""
        selected_voices = [
            mixer.get_voice_weight() for mixer in self.voice_mixers
        ]
        return [voice for voice in selected_voices if voice]  # Filter out None
