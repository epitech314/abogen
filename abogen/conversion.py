import os
import re
import tempfile
import time
import chardet
import charset_normalizer
from platformdirs import user_desktop_dir
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QDialog, QLabel, QDialogButtonBox
import soundfile as sf
from utils import clean_text, create_process
from constants import PROGRAM_NAME, LANGUAGE_DESCRIPTIONS, SAMPLE_VOICE_TEXTS
from voice_formulas import get_new_voice
import static_ffmpeg
import threading  # for efficient waiting
import subprocess


def get_sample_voice_text(lang_code):
    return SAMPLE_VOICE_TEXTS.get(lang_code, SAMPLE_VOICE_TEXTS["a"])


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read()
    detected_encoding = None
    for detectors in (charset_normalizer, chardet):
        try:
            result = detectors.detect(raw_data)["encoding"]
        except Exception:
            continue
        if result is not None:
            detected_encoding = result
            break
    encoding = detected_encoding if detected_encoding else "utf-8"
    return encoding.lower()


class ChapterOptionsDialog(QDialog):
    def __init__(self, chapter_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chapter Options")
        self.setMinimumWidth(350)
        # Prevent closing with the X button and remove the help button
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowCloseButtonHint
            & ~Qt.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)

        # Add informational label
        layout.addWidget(QLabel(f"Detected {chapter_count} chapters in the text file."))
        layout.addWidget(QLabel("How would you like to process these chapters?"))

        # Add checkboxes
        self.save_separately_checkbox = QCheckBox("Save each chapter separately")
        self.merge_at_end_checkbox = QCheckBox("Create a merged version at the end")

        # Set default states
        self.save_separately_checkbox.setChecked(True)
        self.merge_at_end_checkbox.setChecked(True)

        # Connect checkbox state change signal
        self.save_separately_checkbox.stateChanged.connect(
            self.update_merge_checkbox_state
        )

        layout.addWidget(self.save_separately_checkbox)
        layout.addWidget(self.merge_at_end_checkbox)

        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        # Initialize merge checkbox state
        self.update_merge_checkbox_state()

    def update_merge_checkbox_state(self):
        # Enable merge checkbox only if save separately is checked
        self.merge_at_end_checkbox.setEnabled(self.save_separately_checkbox.isChecked())
        # Don't uncheck it, just leave it in its current state

    def get_options(self):
        save_separately = self.save_separately_checkbox.isChecked()
        # Consider merge_at_end as false if the checkbox is disabled, regardless of its checked state
        merge_at_end = (
            self.merge_at_end_checkbox.isChecked()
            and self.merge_at_end_checkbox.isEnabled()
        )
        return {
            "save_chapters_separately": save_separately,
            "merge_chapters_at_end": merge_at_end,
        }

    # Prevent closing by overriding the closeEvent
    def closeEvent(self, event):
        # Ignore all close events
        event.ignore()

    # Prevent escape key from closing the dialog
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)


class ConversionThread(QThread):
    progress_updated = pyqtSignal(int, str)  # Add str for ETR
    conversion_finished = pyqtSignal(object, object)  # Pass output path as second arg
    log_updated = pyqtSignal(object)  # Updated signal for log updates
    chapters_detected = pyqtSignal(int)  # Signal for chapter detection

    def __init__(
        self,
        file_name,
        lang_code,
        speed,
        voice,
        save_option,
        output_folder,
        subtitle_mode,
        output_format,
        np_module,
        kpipeline_class,
        start_time,
        total_char_count,
        use_gpu=True,
    ):  # Add use_gpu parameter
        super().__init__()
        self._chapter_options_event = threading.Event()
        self.np = np_module
        self.KPipeline = kpipeline_class
        self.file_name = file_name
        self.lang_code = lang_code
        self.speed = speed
        self.voice = voice
        self.save_option = save_option
        self.output_folder = output_folder
        self.subtitle_mode = subtitle_mode
        self.cancel_requested = False
        self.output_format = output_format
        self.start_time = start_time  # Store start_time
        self.total_char_count = total_char_count  # Use passed total character count
        self.processed_char_count = 0  # Initialize processed character count
        self.display_path = None  # Add variable for display path
        self.is_direct_text = (
            False  # Flag to indicate if input is from textbox rather than file
        )
        self.chapter_options_set = False
        self.waiting_for_user_input = False
        self.use_gpu = use_gpu  # Store the GPU setting
        self.max_subtitle_words = 50  # Default value, will be overridden from GUI

    def run(self):
        print(
            f"\nVoice: {self.voice}\nLanguage: {self.lang_code}\nSpeed: {self.speed}\nGPU: {self.use_gpu}\nFile: {self.file_name}\nSubtitle mode: {self.subtitle_mode}\nOutput format: {self.output_format}\nSave option: {self.save_option}\n"
        )
        try:
            # Show configuration
            self.log_updated.emit("Configuration:")
            # Use display_path for logs if available, otherwise use the actual file name
            display_file = self.display_path if self.display_path else self.file_name
            self.log_updated.emit(f"- Input File: {display_file}")

            # Use file size string passed from GUI
            if hasattr(self, "file_size_str"):
                self.log_updated.emit(f"- File size: {self.file_size_str}")

            self.log_updated.emit(f"- Total characters: {self.total_char_count:,}")

            self.log_updated.emit(
                f"- Language: {self.lang_code} ({LANGUAGE_DESCRIPTIONS.get(self.lang_code, 'Unknown')})"
            )
            self.log_updated.emit(f"- Voice: {self.voice}")
            self.log_updated.emit(f"- Speed: {self.speed}")
            self.log_updated.emit(f"- Subtitle mode: {self.subtitle_mode}")
            self.log_updated.emit(f"- Output format: {self.output_format}")
            self.log_updated.emit(f"- Save option: {self.save_option}")
            if self.replace_single_newlines:
                self.log_updated.emit(f"- Replace single newlines: Yes")

            # Display save_chapters_separately flag if it's set
            if hasattr(self, "save_chapters_separately"):
                self.log_updated.emit(
                    (
                        f"- Save chapters separately: {'Yes' if self.save_chapters_separately else 'No'}"
                    )
                )
                # Display merge_chapters_at_end flag if save_chapters_separately is True
                if self.save_chapters_separately:
                    merge_at_end = getattr(self, "merge_chapters_at_end", True)
                    self.log_updated.emit(
                        f"- Merge chapters at the end: {'Yes' if merge_at_end else 'No'}"
                    )
                    # Display the separate chapters format if it's set
                    separate_format = getattr(self, 'separate_chapters_format', 'wav')
                    self.log_updated.emit(f"- Separate chapters format: {separate_format}")

            if self.save_option == "Choose output folder":
                self.log_updated.emit(
                    f"  - Output folder: {self.output_folder or os.getcwd()}"
                )
            self.log_updated.emit("\nInitializing TTS pipeline...")

            # Set device based on use_gpu setting
            device = "cuda" if self.use_gpu else "cpu"
            tts = self.KPipeline(
                lang_code=self.lang_code, repo_id="hexgrad/Kokoro-82M", device=device
            )

            if self.is_direct_text:
                text = self.file_name  # Treat file_name as direct text input
            else:
                encoding = detect_encoding(self.file_name)
                with open(
                    self.file_name, "r", encoding=encoding, errors="replace"
                ) as file:
                    text = file.read()

            # Clean up text using utility function
            text = clean_text(text)
            
            # Remove metadata markers from the text to be processed
            metadata_pattern = r"<<METADATA_[^:]+:[^>]*>>"
            text = re.sub(metadata_pattern, "", text)

            # --- Chapter splitting logic ---
            chapter_pattern = r"<<CHAPTER_MARKER:(.*?)>>"
            chapter_splits = list(re.finditer(chapter_pattern, text))
            chapters = []
            if chapter_splits:
                # prepend Introduction for content before first marker
                first_start = chapter_splits[0].start()
                if first_start > 0:
                    intro_text = text[:first_start].strip()
                    if intro_text:
                        chapters.append(("Introduction", intro_text))
                for idx, match in enumerate(chapter_splits):
                    start = match.end()
                    end = (
                        chapter_splits[idx + 1].start()
                        if idx + 1 < len(chapter_splits)
                        else len(text)
                    )
                    chapter_name = match.group(1).strip()
                    chapter_text = text[start:end].strip()
                    chapters.append((chapter_name, chapter_text))
            else:
                chapters = [("text", text)]
            total_chapters = len(chapters)

            # For text files with chapters, prompt user for options if not already set
            is_txt_file = not self.is_direct_text and (
                self.file_name.lower().endswith(".txt")
                or (self.display_path and self.display_path.lower().endswith(".txt"))
            )

            if (
                is_txt_file
                and total_chapters > 1
                and (
                    not hasattr(self, "save_chapters_separately")
                    or not hasattr(self, "merge_chapters_at_end")
                )
                and not self.chapter_options_set
            ):

                # Emit signal to main thread and wait
                self.chapters_detected.emit(total_chapters)
                self._chapter_options_event.wait()
                if self.cancel_requested:
                    self.conversion_finished.emit("Cancelled", None)
                    return
                self.chapter_options_set = True

            # Log all detected chapters at the beginning
            if total_chapters > 1:
                chapter_list = "\n".join(
                    [f"{i+1}) {c[0]}" for i, c in enumerate(chapters)]
                )
                self.log_updated.emit(
                    (f"\nDetected chapters ({total_chapters}):\n" + chapter_list)
                )
            else:
                self.log_updated.emit((f"\nProcessing {chapters[0][0]}..."))

            # If save_chapters_separately is enabled, find a unique suffix ONCE and use for both folder and merged file
            save_chapters_separately = getattr(self, "save_chapters_separately", False)
            chapters_out_dir = None
            suffix = ""
            base_path = self.display_path if self.display_path else self.file_name
            base_name = os.path.splitext(os.path.basename(base_path))[0]
            if self.save_option == "Save to Desktop":
                parent_dir = user_desktop_dir()
            elif self.save_option == "Save next to input file":
                parent_dir = os.path.dirname(base_path)
            else:
                parent_dir = self.output_folder or os.getcwd()
            # Ensure the output folder exists, error if it doesn't
            if not os.path.exists(parent_dir):
                self.log_updated.emit(
                    (
                        f"Output folder does not exist: {parent_dir}",
                        "red",
                    )
                )
            # Find a unique suffix for both folder and merged file, always
            counter = 1
            while True:
                suffix = f"_{counter}" if counter > 1 else ""
                chapters_out_dir_candidate = os.path.join(
                    parent_dir, f"{base_name}{suffix}_chapters"
                )
                merged_file_candidate = os.path.join(
                    parent_dir, f"{base_name}{suffix}.{self.output_format}"
                )
                merged_srt_candidate = (
                    os.path.splitext(merged_file_candidate)[0] + ".srt"
                )
                if (
                    not os.path.exists(chapters_out_dir_candidate)
                    and not os.path.exists(merged_file_candidate)
                    and (
                        self.subtitle_mode == "Disabled"
                        or not os.path.exists(merged_srt_candidate)
                    )
                ):
                    break
                counter += 1
            if save_chapters_separately and total_chapters > 1:
                chapters_out_dir = chapters_out_dir_candidate
                os.makedirs(chapters_out_dir, exist_ok=True)
                self.log_updated.emit(f"\nChapters output folder: {chapters_out_dir}")

            audio_segments = []
            subtitle_entries = []
            current_time = 0.0
            rate = 24000
            subtitle_mode = self.subtitle_mode
            raw_tts_results = []  # Collect all raw tts Result objects

            # ETR timing starts here, after model loading but before processing
            self.etr_start_time = time.time()
            self.processed_char_count = 0  # Initialize processed character count

            # Initialize current segment counter
            current_segment = 0

            # Initialize chapter times
            chapters_time = [
                {"chapter": chapter[0], "start": 0.0, "end": 0.0}
                for chapter in chapters
            ]

            # Instead of processing the whole text, process by chapter
            for chapter_idx, (chapter_name, chapter_text) in enumerate(chapters, 1):
                if total_chapters > 1:
                    self.log_updated.emit(
                        (
                            f"\nChapter {chapter_idx}/{total_chapters}: {chapter_name}",
                            "green",
                        )
                    )

                # Variables for per-chapter processing when save_chapters_separately is enabled
                chapter_audio_segments = []
                chapter_subtitle_entries = []
                chapter_current_time = 0.0

                # chapter start time
                chapter_time = chapters_time[chapter_idx - 1]
                chapter_time["start"] = current_time

                # Set split_pattern to \n+ which will split on one or more newlines
                split_pattern = r"\n+"

                # Check if the voice is a formula and load it if necessary
                if "*" in self.voice:
                    loaded_voice = get_new_voice(tts, self.voice, self.use_gpu)
                else:
                    loaded_voice = self.voice

                for result in tts(
                    chapter_text,
                    voice=loaded_voice,
                    speed=self.speed,
                    split_pattern=split_pattern,
                ):
                    # Print the result for debugging
                    # print(f"Result: {result}")
                    if self.cancel_requested:
                        self.conversion_finished.emit("Cancelled", None)
                        return
                    current_segment += 1
                    grapheme_len = len(result.graphemes)
                    self.processed_char_count += grapheme_len
                    # Log progress with both character counts and the graphemes content
                    self.log_updated.emit(
                        f"\n{self.processed_char_count:,}/{self.total_char_count:,}: {result.graphemes}"
                    )
                    raw_tts_results.append(result)

                    chunk_dur = len(result.audio) / rate
                    chunk_start = current_time
                    audio_segments.append(result.audio)

                    # For per-chapter output
                    if save_chapters_separately and total_chapters > 1:
                        chapter_audio_segments.append(result.audio)
                        chapter_chunk_start = chapter_current_time

                    # Process token timestamps for subtitle generation
                    if self.subtitle_mode != "Disabled":
                        tokens_list = getattr(result, "tokens", [])
                        tokens_with_timestamps = []
                        chapter_tokens_with_timestamps = []

                        # Process every token, regardless of text or timestamps
                        for tok in tokens_list:
                            tokens_with_timestamps.append(
                                {
                                    "start": chunk_start + (tok.start_ts or 0),
                                    "end": chunk_start + (tok.end_ts or 0),
                                    "text": tok.text,
                                    "whitespace": tok.whitespace,
                                }
                            )
                            if save_chapters_separately and total_chapters > 1:
                                chapter_tokens_with_timestamps.append(
                                    {
                                        "start": chapter_chunk_start
                                        + (tok.start_ts or 0),
                                        "end": chapter_chunk_start + (tok.end_ts or 0),
                                        "text": tok.text,
                                        "whitespace": tok.whitespace,
                                    }
                                )

                        # Process tokens according to subtitle mode
                        # Global subtitle processing
                        self._process_subtitle_tokens(
                            tokens_with_timestamps,
                            subtitle_entries,
                            self.max_subtitle_words,
                        )

                        # Per-chapter subtitle processing if enabled
                        if save_chapters_separately and total_chapters > 1:
                            self._process_subtitle_tokens(
                                chapter_tokens_with_timestamps,
                                chapter_subtitle_entries,
                                self.max_subtitle_words,
                            )

                    current_time += chunk_dur

                    # Update chapter_current_time for per-chapter output
                    if save_chapters_separately and total_chapters > 1:
                        chapter_current_time += chunk_dur

                    # Calculate percentage based on characters processed
                    percent = min(
                        int(self.processed_char_count / self.total_char_count * 100), 99
                    )

                    # Calculate ETR based on characters processed
                    etr_str = "Estimating..."
                    chars_done = self.processed_char_count
                    elapsed = time.time() - self.etr_start_time

                    # Calculate ETR if enough data is available
                    if (
                        chars_done > 0 and elapsed > 0.5
                    ):  # Check elapsed > 0.5 to avoid instability
                        avg_time_per_char = elapsed / chars_done
                        remaining = self.total_char_count - self.processed_char_count
                        if remaining > 0:
                            secs = avg_time_per_char * remaining
                            h = int(secs // 3600)
                            m = int((secs % 3600) // 60)
                            s = int(secs % 60)
                            etr_str = f"{h:02d}:{m:02d}:{s:02d}"

                    # Update progress more frequently (after each result)
                    self.progress_updated.emit(percent, etr_str)

                # Update chapter end time
                chapter_time["end"] = current_time

                # Save the individual chapter output if save_chapters_separately is enabled
                if (
                    save_chapters_separately
                    and total_chapters > 1
                    and chapters_out_dir
                    and chapter_audio_segments
                ):
                    # Sanitize chapter name for use in filenames
                    sanitized_chapter_name = re.sub(r"[^\w\-\. ]", "_", chapter_name)
                    sanitized_chapter_name = re.sub(
                        r"_+", "_", sanitized_chapter_name
                    )  # Replace multiple underscores with one
                    chapter_filename = f"{chapter_idx:02d}_{sanitized_chapter_name}"

                    # Concatenate chapter audio and save
                    chapter_audio = self.np.concatenate(chapter_audio_segments)
                    
                    # Use separate_chapters_format
                    separate_format = getattr(self, 'separate_chapters_format', 'wav')
                    
                    chapter_out_path = os.path.join(
                        chapters_out_dir, f"{chapter_filename}.{separate_format}"
                    )
                    if separate_format == "opus":
                        static_ffmpeg.add_paths()
                        proc = create_process(
                            [
                                "ffmpeg",
                                "-y",
                                "-thread_queue_size", "32768", # Increased thread_queue_size for chapter opus
                                "-f",
                                "f32le",
                                "-ar",
                                "24000",
                                "-ac",
                                "1",
                                "-i",
                                "pipe:0",
                                "-c:a",
                                "libopus",
                                "-b:a",
                                "24000",
                                chapter_out_path,
                            ],
                            stdin=subprocess.PIPE,
                            text=False  # Ensure binary stdin for audio data
                        )
                        proc.stdin.write(chapter_audio.astype("float32").tobytes())
                        proc.stdin.close()
                        proc.wait()
                    else:
                        sf.write(
                            chapter_out_path,
                            chapter_audio,
                            24000,
                            format=separate_format,
                        )

                    # Generate .srt subtitle file for chapter if not Disabled
                    if self.subtitle_mode != "Disabled" and chapter_subtitle_entries:
                        chapter_srt_path = os.path.join(
                            chapters_out_dir, f"{chapter_filename}.srt"
                        )
                        with open(
                            chapter_srt_path, "w", encoding="utf-8", errors="replace"
                        ) as srt_file:
                            for i, (start, end, text) in enumerate(
                                chapter_subtitle_entries, 1
                            ):
                                srt_file.write(
                                    f"{i}\n{self._srt_time(start)} --> {self._srt_time(end)}\n{text}\n\n"
                                )

                        self.log_updated.emit(
                            (
                                f"\nChapter {chapter_idx} saved to: {chapter_out_path}\n\nSubtitle saved to: {chapter_srt_path}",
                                "green",
                            )
                        )
                    else:
                        self.log_updated.emit(
                            (
                                f"\nChapter {chapter_idx} saved to: {chapter_out_path}",
                                "green",
                            )
                        )

            # Set progress to 100% when processing is complete
            self.progress_updated.emit(100, "00:00:00")

            # Only generate the merged output file if merge_chapters_at_end is True or save_chapters_separately is False
            merge_chapters = (
                not hasattr(self, "save_chapters_separately")
                or not self.save_chapters_separately
                or getattr(self, "merge_chapters_at_end", True)
            )
            
            intended_output_format = self.output_format # Store the original choice

            if audio_segments and merge_chapters:
                self.log_updated.emit("\nFinalizing audio file...\n")
                audio_data_np = self.np.concatenate(audio_segments)
                
                out_dir = parent_dir
                base_filepath_no_ext = os.path.join(out_dir, f"{base_name}{suffix}")

                final_out_path = None

                if intended_output_format == "m4b":
                    final_out_path = self._generate_m4b_with_chapters(audio_data_np, chapters_time, base_filepath_no_ext)
                elif intended_output_format == "opus":
                    static_ffmpeg.add_paths()
                    opus_out_path = f"{base_filepath_no_ext}.opus"
                    ffmpeg_cmd_opus = [
                        "ffmpeg", "-y",
                        "-thread_queue_size", "32768", # Increased thread_queue_size
                        "-f", "f32le", "-ar", "24000", "-ac", "1", "-i", "pipe:0",
                        "-c:a", "libopus", "-b:a", "24000", # Original bitrate
                        opus_out_path,
                    ]
                    try:
                        process = create_process(ffmpeg_cmd_opus, stdin=subprocess.PIPE, text=False)  # Ensure binary stdin
                        process.stdin.write(audio_data_np.astype("float32").tobytes())
                        process.stdin.close()
                        if process.wait() == 0:
                            final_out_path = opus_out_path
                        else:
                            self.log_updated.emit(("Opus conversion failed.", "red"))
                            final_out_path = None 
                    except Exception as e_opus:
                        self.log_updated.emit((f"Error during Opus conversion: {str(e_opus)}", "red"))
                        final_out_path = None
                else: # For other formats like wav
                    standard_out_path = f"{base_filepath_no_ext}.{intended_output_format}"
                    try:
                        sf.write(standard_out_path, audio_data_np, 24000, format=intended_output_format)
                        final_out_path = standard_out_path
                    except Exception as e_sf:
                        self.log_updated.emit((f"Failed to write audio file {standard_out_path}: {str(e_sf)}", "red"))
                        final_out_path = None

                # Subtitle and final message logic
                if final_out_path:
                    if self.subtitle_mode != "Disabled":
                        srt_path = os.path.splitext(final_out_path)[0] + ".srt"
                        with open(srt_path, "w", encoding="utf-8", errors="replace") as srt_file:
                            for i, (start, end, text) in enumerate(subtitle_entries, 1):
                                srt_file.write(
                                    f"{i}\n{self._srt_time(start)} --> {self._srt_time(end)}\n{text}\n\n"
                                )
                        self.conversion_finished.emit(
                            (
                                f"Audiobook saved to: {final_out_path}\n\nSubtitle saved to: {srt_path}",
                                "green",
                            ),
                            final_out_path,
                        )
                    else:
                        self.conversion_finished.emit(
                            (f"Audiobook saved to: {final_out_path}", "green"), final_out_path
                        )
                else:
                    self.log_updated.emit(("Audio generation failed (final_out_path was not set).", "red"))
                    self.conversion_finished.emit(("Audio generation failed.", "red"), None)
            elif audio_segments and not merge_chapters:
                self.conversion_finished.emit(
                    (
                        f"\nAll chapters processed successfully and saved to: {chapters_out_dir}",
                        "green",
                    ),
                    chapters_out_dir,
                )
            else:
                self.log_updated.emit(("No audio segments were generated.", "red"))
                self.conversion_finished.emit(("Audio generation failed.", "red"), None)
        except Exception as e:
            self.log_updated.emit((f"Error occurred: {str(e)}", "red"))
            self.conversion_finished.emit(("Audio generation failed.", "red"), None)

    def set_chapter_options(self, options):
        """Set chapter options from the dialog and resume processing"""
        self.save_chapters_separately = options["save_chapters_separately"]
        self.merge_chapters_at_end = options["merge_chapters_at_end"]
        self.waiting_for_user_input = False
        self._chapter_options_event.set()

    def _generate_m4b_with_chapters(self, audio_data_np, chapters_time, base_filepath_no_ext):
        final_wav_path = f"{base_filepath_no_ext}.wav"
        
        if not chapters_time or len(chapters_time) <= 1:
            self.log_updated.emit(
                (
                    "File contains only one chapter or no chapters were detected. Audio will be saved as a standard .wav file instead.\n",
                    "red",
                )
            )
            try:
                sf.write(final_wav_path, audio_data_np, 24000, format="wav")
                return final_wav_path
            except Exception as e_wav_single:
                self.log_updated.emit((f"Failed to save single/no chapter audio as WAV: {str(e_wav_single)}", "red"))
                return None

        output_m4b_path = f"{base_filepath_no_ext}.m4b"
        chapters_info_path = f"{base_filepath_no_ext}_chapters.txt"

        try:
            with open(chapters_info_path, "w", encoding="utf-8") as f:
                f.write(";FFMETADATA1\n")
                for chapter in chapters_time:
                    f.write(f"[CHAPTER]\n")
                    f.write(f"TIMEBASE=1/1000\n") # Using milliseconds for precision
                    f.write(f"START={int(chapter['start']*1000)}\n")
                    f.write(f"END={int(chapter['end']*1000)}\n")
                    f.write(f"title={chapter['chapter']}\n\n")

            static_ffmpeg.add_paths()
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-thread_queue_size", "32768", # Increased thread_queue_size
                "-f", "f32le", "-ar", "24000", "-ac", "1", "-i", "pipe:0",
                "-i", chapters_info_path,
                "-map", "0:a",
                "-map_metadata", "1", 
                "-map_chapters", "1",
                # Add metadata tags
                "-metadata", "composer=Narrator",
                "-metadata", "genre=Audiobook",
                # Extract metadata from text markers if available
                *self._extract_and_add_metadata_tags_to_ffmpeg_cmd(),
                "-c:a", "aac",
                "-q:a", "2", # Quality-based VBR for better quality control (lower = better, range 0.1-2)
                "-movflags", "+faststart+use_metadata_tags",  # Added for better compatibility
                output_m4b_path,
            ]

            self.log_updated.emit(f"Generating audio with chapters...\n")

            process = create_process(ffmpeg_cmd, stdin=subprocess.PIPE, text=False)  # Ensure binary stdin
            process.stdin.write(audio_data_np.astype("float32").tobytes())
            process.stdin.close()
            return_code = process.wait()

            if return_code == 0:
                return output_m4b_path
            else:
                self.log_updated.emit(
                    (f"FFmpeg failed to create M4B (return code {return_code}).\n\nFalling back to WAV.\n", "red")
                )
                sf.write(final_wav_path, audio_data_np, 24000, format="wav")
                return final_wav_path

        except Exception as e:
            self.log_updated.emit((f"Error during M4B generation: {str(e)}.\n\nFalling back to WAV.\n", "red"))
            try:
                sf.write(final_wav_path, audio_data_np, 24000, format="wav")
                return final_wav_path
            except Exception as e_wav_fallback:
                self.log_updated.emit((f"Critical error: Failed to save fallback WAV: {str(e_wav_fallback)}\n", "red"))
                return None
        finally:
            if os.path.exists(chapters_info_path):
                try:
                    os.remove(chapters_info_path)
                except Exception as e_clean:
                    self.log_updated.emit((f"Warning: Could not delete temporary chapter file {chapters_info_path}: {e_clean}", "orange"))

    def _extract_and_add_metadata_tags_to_ffmpeg_cmd(self):
        """Extract metadata tags from text content and add them to ffmpeg command"""
        metadata_options = []
        
        # Get the input text (either direct or from file)
        text = ""
        if self.is_direct_text:
            text = self.file_name
        else:
            try:
                encoding = detect_encoding(self.file_name)
                with open(self.file_name, "r", encoding=encoding, errors="replace") as file:
                    text = file.read()
            except Exception as e:
                self.log_updated.emit(f"Warning: Could not read file for metadata extraction: {e}")
                return []
                
        # Extract metadata tags using regex
        title_match = re.search(r"<<METADATA_TITLE:([^>]*)>>", text)
        artist_match = re.search(r"<<METADATA_ARTIST:([^>]*)>>", text) 
        album_match = re.search(r"<<METADATA_ALBUM:([^>]*)>>", text)
        year_match = re.search(r"<<METADATA_YEAR:([^>]*)>>", text)
        album_artist_match = re.search(r"<<METADATA_ALBUM_ARTIST:([^>]*)>>", text)
        
        # Use display path or filename as fallback for title
        filename = os.path.splitext(os.path.basename(self.display_path if self.display_path else self.file_name))[0]
        
        # Add title metadata
        if title_match:
            metadata_options.extend(["-metadata", f"title=Dinginliğin Gücü"])
        else:
            metadata_options.extend(["-metadata", f"title={filename}"])
            
        # Add artist metadata
        if artist_match:
            metadata_options.extend(["-metadata", f"artist={artist_match.group(1)}"])
        else:
            metadata_options.extend(["-metadata", f"artist=Unknown"])
            
        # Add album metadata
        if album_match:
            metadata_options.extend(["-metadata", f"album={album_match.group(1)}"])
        else:
            metadata_options.extend(["-metadata", f"album={filename}"])
            
        # Add year metadata
        if year_match:
            metadata_options.extend(["-metadata", f"date={year_match.group(1)}"])
        else:
            # Use current year if year is not specified
            import datetime
            current_year = datetime.datetime.now().year
            metadata_options.extend(["-metadata", f"date={current_year}"])

        # Add album artist metadata
        if album_artist_match:
            metadata_options.extend(["-metadata", f"album_artist={album_artist_match.group(1)}"])
        else:
            metadata_options.extend(["-metadata", f"album_artist=Unknown"])
            
        # Add these to ffmpeg command
        return metadata_options

    def _srt_time(self, t):
        """Helper function to format time for SRT files"""
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def _process_subtitle_tokens(
        self, tokens_with_timestamps, subtitle_entries, max_subtitle_words
    ):
        """Helper function to process subtitle tokens according to the subtitle mode"""
        if not tokens_with_timestamps:
            return

        if self.subtitle_mode == "Sentence" or self.subtitle_mode == "Sentence + Comma":
            # Define separator pattern based on mode
            separator = r"[.!?]" if self.subtitle_mode == "Sentence" else r"[.!?,]"
            current_sentence = []
            word_count = 0

            for token in tokens_with_timestamps:
                current_sentence.append(token)
                word_count += 1

                # Split sentences based on separator or word count
                if (
                    re.search(separator, token["text"]) and token["whitespace"] == " "
                ) or word_count >= max_subtitle_words:
                    if current_sentence:
                        # Create subtitle entry for this sentence
                        start_time = current_sentence[0]["start"]
                        end_time = current_sentence[-1]["end"]

                        # Simplified text joining logic
                        sentence_text = ""
                        for t in current_sentence:
                            sentence_text += t["text"] + (t.get("whitespace", "") or "")

                        subtitle_entries.append(
                            (start_time, end_time, sentence_text.strip())
                        )
                        current_sentence = []
                        word_count = 0

            # Add any remaining tokens as a sentence
            if current_sentence:
                start_time = current_sentence[0]["start"]
                end_time = current_sentence[-1]["end"]

                # Simplified text joining logic
                sentence_text = ""
                for t in current_sentence:
                    sentence_text += t["text"] + (t.get("whitespace", "") or "")

                subtitle_entries.append((start_time, end_time, sentence_text.strip()))

        else:
            # Word count-based grouping
            try:
                word_count = int(self.subtitle_mode.split()[0])
                word_count = min(word_count, max_subtitle_words)
            except (ValueError, IndexError):
                word_count = 1

            # Combine punctuation with preceding words
            processed_tokens = []
            i = 0
            while i < len(tokens_with_timestamps):
                token = tokens_with_timestamps[i].copy()

                # Look ahead for punctuation
                while i + 1 < len(tokens_with_timestamps) and re.match(
                    r"^[^\w\s]+$", tokens_with_timestamps[i + 1]["text"]
                ):
                    token["text"] += tokens_with_timestamps[i + 1]["text"]
                    token["end"] = tokens_with_timestamps[i + 1]["end"]
                    token["whitespace"] = tokens_with_timestamps[i + 1]["whitespace"]
                    i += 1

                processed_tokens.append(token)
                i += 1

            # Group words into subtitle entries
            for i in range(0, len(processed_tokens), word_count):
                group = processed_tokens[i : i + word_count]
                if group:
                    text = "".join(
                        t["text"] + (t.get("whitespace", "") or "") for t in group
                    )
                    subtitle_entries.append(
                        (group[0]["start"], group[-1]["end"], text.strip())
                    )

    def cancel(self):
        self.cancel_requested = True
        self.waiting_for_user_input = (
            False  # Also release the wait if we're waiting for input
        )


class VoicePreviewThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        np_module,
        kpipeline_class,
        lang_code,
        voice,
        speed,
        use_gpu=False,
        parent=None,
    ):
        super().__init__(parent)
        self.np_module = np_module
        self.kpipeline_class = kpipeline_class
        self.lang_code = lang_code
        self.voice = voice
        self.speed = speed
        self.use_gpu = use_gpu

    def run(self):
        print(
            f"\nVoice: {self.voice}\nLanguage: {self.lang_code}\nSpeed: {self.speed}\nGPU: {self.use_gpu}\n"
        )
        try:
            device = "cuda" if self.use_gpu else "cpu"
            tts = self.kpipeline_class(
                lang_code=self.lang_code, repo_id="hexgrad/Kokoro-82M", device=device
            )
            # Enable voice formula support for preview
            if "*" in self.voice:
                loaded_voice = get_new_voice(tts, self.voice, self.use_gpu)
            else:
                loaded_voice = self.voice
            sample_text = get_sample_voice_text(self.lang_code)
            audio_segments = []
            for result in tts(
                sample_text, voice=loaded_voice, speed=self.speed, split_pattern=None
            ):
                audio_segments.append(result.audio)
            if audio_segments:
                audio = self.np_module.concatenate(audio_segments)
                # Create temp wav file in a folder in the system temp directory
                temp_dir = os.path.join(tempfile.gettempdir(), PROGRAM_NAME)
                os.makedirs(temp_dir, exist_ok=True)
                fd, temp_path = tempfile.mkstemp(
                    prefix="abogen_", suffix=".wav", dir=temp_dir
                )
                os.close(fd)
                sf.write(temp_path, audio, 24000)
                self.temp_wav = temp_path
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Voice preview error: {str(e)}")


class PlayAudioThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, wav_path, parent=None):
        super().__init__(parent)
        self.wav_path = wav_path

    def run(self):
        try:
            import pygame
            import time as _time

            pygame.mixer.init()
            pygame.mixer.music.load(self.wav_path)
            pygame.mixer.music.play()
            # Wait until playback is finished
            while pygame.mixer.music.get_busy():
                _time.sleep(0.2)
            pygame.mixer.music.unload()
            pygame.mixer.quit()  # Quit the mixer
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Audio playback error: {str(e)}")
