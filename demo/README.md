# How to Create Videos Like the Demo (52 seconds in just 736kB!)

This guide explains how I created such a small yet effective demonstration video, being only **736kB** for a **52-second video**!

https://github.com/user-attachments/assets/9e4fc237-a3cd-46bd-b82c-c608336d6411

### What You Need

- A background image (bg.jpg)
- The subtitle file (.ass) **(created by Abogen)**
    - Select `ass(centered narrow)` as subtitle format in settings.
- The audio recording (.wav) **(created by Abogen)**
- FFmpeg installed on your computer:

```bash
# Windows
winget install ffmpeg

# MacOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

## Create the Video (.mp4) (Recommended)

Run this FFmpeg command to create the video:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i demo.wav -vf "ass=demo.ass" -c:v libx264 -pix_fmt yuv420p -preset slow -crf 18 -c:a aac -b:a 192k -movflags +faststart -shortest demo.mp4
```

## For Smaller Filesize (.webm)

If you need a smaller video file, use this command:

```
ffmpeg -loop 1 -framerate 24 -i bg.jpg -i demo.wav -vf "ass=demo.ass" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -shortest demo.webm
```




