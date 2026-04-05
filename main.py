# main.py
import os
import sys
import argparse
from modules.utils import create_output_folder, convert_to_wav
from modules.story_engine import StoryEngine
from modules.audio_engine import AudioEngine
from modules.voice_engine import VoiceEngine

def cleanup_empty_folders(root):
    for dir_path, dir_names, file_names in os.walk(root, topdown=False):
        if not dir_names and not file_names:
            try:
                os.rmdir(dir_path)
            except OSError:
                pass

def select_mode():
    print("\n=== VOX-CLONE — MODE SELECT ===")
    print("1. Story only     (generate script, save story.txt)")
    print("2. TTS only       (narrate an existing story.txt)")
    print("3. Auto           (story → TTS, full pipeline)")
    choice = input("Select (1/2/3): ").strip()
    return {"1": "story", "2": "tts", "3": "auto"}.get(choice, "auto")

def select_voice(voice_engine):
    print("\n--- VOICE SELECTION ---")
    print("1. ElevenLabs pre-downloaded samples")
    print("2. Your own voice sample")
    voice_choice = input("Select (1/2): ").strip()
    reference_path = ""
    if voice_choice == "1":
        wav_dir = voice_engine.wav_dir
        if not os.path.exists(wav_dir) or not os.listdir(wav_dir):
            voice_engine.download_voice_samples()
        categories = sorted([
            d for d in os.listdir(wav_dir)
            if os.path.isdir(os.path.join(wav_dir, d)) and os.listdir(os.path.join(wav_dir, d))
        ])
        if not categories:
            print("[ERROR] No voice categories found.")
            sys.exit(1)
        for idx, cat in enumerate(categories, 1):
            print(f"  {idx}. {cat}")
        cat_idx = int(input("Category: ").strip()) - 1
        cat_path = os.path.join(wav_dir, categories[cat_idx])
        voices = sorted([f for f in os.listdir(cat_path) if f.endswith(".wav")])
        for idx, voice in enumerate(voices, 1):
            print(f"  {idx}. {voice.split('__')[0]}")
        voice_idx = int(input("Voice: ").strip()) - 1
        reference_path = os.path.join(cat_path, voices[voice_idx])
    else:
        sample_path = input("Path to voice sample: ").strip().replace('"', '')
        if not os.path.exists(sample_path):
            print(f"[ERROR] Not found: {sample_path}")
            sys.exit(1)
        ext = os.path.splitext(sample_path)[1].lower()
        if ext in [".mp4", ".mp3", ".m4a"]:
            temp_wav = "temp_reference.wav"
            if convert_to_wav(sample_path, temp_wav):
                reference_path = temp_wav
            else:
                sys.exit(1)
        else:
            reference_path = sample_path
    return reference_path

def main():
    """
    Main entry point for Vox-Clone. 
    Supports three modes:
    1. Story only: Generates a horror story script based on a gist.
    2. TTS only: Narrates an existing story.txt file using a voice clone.
    3. Auto: Full end-to-end pipeline (Story → Narration).
    """
    print("=" * 60)
    print("      VOX-CLONE — MODULAR AI STORY PIPELINE")
    print("=" * 60)

    mode = select_mode()

    # Mode 2: TTS-only (requires an existing text file)
    if mode == "tts":
        story_file = input("\nPath to existing story.txt: ").strip().replace('"', '')
        if not os.path.exists(story_file):
            print(f"[ERROR] Not found: {story_file}")
            sys.exit(1)
        with open(story_file, "r", encoding="utf-8") as f:
            story_text = f.read()
        
        # Use parent folder name as the topic for organizing outputs
        topic = os.path.basename(os.path.dirname(story_file)) or "tts_session"
        
        voice_engine = VoiceEngine()
        reference_path = select_voice(voice_engine)
        try:
            audio_engine = AudioEngine()
        except Exception as e:
            print(e)
            sys.exit(1)
        
        session_root = create_output_folder(topic)
        output_audio = os.path.join(session_root, "narration.wav")
        audio_engine.generate_narration(story_text, reference_path, output_audio)
        
        if os.path.exists("temp_reference.wav"):
            os.remove("temp_reference.wav")
        cleanup_empty_folders(".")
        return

    # Mode 1 & 3: Require story parameters
    print("\n--- STORY CONFIG ---")
    topic = input("Story idea / gist: ").strip()
    print("\n1. 30 min  2. 45 min  3. 60 min  4. Custom")
    dur_choice = input("Duration (1/2/3/4): ").strip()
    duration_map = {"1": "30", "2": "45", "3": "60"}
    duration_str = input("Minutes: ").strip() if dur_choice == "4" else duration_map.get(dur_choice, "30")

    try:
        story_engine = StoryEngine()
    except ValueError as e:
        print(e)
        sys.exit(1)

    session_root = create_output_folder(topic)
    story_file = os.path.join(session_root, "story.txt")

    # Step 1: Generate the story text
    story_text = story_engine.generate_story(topic, duration_str)
    if not story_text:
        print("[ERROR] Story generation failed.")
        sys.exit(1)

    with open(story_file, "w", encoding="utf-8") as f:
        f.write(story_text)
    print(f"\n[INFO] Story saved → {story_file}")

    if mode == "story":
        print("\n[INFO] Story-only mode complete. Run TTS separately with mode 2.")
        cleanup_empty_folders(".")
        return

    # Step 2: Auto Mode continues to TTS Narration
    voice_engine = VoiceEngine()
    reference_path = select_voice(voice_engine)
    try:
        audio_engine = AudioEngine()
    except Exception as e:
        print(e)
        sys.exit(1)

    output_audio = os.path.join(session_root, "narration.wav")
    audio_engine.generate_narration(story_text, reference_path, output_audio)

    if os.path.exists("temp_reference.wav"):
        os.remove("temp_reference.wav")
    print(f"\n[DONE] Output → {os.path.abspath(session_root)}")
    cleanup_empty_folders(".")

if __name__ == "__main__":
    main()