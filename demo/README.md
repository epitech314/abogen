# How to Create Videos Like the Demo (52 seconds in just 736kB!)

This guide explains how I created such a small yet effective demonstration video, being only **736kB** for a **52-second video**!

https://github.com/user-attachments/assets/9e4fc237-a3cd-46bd-b82c-c608336d6411

### What You Need

- A background image (bg.jpg)
- The subtitle file (.srt) **(created by Abogen)**
- The audio recording (.wav) **(created by Abogen)**
- [Python](https://www.python.org/downloads/) and FFmpeg installed on your computer:

```bash
# Windows
winget install ffmpeg

# MacOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Step 1: Process the Subtitle File

Run this command to process Abogen's subtitle file:

```
python convert.py your_subtitle.srt
```

This creates a properly formatted subtitle file called "your_subtitle_demo.ass" with centered text and appropriate styling.

### Step 2: Create the Video (.webm)

Run this FFmpeg command to create the tiny video:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=your_subtitle_demo.ass" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -shortest demo.webm
```

## For Higher Quality (But Larger) Video (.mp4)

If you need better quality for distribution, use this command instead:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=your_subtitle_demo.ass" -c:v libx264 -preset slow -crf 18 -movflags +faststart -c:a copy -shortest demo.mp4
```

This creates an MP4 file that's compatible with more devices but larger in size.
