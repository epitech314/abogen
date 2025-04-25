# How to Create Videos Like the Demo (52 seconds in just 736kB!)

The demo video showcases Abogen - an all-in-one tool for turning text into something you can see and hear. This guide explains how I created such a small yet effective demonstration video.

## About the Demo

The demo video shows how Abogen:
- Converts text files (ePub, PDF, text) into audio with synchronized subtitles
- Uses Kokoro (a powerful text-to-speech engine) to create natural voices
- Works completely on your computer for privacy and security
- Offers an easy interface for creating audiobooks and voiceovers
- Can be used for Instagram, YouTube, TikTok, or any content creation

And it does all this while being only **736kB** for a **52-second video**!

## How I Created This Tiny Video

### What You Need

- A background image (bg.jpg)
- The subtitle file (.srt) created by Abogen
- The audio recording (.wav) created by Abogen
- FFmpeg installed on your computer:

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
python convert.py abogen_subtitles.srt
```

This creates a properly formatted subtitle file called "abogen_subtitles_demo.ass" with centered text and appropriate styling.

### Step 2: Create the Video

Run this FFmpeg command to create the tiny video:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=abogen_subtitles_demo.ass" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -shortest demo.webm
```

That's it! The magic happens because:
- We use a single static background image instead of many frames
- The subtitles are stored as text (vector data), not as pixels
- VP9 video codec with Opus audio provides excellent compression

## For Higher Quality (But Larger) Video

If you need better quality for distribution, use this command instead:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=abogen_subtitles_demo.ass" -c:v libx264 -preset slow -crf 18 -movflags +faststart -c:a copy -shortest demo.mp4
```

This creates an MP4 file that's compatible with more devices but larger in size.