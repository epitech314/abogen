# FFmpeg commands for creating videos:
#
# For WebM (smaller filesize):
# ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=your_subtitle_demo.ass" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -shortest demo.webm
# 
# For MP4 (higher quality):
# ffmpeg -loop 1 -framerate 24 -i bg.jpg -i audio.wav -vf "ass=your_subtitle_demo.ass" -c:v libx264 -preset slow -crf 18 -movflags +faststart -c:a copy -shortest demo.mp4
#
# Note: Replace 'audio.wav' with your audio file and 'your_subtitle_demo.ass' with your processed subtitle file


import re
import sys
from datetime import timedelta

def parse_time(s):
    # For ASS format
    if ':' in s and '.' in s:
        h, m, s = s.split(':')
        sec, cs = s.split('.')
        return timedelta(hours=int(h), minutes=int(m), seconds=int(sec), milliseconds=int(cs) * 10)
    # For SRT format (00:00:00,000)
    elif ':' in s and ',' in s:
        parts = s.split(':')
        h = int(parts[0])
        m = int(parts[1])
        sec_parts = parts[2].split(',')
        sec = int(sec_parts[0])
        ms = int(sec_parts[1])
        return timedelta(hours=h, minutes=m, seconds=sec, milliseconds=ms)
    return None

def format_time(t):
    total_seconds = int(t.total_seconds())
    cs = int((t.total_seconds() - total_seconds) * 100)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h}:{m:02}:{s:02}.{cs:02}"

# Desired script info and style
DESIRED_SCRIPT_INFO = """[Script Info]
Title: Centered Subs
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
"""

DESIRED_STYLE = """[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,0,5,10,10,10,1
"""

def process_subtitle_file(input_file):
    output_file = input_file.replace('.ass', '_demo.ass').replace('.srt', '_demo.ass')
    if output_file == input_file:
        output_file = f"{input_file}_demo.ass"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    # Check if it's an SRT file
    is_srt = input_file.lower().endswith('.srt')
    
    if is_srt:
        return convert_srt_to_ass(input_file, output_file, lines)
    
    # Process ASS file
    header = []
    events = []
    in_events = False
    script_info_found = False
    styles_found = False

    for line in lines:
        if line.strip().startswith("[Script Info]"):
            script_info_found = True
            header.append(DESIRED_SCRIPT_INFO)
            continue
        elif line.strip().startswith("[V4+ Styles]"):
            styles_found = True
            header.append(DESIRED_STYLE)
            continue
        elif line.strip().startswith("[Events]"):
            in_events = True
            header.append(line)
        elif not in_events:
            if not script_info_found and not styles_found:
                header.append(line)
        else:
            if line.startswith("Dialogue:"):
                events.append(line)
            else:
                header.append(line)

    parsed_events = []
    for line in events:
        match = re.match(r"Dialogue: \d,([^,]+),([^,]+),", line)
        if not match:
            parsed_events.append((None, None, line))
            continue
        start = parse_time(match.group(1))
        end = parse_time(match.group(2))
        parsed_events.append((start, end, line))

    # Cut overlaps
    fixed_lines = []
    for i in range(len(parsed_events)):
        start, end, line = parsed_events[i]
        if start is None:
            fixed_lines.append(line)
            continue

        # Check for next subtitle
        if i + 1 < len(parsed_events):
            next_start, _, _ = parsed_events[i + 1]
            if end > next_start:
                end = next_start  # cut current subtitle to stop at next one's start

        fixed_line = re.sub(r"Dialogue: \d,[^,]+,[^,]+,", 
                          f"Dialogue: 0,{format_time(start)},{format_time(end)},", 
                          line, count=1)
        fixed_lines.append(fixed_line)

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(header)
            f.writelines(fixed_lines)
        print(f"✅ Successfully processed. Output file: {output_file}")
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)

def convert_srt_to_ass(input_file, output_file, lines):
    """Convert SRT format to ASS format."""
    events = []
    subtitle_blocks = []
    current_block = []
    
    # Parse SRT file
    for line in lines:
        line = line.strip()
        if not line:
            if current_block:
                subtitle_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    
    # Don't forget the last block
    if current_block:
        subtitle_blocks.append(current_block)
    
    # Process subtitle blocks
    for block in subtitle_blocks:
        if len(block) < 3:
            continue  # Invalid block
            
        # Skip the subtitle number
        timing_line = block[1]
        
        # Parse timing information
        timing_match = re.match(r'(\d+:\d+:\d+,\d+)\s+-->\s+(\d+:\d+:\d+,\d+)', timing_line)
        if not timing_match:
            continue
            
        start_time = parse_time(timing_match.group(1))
        end_time = parse_time(timing_match.group(2))
        
        # Combine text lines
        text = "\\N".join(block[2:])
        
        # Create ASS Dialogue line
        dialogue_line = f"Dialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{text}\n"
        events.append(dialogue_line)
    
    # Create ASS file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(DESIRED_SCRIPT_INFO)
            f.write(DESIRED_STYLE)
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            f.writelines(events)
        print(f"✅ Successfully converted SRT to ASS. Output file: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: No input file specified")
        print(f"Usage: {sys.argv[0]} <input_file.ass|input_file.srt>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_subtitle_file(input_file)