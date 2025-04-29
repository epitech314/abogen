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
    QMessageBox
)
from PyQt5.QtCore import (
    Qt,
    QTimer
)
from constants import (
    VOICES_INTERNAL, 
    FLAGS
)

# Constants for voice names and flags
VOICE_MIXER_WIDTH = 160
SLIDER_WIDTH = 32  # Added slider width
MIN_WINDOW_WIDTH = 600  # Minimum window width
MIN_WINDOW_HEIGHT = 400  # Minimum window height
INITIAL_WINDOW_WIDTH = 1000  # Initial window width
INITIAL_WINDOW_HEIGHT = 500  # Initial window height
FEMALE = "👩‍🦰"
MALE = "👨"

class VoiceMixer(QWidget):
    def __init__(self, voice_name, language_icon, initial_status=False, initial_weight=0.0):
        super().__init__()

        self.voice_name = voice_name

        # Set fixed width for this widget
        self.setFixedWidth(VOICE_MIXER_WIDTH)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # TODO Set CSS for rounded corners
        # self.setObjectName("VoiceMixer")
        # self.setStyleSheet(self.ROUNDED_CSS)

        # Main Layout
        layout = QVBoxLayout()

        # Checkbox at the top
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(initial_status)
        self.checkbox.stateChanged.connect(self.toggle_inputs)
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)

        voice_gender = self.get_voice_gender()
        name = voice_name[3:].capitalize()
        name_label = QLabel(f"{language_icon} {voice_gender} {name}")
        name_layout = QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.setAlignment(name_label, Qt.AlignCenter)
        layout.addLayout(name_layout)

        # Input and Slider
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(0, 1)
        self.spin_box.setSingleStep(0.01)
        self.spin_box.setDecimals(2)
        self.spin_box.setValue(initial_weight)

        self.slider = QSlider(Qt.Vertical)  # Set slider orientation to vertical
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_weight * 100))
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Fixed width, expanding height
        self.slider.setFixedWidth(SLIDER_WIDTH)  # Set fixed width for slider
        self.slider.valueChanged.connect(
            lambda val: self.spin_box.setValue(val / 100)
        )
        self.spin_box.valueChanged.connect(
            lambda val: self.slider.setValue(int(val * 100))
        )
 
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.spin_box)
        slider_layout.addWidget(QLabel("1", alignment=Qt.AlignCenter))
        slider_layout.addWidget(self.slider, alignment=Qt.AlignCenter, stretch=1)  # Use stretch to expand slider
        slider_layout.addWidget(QLabel("0", alignment=Qt.AlignCenter))
        slider_layout.setStretch(2, 2)  # Make slider take all available vertical space

        layout.addLayout(slider_layout, stretch=1)  # Make slider layout expand
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
        self.setMinimumWidth(MIN_WINDOW_WIDTH)
        self.setMinimumHeight(MIN_WINDOW_HEIGHT)
        self.resize(INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT)
        self.voice_mixers = []

        # Main Layout
        main_layout = QVBoxLayout()

        # Header Label
        self.header_label = QLabel("Select Voices For the Mix and Adjust Weights")
        main_layout.addWidget(self.header_label)

        # Weighted Sums Label
        self.weighted_sums_label = QLabel()
        self.weighted_sums_label.setAlignment(Qt.AlignCenter)  # Center align the label
        self.weighted_sums_label.setWordWrap(True)  # Enable word wrap
        main_layout.addWidget(self.weighted_sums_label)

        # Scroll Area for Voice Panels
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.viewport().installEventFilter(self)  # Install event filter for wheel events

        self.voice_list_widget = QWidget()
        self.voice_list_layout = QHBoxLayout()  
        self.voice_list_widget.setLayout(self.voice_list_layout)
        self.voice_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.voice_list_widget)
        main_layout.addWidget(self.scroll_area)

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
        
        self.add_voices(initial_state)
        self.update_weighted_sums()

    def add_voices(self, initial_state):
        """Add voice mixers to the dialog based on the initial state and scroll to first enabled one."""
        first_enabled_voice = None 

        for voice in VOICES_INTERNAL:
            flag = FLAGS.get(voice[0], "")
            matching_voice = next((item for item in initial_state if item[0] == voice), None)
            initial_status = matching_voice is not None
            initial_weight = matching_voice[1] if matching_voice else 0.0
            voice_mixer = self.add_voice(voice, flag, initial_status, initial_weight)
            # remember the first enabled voice
            if initial_status and first_enabled_voice is None:
                first_enabled_voice = voice_mixer
        
        if first_enabled_voice:
            self.scroll_to_voice(first_enabled_voice)
        
    def add_voice(self, voice_name, language_icon, initial_status=False, initial_weight=1.0):
        voice_mixer = VoiceMixer(voice_name, language_icon, initial_status, initial_weight)
        self.voice_mixers.append(voice_mixer)
        self.voice_list_layout.addWidget(voice_mixer)
        # Connect signals to update weighted sums
        voice_mixer.checkbox.stateChanged.connect(self.update_weighted_sums)
        voice_mixer.spin_box.valueChanged.connect(self.update_weighted_sums)
        return voice_mixer

    def scroll_to_voice(self, voice_mixer):
        """Scroll the QScrollArea to ensure the given VoiceMixer is visible."""        
        QTimer.singleShot(0, lambda: self.scroll_area.ensureWidgetVisible(voice_mixer))

    def get_selected_voices(self):
        """Return the list of selected voices and their weights."""
        selected_voices = [
            mixer.get_voice_weight() for mixer in self.voice_mixers
        ]
        return [voice for voice in selected_voices if voice]  # Filter out None

    def update_weighted_sums(self):
        selected = [(m.voice_name, m.spin_box.value()) for m in self.voice_mixers if m.checkbox.isChecked()]
        total = sum(w for _, w in selected)
        if total > 0:
            lines = [f"{name}: {weight/total*100:.1f}%" for name, weight in selected]
            joined = " | ".join(lines)
        else:
            joined = ""
        self.weighted_sums_label.setText(joined)  # Remove the prefix

    def eventFilter(self, source, event):
        """Event filter to handle mouse wheel events for horizontal scrolling."""
        if (source is self.scroll_area.viewport() and event.type() == event.Wheel):

            # Check if the event is over a slider
            # Check if mouse is over an enabled slider
            if any(mixer.slider.underMouse() and mixer.slider.isEnabled() for mixer in self.voice_mixers):
                return False
            # Convert vertical wheel movement to horizontal scrolling
            horiz_bar = self.scroll_area.horizontalScrollBar()
            if event.angleDelta().y() > 0:
                horiz_bar.setValue(horiz_bar.value() - 120)  # Scroll left
            else:
                horiz_bar.setValue(horiz_bar.value() + 120)  # Scroll right
            return True
        return super().eventFilter(source, event)

    def resizeEvent(self, event):
        """Handle resize events to adjust slider heights"""
        super().resizeEvent(event)
        
        # Calculate available height for sliders
        header_height = self.header_label.height() + self.weighted_sums_label.height()
        button_area_height = 50  # Approximate height for button area
        available_height = self.height() - header_height - button_area_height - 220  # Add more margin for safety
        
        # Set slider height (don't make them too small)
        slider_height = max(available_height, 100)
        
        # Update all sliders
        for mixer in self.voice_mixers:
            mixer.slider.setFixedHeight(slider_height)  # Use fixed height instead of minimum height

    def accept(self):
        selected_voices = self.get_selected_voices()
        total_weight = sum(weight for _, weight in selected_voices)
        if total_weight == 0:
            QMessageBox.warning(
                self,
                "Invalid Weights",
                "The total weight of selected voices cannot be zero. Please select at least one voice or adjust the weights."
            )
            return
        super().accept()
