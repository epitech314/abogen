# abogen <img width="40px" title="abogen icon" src="https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/abogen/assets/icon.ico" align="right" style="padding-left: 10px; padding-top:5px;">

[![Build Status](https://github.com/denizsafak/abogen/actions/workflows/test_pip.yml/badge.svg)](https://github.com/denizsafak/abogen/actions)
![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python)
[![Operating Systems](https://img.shields.io/badge/os-windows%20%7C%20linux%20%7C%20macos%20-blue)](https://github.com/denizsafak/abogen/releases/latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-maroon.svg)](https://opensource.org/licenses/MIT)

Abogen is a powerful text-to-speech conversion tool that makes it easy to turn ePub, PDF, or text files into high-quality audio with matching subtitles in seconds. Use it for audiobooks, voiceovers for Instagram, YouTube, TikTok, or any project that needs natural-sounding text-to-speech, using [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).

<img title="Abogen Main" src='https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/demo/abogen.png' width="380"> <img title="Abogen Processing" src='https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/demo/abogen2.png' width="380">

## Demo
https://github.com/user-attachments/assets/cb66512d-0a52-48c3-bda4-f1e6a03fb8d6


> This demo was generated in just 5 seconds, producing ∼1 minute of audio with perfectly synced subtitles. To create a similar video, see [the demo guide](https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/demo/README.md).

## `How to install?`
### Windows
Go to [espeak-ng latest release](https://github.com/espeak-ng/espeak-ng/releases/latest) download and run the *.msi file.
```bash
# For NVIDIA GPUs:
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install abogen
```
Alternatively, for an easier setup on Windows:
1. [Download](https://github.com/denizsafak/abogen/archive/refs/heads/main.zip) the repository
2. Extract the ZIP file
3. Run `WINDOWS_INSTALL.bat` by double-clicking it

This method handles everything automatically - installing all dependencies including CUDA in a self-contained environment without requiring a separate Python installation. (You still need to install [espeak-ng](https://github.com/espeak-ng/espeak-ng/releases/latest).)

### Mac
```bash
brew install espeak-ng
pip install abogen # (I have not tested it)
```
### Linux
```bash
# Ubuntu/Debian
sudo apt install espeak-ng
# Arch Linux
sudo pacman -S espeak-ng
# Fedora
sudo dnf install espeak-ng
pip install abogen
```
> If you get "No matching distribution found" error, try installing it on supported Python (3.10 to 3.12). You can use [pyenv](https://github.com/pyenv/pyenv) to manage multiple Python versions easily in Linux.

Then simply run by typing:

```bash
abogen
```

## `How to use?`
1) Drag and drop any ePub, PDF, or text file (or use the built-in text editor)
2) Configure the settings:
    - Set speech speed
    - Select a voice
    - Select subtitle generation style (by sentence, word, etc.)
    - Select output format
    - Select where to save the output
3) Hit Start

## `In action`
<img title="Abogen in action" src='https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/demo/abogen.gif'> 

Here’s Abogen in action: in this demo, it processes ∼3,000 characters of text in just 11 seconds and turns it into 3 minutes and 28 seconds of audio, and I have a low-end **GTX 2060 Mobile laptop GPU**. Your results may vary depending on your hardware.

## `Key Features`
- **Supported formats**: `ePub`, `PDF`, or `.TXT` files (or use built-in text editor)
- **Speed**: Adjust speech rate from `0.1x` to `2.0x`
- **Voices**: First letter of the language code (e.g., `a` for American English, `b` for British English, etc.), second letter is for `m` for male and `f` for female.
- **Generate subtitles**: `Disabled`, `Sentence`, `Sentence + Comma`, `1 word`, `2 words`, `3 words`, etc. (Represents the number of words in each subtitle entry)
- **Output formats**: `.WAV`, `.FLAC`, or `.MP3`
- **Save location**: `Save next to input file`, `Save to desktop`, or `Choose output folder`
- **Chapter Control**: Select specific `chapters` from ePUBs or `chapters + pages` from PDFs.
- **Options**:
    - **Configure max words per subtitle**: Automatically configures the maximum number of words per subtitle entry.
    - **Create desktop shortcut**: Creates a shortcut on your desktop for easy access.
    - **Open config.json directory**: Opens the directory where the configuration file is stored.
    - **Open temp directory**: Opens the temporary directory where converted text files are stored.
    - **Clear all teporary files**: Deletes all temporary files created during the conversion process.
    - **Check for updates at startup**: Automatically checks for updates when the program starts.
- **After conversion**: `Open file`, `Go to folder`, `New conversion`, or `Go back`.

## `Supported Languages`
```
# 🇺🇸 'a' => American English, 🇬🇧 'b' => British English
# 🇪🇸 'e' => Spanish es
# 🇫🇷 'f' => French fr-fr
# 🇮🇳 'h' => Hindi hi
# 🇮🇹 'i' => Italian it
# 🇯🇵 'j' => Japanese: pip install misaki[ja]
# 🇧🇷 'p' => Brazilian Portuguese pt-br
# 🇨🇳 'z' => Mandarin Chinese: pip install misaki[zh]
```
For a complete list of supported languages and voices, refer to Kokoro's [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). To listen to sample audio outputs, see [SAMPLES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/SAMPLES.md).

## `Similar Projects`
Abogen is a standalone project, but it is inspired by and shares some similarities with other projects. Here are a few:
- [audiblez](https://github.com/santinic/audiblez): Generate audiobooks from e-books. **(Has CLI and GUI support)**
- [autiobooks](https://github.com/plusuncold/autiobooks): Automatically convert epubs to audiobooks
- [pdf-narrator](https://github.com/mateogon/pdf-narrator): Convert your PDFs and EPUBs into audiobooks effortlessly.

## `Roadmap`
- [ ] Improve PDF support for better text extraction.
- [ ] Add chapter metadata for .m4a files using ffmpeg-bin.
- [ ] Add support for different languages in GUI.
- [ ] Add voice formula feature that enables mixing different voice models.
- [ ] Add support for kokoro-onnx.

## `Contributing`
I welcome contributions! If you have ideas for new features, improvements, or bug fixes, please fork the repository and submit a pull request.
### For developers and contributors
If you'd like to modify the code and contribute to development, you can [download the repository](https://github.com/denizsafak/abogen/archive/refs/heads/main.zip), extract it and run the following commands to build **or** install the package:
```bash
# Go to the directory where you extracted the repository and run:
pip install -e .      # Installs the package in editable mode
python -m build       # Builds the package in dist folder
abogen                # Opens the GUI
```
Feel free to explore the code and make any changes you like.

## `Credits`
Abogen uses [Kokoro](https://github.com/hexgrad/kokoro) for its high-quality, natural-sounding text-to-speech synthesis. Huge thanks to the Kokoro project and its contributors for making this possible.

## `License`
This project is available under the MIT License - see the [LICENSE](https://raw.githubusercontent.com/denizsafak/abogen/refs/heads/main/LICENSE) file for details.
[Kokoro](https://github.com/hexgrad/kokoro) is licensed under [Apache-2.0](https://github.com/hexgrad/kokoro/blob/main/LICENSE) which allows commercial use, modification, distribution, and private use.

> [!IMPORTANT]
> Subtitle generation currently works only for English. This is because Kokoro provides timestamp tokens only for English text. If you want subtitles in other languages, please request this feature in the [Kokoro project](https://github.com/hexgrad/kokoro). For more technical details, see [this line](https://github.com/hexgrad/kokoro/blob/6d87f4ae7abc2d14dbc4b3ef2e5f19852e861ac2/kokoro/pipeline.py#L383) in the Kokoro's code.

> Tags: audiobook, kokoro, text-to-speech, TTS, audiobook generator, audiobooks, text to speech, audiobook maker, audiobook creator, audiobook generator, voice-synthesis, text to audio, text to audio converter, text to speech converter, text to speech generator, text to speech software, text to speech app, epub to audio, pdf to audio, content-creation, media-generation
