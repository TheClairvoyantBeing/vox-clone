import os
import subprocess
import re
from datetime import datetime

def create_output_folder(topic):
    # Ensure there's a folder for this specific generation session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = re.sub(r'[^\w\s-]', '', topic)[:40].strip().replace(" ", "_")
    folder_name = f"outputs/session_{timestamp}_{safe_topic}"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def convert_to_wav(input_path, output_path):
    # FFmpeg command to 22050 Hz 1-channel mono wav
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "22050", "-ac", "1", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except Exception as e:
        print(f"[ERROR] FFmpeg conversion failed for {input_path}: {e}")
        return False

def get_audio_duration(path):
    # Optional: use ffmpeg to get duration
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)
    except:
        return 0.0
