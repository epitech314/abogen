import os
import sys
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from abogen.gui import abogen
from abogen.utils import get_resource_path

# Ensure sys.stdout and sys.stderr are valid in GUI mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Enable MPS GPU acceleration on Mac Apple Silicon
if platform.system() == "Darwin" and platform.processor() == "arm":
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Set application ID for Windows taskbar icon
if platform.system() == "Windows":
    import ctypes

    app_id = "abogen.v1.0.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

# Handle Wayland on Linux GNOME
if platform.system() == "Linux":
    xdg_session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "gnome" in desktop and xdg_session == "wayland" and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland"


def main():
    """Main entry point for console usage."""
    app = QApplication(sys.argv)

    # Set application icon using get_resource_path from utils
    icon_path = get_resource_path("abogen.assets", "icon.ico")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    ex = abogen()
    ex.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
