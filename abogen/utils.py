import os
import json
import warnings
import platform
import subprocess
import re
from threading import Thread

# suppress warnings and disable HF hub symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

# Language description mapping
LANGUAGE_DESCRIPTIONS = {
    "a": "American English",
    "b": "British English",
    "e": "Spanish",
    "f": "French",
    "h": "Hindi",
    "i": "Italian",
    "j": "Japanese",
    "p": "Brazilian Portuguese",
    "z": "Mandarin Chinese",
}

# Supported languages for subtitle generation
# Currently, only 'a (American English)' and 'b (British English)' are supported for subtitle generation.
# This is because tokens that contain timestamps are not generated for other languages in the Kokoro pipeline.
# Please refer to: https://github.com/hexgrad/kokoro/blob/6d87f4ae7abc2d14dbc4b3ef2e5f19852e861ac2/kokoro/pipeline.py
# 383 English processing (unchanged)
# 384 if self.lang_code in 'ab':
SUPPORTED_LANGUAGES_FOR_SUBTITLE_GENERATION = [
    "a",
    "b",
]

# Voice and sample text constants
VOICES_INTERNAL = [
    "af_alloy",
    "af_aoede",
    "af_bella",
    "af_heart",
    "af_jessica",
    "af_kore",
    "af_nicole",
    "af_nova",
    "af_river",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_echo",
    "am_eric",
    "am_fenrir",
    "am_liam",
    "am_michael",
    "am_onyx",
    "am_puck",
    "am_santa",
    "bf_alice",
    "bf_emma",
    "bf_isabella",
    "bf_lily",
    "bm_daniel",
    "bm_fable",
    "bm_george",
    "bm_lewis",
    "ef_dora",
    "em_alex",
    "em_santa",
    "ff_siwis",
    "hf_alpha",
    "hf_beta",
    "hm_omega",
    "hm_psi",
    "if_sara",
    "im_nicola",
    "jf_alpha",
    "jf_gongitsune",
    "jf_nezumi",
    "jf_tebukuro",
    "jm_kumo",
    "pf_dora",
    "pm_alex",
    "pm_santa",
    "zf_xiaobei",
    "zf_xiaoni",
    "zf_xiaoxiao",
    "zf_xiaoyi",
    "zm_yunjian",
    "zm_yunxi",
    "zm_yunxia",
    "zm_yunyang",
]

# Voice and sample text mapping
SAMPLE_VOICE_TEXTS = {
    "a": "This is a sample of the selected voice.",
    "b": "This is a sample of the selected voice.",
    "e": "Este es una muestra de la voz seleccionada.",
    "f": "Ceci est un exemple de la voix sélectionnée.",
    "h": "यह चयनित आवाज़ का एक नमूना है।",
    "i": "Questo è un esempio della voce selezionata.",
    "j": "これは選択した声のサンプルです。",
    "p": "Este é um exemplo da voz selecionada.",
    "z": "这是所选语音的示例。",
}

# flags mapping for voice display
FLAGS = {
    "a": "🇺🇸",
    "b": "🇬🇧",
    "e": "🇪🇸",
    "f": "🇫🇷",
    "h": "🇮🇳",
    "i": "🇮🇹",
    "j": "🇯🇵",
    "p": "🇧🇷",
    "z": "🇨🇳",
}


def get_resource_path(package, resource):
    """
    Get the path to a resource file, with fallback to local file system.

    Args:
        package (str): Package name containing the resource (e.g., 'abogen.assets')
        resource (str): Resource filename (e.g., 'icon.ico')

    Returns:
        str: Path to the resource file, or None if not found
    """
    from importlib import resources

    # Try using importlib.resources first
    try:
        with resources.path(package, resource) as resource_path:
            if os.path.exists(resource_path):
                return str(resource_path)
    except (ImportError, FileNotFoundError):
        pass

    # Fallback to local file system
    try:
        # Extract the subdirectory from package name (e.g., 'assets' from 'abogen.assets')
        subdir = package.split(".")[-1] if "." in package else package
        local_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), subdir, resource
        )
        if os.path.exists(local_path):
            return local_path
    except Exception:
        pass

    return None


def get_version():
    """Return the current version of the application."""
    try:
        with open(get_resource_path("abogen", "VERSION"), "r") as f:
            return f.read().strip()
    except Exception:
        return "Unknown"


# Define config path
def get_user_config_path():
    if os.name == "nt":
        config_dir = os.path.join(os.environ["APPDATA"], "abogen")
    else:
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "abogen")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


CONFIG_PATH = get_user_config_path()

_sleep_procs = {"Darwin": None, "Linux": None}  # Store sleep prevention processes


def clean_text(text):
    # Trim spaces and tabs at the start and end of each line, preserving blank lines
    text = "\n".join(line.strip() for line in text.splitlines())
    # Standardize paragraph breaks (multiple newlines become exactly two) and trim overall whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # Replace single newlines with spaces, but preserve double newlines
    # text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Collapse multiple spaces and tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    return text


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


def calculate_text_length(text):
    # Remove double newlines (replace them with single newlines)
    cleaned_text = text.replace("\n\n", "")
    # Calculate character count
    char_count = len(cleaned_text)
    return char_count


def get_gpu_acceleration(enabled):
    from torch.cuda import is_available

    if not enabled:
        return "CUDA GPU available but using CPU.", False

    if is_available():
        return "CUDA GPU available and enabled.", True
    return "CUDA GPU is not available. Using CPU.", False


def prevent_sleep_start():
    system = platform.system()
    if system == "Windows":
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(
            0x80000000 | 0x00000001 | 0x00000040
        )  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
    elif system == "Darwin":
        _sleep_procs["Darwin"] = subprocess.Popen(["caffeinate"])
    elif system == "Linux":
        try:
            _sleep_procs["Linux"] = subprocess.Popen(
                [
                    "systemd-inhibit",
                    "--what=sleep",
                    "--why=TextToAudiobook conversion",
                    "sleep",
                    "999999",
                ]
            )
        except Exception:
            try:
                subprocess.Popen(["xdg-screensaver", "reset"])
            except Exception:
                pass


def prevent_sleep_end():
    system = platform.system()
    if system == "Windows":
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS
    elif system in ("Darwin", "Linux") and _sleep_procs[system]:
        try:
            _sleep_procs[system].terminate()
            _sleep_procs[system] = None
        except Exception:
            pass


def load_numpy_kpipeline():
    import numpy as np
    from kokoro import KPipeline

    return np, KPipeline


class LoadPipelineThread(Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def run(self):
        try:
            np_module, kpipeline_class = load_numpy_kpipeline()
            self.callback(np_module, kpipeline_class, None)
        except Exception as e:
            self.callback(None, None, str(e))
